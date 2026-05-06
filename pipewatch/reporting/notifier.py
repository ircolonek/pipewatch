"""Notification throttle: suppress repeated alerts for the same metric."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from pipewatch.alerts.rules import AlertRule
from pipewatch.metrics.models import Metric


@dataclass
class _ThrottleEntry:
    last_sent: float
    count: int = 1


class AlertNotifier:
    """Wraps an AlertDispatcher and suppresses duplicate alerts within a cooldown window."""

    def __init__(self, cooldown_seconds: float = 300.0) -> None:
        if cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be positive")
        self.cooldown_seconds = cooldown_seconds
        self._history: Dict[str, _ThrottleEntry] = {}

    def _throttle_key(self, rule: AlertRule, metric: Metric) -> str:
        return f"{rule.metric_name}::{rule.severity.value}::{metric.source}"

    def should_send(self, rule: AlertRule, metric: Metric) -> bool:
        """Return True if this alert should be dispatched (not throttled)."""
        key = self._throttle_key(rule, metric)
        now = time.monotonic()
        entry = self._history.get(key)
        if entry is None or (now - entry.last_sent) >= self.cooldown_seconds:
            self._history[key] = _ThrottleEntry(last_sent=now)
            return True
        entry.count += 1
        return False

    def suppressed_count(self, rule: AlertRule, metric: Metric) -> int:
        """Return how many times this alert has been suppressed since last send."""
        key = self._throttle_key(rule, metric)
        entry = self._history.get(key)
        return entry.count - 1 if entry else 0

    def reset(self, rule: Optional[AlertRule] = None, metric: Optional[Metric] = None) -> None:
        """Clear throttle history, optionally scoped to a specific rule+metric pair."""
        if rule is not None and metric is not None:
            key = self._throttle_key(rule, metric)
            self._history.pop(key, None)
        else:
            self._history.clear()
