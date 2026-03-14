"""環境変数から設定を読み込む。"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # MQTT
    mqtt_broker: str = "127.0.0.1"
    mqtt_port: int = 1883
    mqtt_topic: str = "plant/#"

    # Database
    db_path: Path = field(default_factory=lambda: Path("data/seedcare.db"))

    # Email
    email_account: str = ""
    email_password: str = ""
    alert_email_to: str = ""

    # Thresholds
    low_threshold_temperature: float = 10.0
    high_threshold_temperature: float = 35.0
    low_threshold_moisture: float = 30.0
    high_threshold_moisture: float = 101.0  # 実質無効

    # Timing
    timeout_no_message: float = 300.0
    email_interval: float = 3600.0

    # Retention
    retention_days: int = 120


def load_config() -> Config:
    """環境変数から Config を生成する。メール設定が未設定なら ValueError。"""
    cfg = Config(
        mqtt_broker=os.environ.get("MQTT_BROKER", "127.0.0.1"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        mqtt_topic=os.environ.get("MQTT_TOPIC", "plant/#"),
        db_path=Path(os.environ.get("DB_PATH", "data/seedcare.db")),
        email_account=os.environ.get("PYTHON_SEND_EMAIL_ACCOUNT", ""),
        email_password=os.environ.get("PYTHON_SEND_EMAIL_PASSWORD", ""),
        alert_email_to=os.environ.get("ALERT_EMAIL_TO", ""),
        low_threshold_temperature=float(
            os.environ.get("LOW_THRESHOLD_TEMPERATURE", "10.0")
        ),
        high_threshold_temperature=float(
            os.environ.get("HIGH_THRESHOLD_TEMPERATURE", "35.0")
        ),
        low_threshold_moisture=float(
            os.environ.get("LOW_THRESHOLD_MOISTURE", "30.0")
        ),
        timeout_no_message=float(os.environ.get("TIMEOUT_NO_MESSAGE", "300")),
        retention_days=int(os.environ.get("RETENTION_DAYS", "120")),
    )
    if not cfg.email_account or not cfg.email_password:
        raise ValueError(
            "PYTHON_SEND_EMAIL_ACCOUNT と PYTHON_SEND_EMAIL_PASSWORD を設定してください"
        )
    return cfg
