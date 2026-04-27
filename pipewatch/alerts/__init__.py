"""Alert rules, dispatching, and notification channels for pipewatch."""

from pipewatch.alerts.rules import AlertRule, AlertSeverity
from pipewatch.alerts.dispatcher import AlertDispatcher
from pipewatch.alerts.channels import (
    BaseChannel,
    LogChannel,
    EmailChannel,
    get_channel,
    register_channel,
)

__all__ = [
    "AlertRule",
    "AlertSeverity",
    "AlertDispatcher",
    "BaseChannel",
    "LogChannel",
    "EmailChannel",
    "get_channel",
    "register_channel",
]
