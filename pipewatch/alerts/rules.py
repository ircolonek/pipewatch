from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
from pipewatch.metrics.models import Metric, MetricStatus


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Defines a rule that triggers an alert based on metric state."""

    name: str
    metric_name: str
    severity: AlertSeverity = AlertSeverity.WARNING
    trigger_on: list[MetricStatus] = field(
        default_factory=lambda: [MetricStatus.CRITICAL]
    )
    message_template: str = "Metric '{metric_name}' is {status} (value={value})"
    condition: Optional[Callable[[Metric], bool]] = None

    def matches(self, metric: Metric) -> bool:
        """Return True if this rule should fire for the given metric."""
        if metric.name != self.metric_name:
            return False
        if self.condition is not None:
            return self.condition(metric)
        return metric.status in self.trigger_on

    def format_message(self, metric: Metric) -> str:
        """Render the alert message for a matched metric."""
        return self.message_template.format(
            metric_name=metric.name,
            status=metric.status.value,
            value=metric.value,
            unit=metric.unit or "",
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "metric_name": self.metric_name,
            "severity": self.severity.value,
            "trigger_on": [s.value for s in self.trigger_on],
            "message_template": self.message_template,
        }

    def __repr__(self) -> str:
        return (
            f"AlertRule(name={self.name!r}, metric={self.metric_name!r}, "
            f"severity={self.severity.value!r})"
        )
