"""notifier モジュールのテスト。"""

import time
from unittest.mock import patch, MagicMock

import pytest

from seedcare.config import Config
from seedcare.notifier import send_email, AlertTracker


@pytest.fixture
def config():
    return Config(
        email_account="test@gmail.com",
        email_password="password",
        alert_email_to="user@example.com",
        email_interval=3600.0,
        low_threshold_temperature=10.0,
        high_threshold_temperature=35.0,
        low_threshold_moisture=30.0,
    )


class TestSendEmail:
    @patch("seedcare.notifier.smtplib.SMTP_SSL")
    def test_success(self, mock_smtp, config):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = send_email(config, "to@test.com", "Subject", "Body")
        assert result is True
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch("seedcare.notifier.smtplib.SMTP_SSL", side_effect=OSError("fail"))
    def test_failure_returns_false(self, mock_smtp, config):
        result = send_email(config, "to@test.com", "Subject", "Body")
        assert result is False


class TestAlertTracker:
    def test_low_temp_triggers_email(self, config):
        tracker = AlertTracker(config)
        record = {
            "Temperature": {0: 5.0, 1: 25.0},
            "Moisture": {0: 60, 1: 55},
        }
        with patch("seedcare.notifier.send_email", return_value=True) as mock:
            tracker.check_thresholds(record)
        assert mock.call_count == 1
        assert "Low Temperature" in mock.call_args[0][2]

    def test_rate_limiting(self, config):
        config.email_interval = 3600.0
        tracker = AlertTracker(config)
        record = {"Temperature": {0: 5.0}, "Moisture": {}}
        with patch("seedcare.notifier.send_email", return_value=True) as mock:
            tracker.check_thresholds(record)
            tracker.check_thresholds(record)  # 2回目は間隔内
        assert mock.call_count == 1

    def test_none_record_no_crash(self, config):
        tracker = AlertTracker(config)
        tracker.check_thresholds(None)  # 例外が出なければ OK

    def test_high_temp_triggers_email(self, config):
        tracker = AlertTracker(config)
        record = {"Temperature": {0: 40.0}, "Moisture": {}}
        with patch("seedcare.notifier.send_email", return_value=True) as mock:
            tracker.check_thresholds(record)
        assert mock.call_count == 1
        assert "High Temperature" in mock.call_args[0][2]

    def test_no_message_alert(self, config):
        config.timeout_no_message = 1.0
        tracker = AlertTracker(config)
        past = time.time() - 10  # 10秒前
        with patch("seedcare.notifier.send_email", return_value=True) as mock:
            tracker.check_no_message(past)
        assert mock.call_count == 1

    def test_no_message_within_timeout(self, config):
        config.timeout_no_message = 600.0
        tracker = AlertTracker(config)
        recent = time.time()
        with patch("seedcare.notifier.send_email", return_value=True) as mock:
            tracker.check_no_message(recent)
        assert mock.call_count == 0
