"""Metric collection logic with threshold evaluation."""

from typing import List, Optional

from .models import Metric, MetricStatus


class MetricCollector:
    """Collects metrics and evaluates them against configured thresholds."""

    def __init__(self, source: str, thresholds: Optional[dict] = None):
        self.source = source
        self.thresholds = thresholds or {}
        self._metrics: List[Metric] = []

    def record(self, name: str, value: float, unit: str = "", tags: Optional[dict] = None) -> Metric:
        """Record a metric value and evaluate its status."""
        status = self._evaluate_status(name, value)
        metric = Metric(
            source=self.source,
            name=name,
            value=value,
            unit=unit,
            status=status,
            tags=tags or {},
        )
        self._metrics.append(metric)
        return metric

    def _evaluate_status(self, name: str, value: float) -> MetricStatus:
        """Evaluate metric status based on configured thresholds."""
        thresholds = self.thresholds.get(name, {})
        if not thresholds:
            return MetricStatus.OK

        critical = thresholds.get("critical")
        warning = thresholds.get("warning")

        if critical is not None and value >= critical:
            return MetricStatus.CRITICAL
        if warning is not None and value >= warning:
            return MetricStatus.WARNING
        return MetricStatus.OK

    def get_all(self) -> List[Metric]:
        """Return all collected metrics."""
        return list(self._metrics)

    def get_by_status(self, status: MetricStatus) -> List[Metric]:
        """Filter metrics by status."""
        return [m for m in self._metrics if m.status == status]

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()

    def summary(self) -> dict:
        """Return a summary count of metrics by status."""
        summary = {s.value: 0 for s in MetricStatus}
        for metric in self._metrics:
            summary[metric.status.value] += 1
        summary["total"] = len(self._metrics)
        return summary
