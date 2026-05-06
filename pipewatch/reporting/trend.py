"""Trend analysis for pipeline metrics over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque

from pipewatch.metrics.models import Metric, MetricStatus


_DEFAULT_WINDOW = 10  # number of samples to keep per metric name


@dataclass
class TrendPoint:
    """A single historical sample for a metric."""
    value: float
    status: MetricStatus
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }


@dataclass
class MetricTrend:
    """Rolling trend window for a named metric."""
    name: str
    window: int = _DEFAULT_WINDOW
    points: deque = field(default_factory=deque)

    def __post_init__(self) -> None:
        if not isinstance(self.points, deque):
            self.points = deque(self.points, maxlen=self.window)
        else:
            self.points = deque(self.points, maxlen=self.window)

    def add(self, metric: Metric) -> None:
        """Push a new sample from *metric* into the window."""
        self.points.append(
            TrendPoint(
                value=metric.value,
                status=metric.status,
                timestamp=metric.timestamp,
            )
        )

    @property
    def latest(self) -> Optional[TrendPoint]:
        return self.points[-1] if self.points else None

    @property
    def average(self) -> Optional[float]:
        if not self.points:
            return None
        return sum(p.value for p in self.points) / len(self.points)

    @property
    def direction(self) -> str:
        """Return 'up', 'down', or 'stable' based on last two samples."""
        if len(self.points) < 2:
            return "stable"
        delta = self.points[-1].value - self.points[-2].value
        if delta > 0:
            return "up"
        if delta < 0:
            return "down"
        return "stable"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "average": self.average,
            "direction": self.direction,
            "points": [p.to_dict() for p in self.points],
        }


class TrendTracker:
    """Accumulates metric samples and exposes per-metric trend windows."""

    def __init__(self, window: int = _DEFAULT_WINDOW) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._window = window
        self._trends: dict[str, MetricTrend] = {}

    def record(self, metric: Metric) -> None:
        """Record a new sample for *metric*."""
        if metric.name not in self._trends:
            self._trends[metric.name] = MetricTrend(
                name=metric.name, window=self._window
            )
        self._trends[metric.name].add(metric)

    def get(self, name: str) -> Optional[MetricTrend]:
        return self._trends.get(name)

    def all_trends(self) -> List[MetricTrend]:
        return list(self._trends.values())

    def summary(self) -> List[dict]:
        return [t.to_dict() for t in self.all_trends()]
