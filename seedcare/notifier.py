"""メール通知モジュール。

既存 send_mail.py からの修正点:
1. env var 未設定時に "None" 文字列になるバグ → config で事前検証
2. 例外を握りつぶすバグ → ログ出力 + bool 返却
3. 呼び出し側に成否が伝わらないバグ → send_email() が bool を返す
"""

import errno
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Dict, Optional

from seedcare.config import Config

logger = logging.getLogger(__name__)

THRESHOLD_UNITS = {"Temperature": "\u2103", "Moisture": "%"}


def send_email(config: Config, to: str, subject: str, body: str) -> bool:
    """メールを送信する。成功なら True、失敗なら False。"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.email_account
    msg["To"] = to
    msg["Date"] = formatdate()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(config.email_account, config.email_password)
            s.sendmail(config.email_account, to, msg.as_string())
        logger.info("メール送信成功: %s", subject)
        return True
    except OSError as e:
        if e.errno == errno.ENETDOWN:
            logger.warning("ネットワーク停止中のためメール送信失敗: %s", e)
        elif e.errno == errno.ECONNRESET:
            logger.warning("接続リセットのためメール送信失敗: %s", e)
        else:
            logger.warning("メール送信失敗 (OSError): %s", e)
        return False
    except Exception as e:
        logger.warning("メール送信失敗: %s", e)
        return False


class AlertTracker:
    """アラート送信間隔を管理する。"""

    def __init__(self, config: Config):
        self.config = config
        self._last_sent: Dict[str, float] = {}

    def _key(self, kind: str, dev_no: int) -> str:
        return f"{kind}-{dev_no}"

    def _can_send(self, key: str) -> bool:
        last = self._last_sent.get(key, 0)
        return (time.time() - last) > self.config.email_interval

    def _mark_sent(self, key: str) -> None:
        self._last_sent[key] = time.time()

    def check_thresholds(self, record: Optional[dict]) -> None:
        """レコードの値を閾値と比較し、超過時にメール通知する。"""
        if record is None:
            return

        cfg = self.config
        thresholds = {
            "Temperature": (cfg.low_threshold_temperature, cfg.high_threshold_temperature),
            "Moisture": (cfg.low_threshold_moisture, cfg.high_threshold_moisture),
        }
        low_messages = {
            "Temperature": "to heat",
            "Moisture": "and pour enough water",
        }
        high_messages = {
            "Temperature": "around sunlight",
            "Moisture": "",
        }

        for kind in ("Temperature", "Moisture"):
            if kind not in record:
                continue
            low, high = thresholds[kind]
            unit = THRESHOLD_UNITS[kind]
            for dev_no, value in record[kind].items():
                key = self._key(kind, dev_no)
                if value <= low and self._can_send(key):
                    subject = f"CAUTION - Low {kind} {value:.1f}{unit} dev:{dev_no}"
                    body = f"Please check the device {dev_no} {low_messages[kind]}."
                    if send_email(cfg, cfg.alert_email_to, subject, body):
                        self._mark_sent(key)
                elif value >= high and self._can_send(key):
                    subject = f"CAUTION - High {kind} {value:.1f}{unit} dev:{dev_no}"
                    body = f"Please check the device {dev_no} {high_messages[kind]}."
                    if send_email(cfg, cfg.alert_email_to, subject, body):
                        self._mark_sent(key)

    def check_no_message(self, last_msg_time: float) -> None:
        """一定時間メッセージがない場合にアラートを送信する。"""
        if last_msg_time == 0:
            return
        if (time.time() - last_msg_time) <= self.config.timeout_no_message:
            return
        key = "__no_message__"
        if self._can_send(key):
            subject = "CAUTION: データ更新が停止しています"
            body = "一定時間データが更新されていません。デバイスを確認してください。"
            if send_email(self.config, self.config.alert_email_to, subject, body):
                self._mark_sent(key)
