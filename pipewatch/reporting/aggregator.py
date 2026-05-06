"""Metric aggregation utilities: compute stats over a collection of Metric objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median, stdev
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric, MetricStatus


@dataclass
class AggregatedStats:
    """Descriptive statistics for a group of metric values."""

    name: str
    count: int
    minimum: float
    maximum: float
    mean: float
    median: float
    stddev: Optional[float]  # None when count < 2
    status_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": round(self.mean, 6),
            "median": round(self.median, 6),
            "stddev": round(self.stddev, 6) if self.stddev is not None else None,
            "status_counts": self.status_counts,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AggregatedStats(name={self.name!r}, count={self.count}, "
            f"mean={self.mean:.4f}, stddev={self.stddev})"
        )


def aggregate_metrics(metrics: List[Metric]) -> Dict[str, AggregatedStats]:
    """Group *metrics* by name and compute per-group statistics.

    Returns a mapping of metric name -> :class:`AggregatedStats`.
    Metrics with a ``None`` value are silently skipped for numeric stats
    but still counted in *status_counts*.
    """
    groups: Dict[str, List[Metric]] = {}
    for m in metrics:
        groups.setdefault(m.name, []).append(m)

    result: Dict[str, AggregatedStats] = {}
    for name, group in groups.items():
        values = [m.value for m in group if m.value is not None]
        status_counts: Dict[str, int] = {}
        for m in group:
            key = m.status.value if isinstance(m.status, MetricStatus) else str(m.status)
            status_counts[key] = status_counts.get(key, 0) + 1

        if not values:
            result[name] = AggregatedStats(
                name=name,
                count=len(group),
                minimum=float("nan"),
                maximum=float("nan"),
                mean=float("nan"),
                median=float("nan"),
                stddev=None,
                status_counts=status_counts,
            )
            continue

        result[name] = AggregatedStats(
            name=name,
            count=len(group),
            minimum=min(values),
            maximum=max(values),
            mean=mean(values),
            median=median(values),
            stddev=stdev(values) if len(values) >= 2 else None,
            status_counts=status_counts,
        )

    return result
