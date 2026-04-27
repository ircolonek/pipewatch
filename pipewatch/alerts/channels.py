"""Alert notification channels for dispatching alerts to external systems."""

import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CHANNEL_REGISTRY: Dict[str, type] = {}


def register_channel(name: str):
    """Class decorator to register a notification channel by name."""
    def decorator(cls):
        _CHANNEL_REGISTRY[name] = cls
        return cls
    return decorator


def get_channel(name: str) -> Optional[type]:
    """Retrieve a registered channel class by name."""
    return _CHANNEL_REGISTRY.get(name)


class BaseChannel(ABC):
    """Abstract base class for all alert notification channels."""

    @abstractmethod
    def send(self, subject: str, message: str, severity: str) -> bool:
        """Send an alert notification. Returns True on success."""
        raise NotImplementedError


@register_channel("log")
@dataclass
class LogChannel(BaseChannel):
    """Sends alerts to the Python logging system."""

    level: str = "WARNING"

    def send(self, subject: str, message: str, severity: str) -> bool:
        log_level = getattr(logging, self.level.upper(), logging.WARNING)
        logger.log(log_level, "[%s] %s — %s", severity.upper(), subject, message)
        return True


@register_channel("email")
@dataclass
class EmailChannel(BaseChannel):
    """Sends alerts via SMTP email."""

    smtp_host: str = "localhost"
    smtp_port: int = 25
    from_addr: str = "pipewatch@localhost"
    to_addrs: List[str] = field(default_factory=list)
    username: Optional[str] = None
    password: Optional[str] = None

    def send(self, subject: str, message: str, severity: str) -> bool:
        if not self.to_addrs:
            logger.warning("EmailChannel: no recipients configured, skipping.")
            return False
        msg = MIMEText(message)
        msg["Subject"] = f"[pipewatch/{severity.upper()}] {subject}"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            return True
        except smtplib.SMTPException as exc:
            logger.error("EmailChannel: failed to send email: %s", exc)
            return False
