"""MQTT データ収集デーモン。plantDevReporter.py からの移植・リファクタリング版。"""

import logging
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from seedcare import db
from seedcare.config import Config
from seedcare.notifier import AlertTracker
from seedcare.purge import purge

logger = logging.getLogger(__name__)

LOOP_TIMEOUT = 2.0  # mqtt.loop() のタイムアウト秒数


class MQTTCollector:
    def __init__(self, config: Config):
        self.config = config
        self.alert = AlertTracker(config)
        self.pack: dict = {}
        self.current_dt = "Undefined"
        self.last_minute = "Undefined"
        self.last_msg_time: float = 0
        self._last_purge_date: str = ""
        self._client: mqtt.Client | None = None

    def start(self) -> None:
        db.setup(self.config.db_path)
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        logger.info(
            "MQTT ブローカーに接続: %s:%d", self.config.mqtt_broker, self.config.mqtt_port
        )
        self._client.connect(self.config.mqtt_broker, self.config.mqtt_port, 60)
        self._run_loop()

    def _on_connect(self, client, userdata, flags, rc):
        logger.info("MQTT 接続成功 (rc=%d)", rc)
        client.subscribe(self.config.mqtt_topic)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("MQTT 予期しない切断 (rc=%d)", rc)

    def _on_message(self, client, userdata, msg):
        self.last_msg_time = time.time()
        topic_parts = str(msg.topic).split("/")
        if len(topic_parts) == 2:
            kind, dev_no = topic_parts[1], 0
        elif len(topic_parts) == 3:
            kind, dev_no = topic_parts[1], int(topic_parts[2])
        else:
            logger.warning("不明なトピック形式: %s", msg.topic)
            return

        payload = msg.payload.decode("utf-8")
        if kind == "DateTime":
            value = payload.replace("/", "-")
        elif kind == "Moisture":
            value = int(payload)
        elif kind == "Temperature":
            value = float(payload)
        else:
            value = payload

        if self.current_dt not in self.pack:
            self.pack[self.current_dt] = {}
        if kind not in self.pack[self.current_dt]:
            self.pack[self.current_dt][kind] = {}
        self.pack[self.current_dt][kind][dev_no] = value

        if kind == "DateTime":
            self.current_dt = value
            current_minute = value[-5:-3]
            if current_minute != self.last_minute:
                self.last_minute = current_minute
                record = self._gathering_average()
                if record is not None:
                    self.alert.check_thresholds(record)
                    db.append(self.config.db_path, record)
                self.pack = {}

        logger.info("%s %s-%d = %s", self.current_dt, kind, dev_no, value)

    def _gathering_average(self) -> dict | None:
        """10秒サンプルを1分平均に集約する。"""
        if "Undefined" in self.pack:
            return None

        total: dict[str, float] = {}
        last_dt = ""
        for dt_key in self.pack:
            last_dt = dt_key
            for kind in self.pack[dt_key]:
                if kind not in ("Temperature", "Moisture"):
                    continue
                for dev_no in self.pack[dt_key][kind]:
                    k = f"{kind}-{dev_no}"
                    total[k] = total.get(k, 0) + self.pack[dt_key][kind][dev_no]

        n = len(self.pack)
        if n == 0:
            return None

        result: dict = {"DateTime": last_dt[:-3] + ":00"}
        for dev_key, total_val in total.items():
            kind_name, no_str = dev_key.split("-")
            if kind_name not in result:
                result[kind_name] = {}
            result[kind_name][int(no_str)] = total_val / n

        # Relay は最後のサンプルをそのまま使う
        if last_dt in self.pack and "Relay" in self.pack[last_dt]:
            result["Relay"] = self.pack[last_dt]["Relay"]
        else:
            result["Relay"] = {0: "OFF", 1: "OFF"}
        return result

    def _maybe_daily_purge(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._last_purge_date:
            self._last_purge_date = today
            purge(self.config.db_path, self.config.retention_days)

    def _run_loop(self) -> None:
        assert self._client is not None
        logger.info("イベントループ開始")
        while True:
            self._client.loop(timeout=LOOP_TIMEOUT)
            if self.last_msg_time > 0:
                self.alert.check_no_message(self.last_msg_time)
            self._maybe_daily_purge()
