"""Metric comparison utilities: diff two snapshots of metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric, MetricStatus


@dataclass
class MetricDiff:
    """Difference between a metric value at two points in time."""

    name: str
    source: str
    previous_value: Optional[float]
    current_value: Optional[float]
    previous_status: Optional[MetricStatus]
    current_status: Optional[MetricStatus]

    @property
    def value_delta(self) -> Optional[float]:
        if self.previous_value is None or self.current_value is None:
            return None
        return self.current_value - self.previous_value

    @property
    def status_changed(self) -> bool:
        return self.previous_status != self.current_status

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "value_delta": self.value_delta,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "current_status": self.current_status.value if self.current_status else None,
            "status_changed": self.status_changed,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MetricDiff(name={self.name!r}, delta={self.value_delta}, "
            f"status_changed={self.status_changed})"
        )


@dataclass
class ComparisonReport:
    """Result of comparing two metric snapshots."""

    diffs: List[MetricDiff] = field(default_factory=list)
    new_metrics: List[str] = field(default_factory=list)
    removed_metrics: List[str] = field(default_factory=list)

    @property
    def changed(self) -> List[MetricDiff]:
        return [d for d in self.diffs if d.status_changed]

    def to_dict(self) -> dict:
        return {
            "diffs": [d.to_dict() for d in self.diffs],
            "new_metrics": self.new_metrics,
            "removed_metrics": self.removed_metrics,
            "changed_count": len(self.changed),
        }


def compare_snapshots(
    previous: List[Metric],
    current: List[Metric],
) -> ComparisonReport:
    """Compare two lists of metrics and return a ComparisonReport."""
    prev_map: Dict[str, Metric] = {m.name: m for m in previous}
    curr_map: Dict[str, Metric] = {m.name: m for m in current}

    diffs: List[MetricDiff] = []
    for name, curr_metric in curr_map.items():
        if name in prev_map:
            prev_metric = prev_map[name]
            diffs.append(
                MetricDiff(
                    name=name,
                    source=curr_metric.source,
                    previous_value=prev_metric.value,
                    current_value=curr_metric.value,
                    previous_status=prev_metric.status,
                    current_status=curr_metric.status,
                )
            )

    new_metrics = [n for n in curr_map if n not in prev_map]
    removed_metrics = [n for n in prev_map if n not in curr_map]

    return ComparisonReport(diffs=diffs, new_metrics=new_metrics, removed_metrics=removed_metrics)
