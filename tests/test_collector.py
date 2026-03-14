"""collector モジュールのテスト。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from seedcare import db
from seedcare.collector import MQTTCollector
from seedcare.config import Config


@pytest.fixture
def config(tmp_path):
    return Config(
        mqtt_broker="127.0.0.1",
        mqtt_port=1883,
        mqtt_topic="plant/#",
        db_path=tmp_path / "test.db",
        email_account="test@gmail.com",
        email_password="pass",
        alert_email_to="user@example.com",
    )


@pytest.fixture
def collector(config):
    db.setup(config.db_path)
    return MQTTCollector(config)


def _make_mqtt_msg(topic: str, payload: str):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = payload.encode("utf-8")
    msg.qos = 0
    return msg


class TestGatheringAverage:
    def test_average_of_samples(self, collector):
        collector.pack = {
            "2025-03-01 12:00:10": {
                "Temperature": {0: 20.0, 1: 22.0},
                "Moisture": {0: 50, 1: 40},
                "Relay": {0: "OFF", 1: "OFF"},
            },
            "2025-03-01 12:00:20": {
                "Temperature": {0: 24.0, 1: 26.0},
                "Moisture": {0: 60, 1: 50},
                "Relay": {0: "OFF", 1: "ON"},
            },
        }
        result = collector._gathering_average()
        assert result is not None
        assert result["DateTime"] == "2025-03-01 12:00:00"
        assert result["Temperature"][0] == pytest.approx(22.0)
        assert result["Temperature"][1] == pytest.approx(24.0)
        assert result["Moisture"][0] == pytest.approx(55.0)

    def test_undefined_returns_none(self, collector):
        collector.pack = {"Undefined": {}}
        assert collector._gathering_average() is None


class TestOnMessage:
    def test_temperature_message(self, collector):
        msg = _make_mqtt_msg("plant/Temperature/0", "25.5")
        collector._on_message(None, None, msg)
        assert collector.pack[collector.current_dt]["Temperature"][0] == 25.5

    def test_moisture_message(self, collector):
        msg = _make_mqtt_msg("plant/Moisture/1", "65")
        collector._on_message(None, None, msg)
        assert collector.pack[collector.current_dt]["Moisture"][1] == 65

    def test_datetime_triggers_aggregation(self, collector):
        # 最初に温度データを送信
        collector.current_dt = "2025-03-01 12:00:10"
        collector.last_minute = "00"
        collector.pack = {
            "2025-03-01 12:00:10": {
                "Temperature": {0: 25.0, 1: 24.0},
                "Moisture": {0: 60, 1: 55},
                "Relay": {0: "OFF", 1: "OFF"},
            },
        }
        # 分が変わる DateTime を送信
        msg = _make_mqtt_msg("plant/DateTime", "2025/03/01 12:01:10")
        with patch("seedcare.collector.db.append") as mock_append:
            with patch.object(collector.alert, "check_thresholds"):
                collector._on_message(None, None, msg)
        mock_append.assert_called_once()
        assert collector.pack == {}  # pack がリセットされている

    def test_unknown_topic_ignored(self, collector):
        msg = _make_mqtt_msg("a/b/c/d", "data")
        collector._on_message(None, None, msg)  # 例外なし


class TestDailyPurge:
    def test_purge_runs_once_per_day(self, collector):
        with patch("seedcare.collector.purge") as mock_purge:
            collector._maybe_daily_purge()
            collector._maybe_daily_purge()  # 同日2回目
        assert mock_purge.call_count == 1
