"""Tests for pipewatch.alerts.channels."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.alerts.channels import (
    BaseChannel,
    EmailChannel,
    LogChannel,
    get_channel,
    register_channel,
)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestChannelRegistry:
    def test_log_channel_registered(self):
        assert get_channel("log") is LogChannel

    def test_email_channel_registered(self):
        assert get_channel("email") is EmailChannel

    def test_unknown_channel_returns_none(self):
        assert get_channel("nonexistent") is None

    def test_custom_channel_registration(self):
        @register_channel("dummy_test_chan")
        class _Dummy(BaseChannel):
            def send(self, subject, message, severity):
                return True

        assert get_channel("dummy_test_chan") is _Dummy


# ---------------------------------------------------------------------------
# LogChannel tests
# ---------------------------------------------------------------------------

class TestLogChannel:
    def test_send_returns_true(self):
        ch = LogChannel(level="WARNING")
        assert ch.send("Test subject", "Test body", "warning") is True

    def test_send_uses_correct_log_level(self, caplog):
        ch = LogChannel(level="ERROR")
        with caplog.at_level(logging.ERROR):
            ch.send("Pipeline lag", "Lag exceeded threshold", "critical")
        assert "Pipeline lag" in caplog.text

    def test_send_includes_severity_in_message(self, caplog):
        ch = LogChannel(level="WARNING")
        with caplog.at_level(logging.WARNING):
            ch.send("subject", "body", "warning")
        assert "WARNING" in caplog.text


# ---------------------------------------------------------------------------
# EmailChannel tests
# ---------------------------------------------------------------------------

class TestEmailChannel:
    def test_send_returns_false_when_no_recipients(self):
        ch = EmailChannel(to_addrs=[])
        assert ch.send("subj", "msg", "critical") is False

    def test_send_calls_smtp(self):
        ch = EmailChannel(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="alert@example.com",
            to_addrs=["ops@example.com"],
        )
        with patch("pipewatch.alerts.channels.smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            result = ch.send("High error rate", "Errors spiked", "critical")
        assert result is True
        mock_server.sendmail.assert_called_once()

    def test_send_returns_false_on_smtp_error(self):
        import smtplib
        ch = EmailChannel(to_addrs=["ops@example.com"])
        with patch("pipewatch.alerts.channels.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp_cls.side_effect = smtplib.SMTPException("connection refused")
            result = ch.send("subj", "body", "warning")
        assert result is False

    def test_subject_contains_severity(self):
        ch = EmailChannel(to_addrs=["ops@example.com"])
        captured = {}
        with patch("pipewatch.alerts.channels.smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            mock_server.sendmail.side_effect = lambda f, t, msg: captured.update({"msg": msg})
            ch.send("disk full", "disk at 95%", "critical")
        assert "CRITICAL" in captured.get("msg", "")
