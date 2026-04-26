from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from pipewatch.metrics.models import Metric
from .rules import AlertRule


class AlertDispatcher:
    """Evaluates metrics against registered AlertRules and dispatches alerts."""

    def __init__(self, on_alert: Optional[Callable[[dict], None]] = None) -> None:
        self._rules: list[AlertRule] = []
        self._on_alert = on_alert
        self.history: list[dict] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule with the dispatcher."""
        self._rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name. Returns True if found and removed."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != rule_name]
        return len(self._rules) < before

    def evaluate(self, metric: Metric) -> list[dict]:
        """Check metric against all rules; fire callbacks for matches."""
        fired: list[dict] = []
        for rule in self._rules:
            if rule.matches(metric):
                alert = self._build_alert(rule, metric)
                self.history.append(alert)
                fired.append(alert)
                if self._on_alert is not None:
                    self._on_alert(alert)
        return fired

    def evaluate_many(self, metrics: list[Metric]) -> list[dict]:
        """Evaluate a batch of metrics and return all fired alerts."""
        results: list[dict] = []
        for metric in metrics:
            results.extend(self.evaluate(metric))
        return results

    @staticmethod
    def _build_alert(rule: AlertRule, metric: Metric) -> dict:
        return {
            "rule": rule.name,
            "metric": metric.name,
            "severity": rule.severity.value,
            "message": rule.format_message(metric),
            "value": metric.value,
            "status": metric.status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear_history(self) -> None:
        """Wipe the in-memory alert history."""
        self.history.clear()

    def __repr__(self) -> str:
        return f"AlertDispatcher(rules={len(self._rules)}, history={len(self.history)})"
