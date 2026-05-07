"""Metric ranking: sort and score metrics by health severity and value deviation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics.models import Metric, MetricStatus

# Weight table: higher score = worse health
_STATUS_WEIGHT: dict[MetricStatus, int] = {
    MetricStatus.CRITICAL: 100,
    MetricStatus.WARNING: 50,
    MetricStatus.OK: 0,
    MetricStatus.UNKNOWN: 10,
}


@dataclass
class RankedMetric:
    metric: Metric
    score: float
    rank: int = field(default=0, init=False)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "name": self.metric.name,
            "source": self.metric.source,
            "status": self.metric.status.value,
            "value": self.metric.value,
            "score": round(self.score, 4),
        }

    def __repr__(self) -> str:
        return (
            f"RankedMetric(rank={self.rank}, name={self.metric.name!r}, "
            f"score={self.score:.4f}, status={self.metric.status.value})"
        )


def _compute_score(metric: Metric, baseline: Optional[float] = None) -> float:
    """Combine status weight with optional relative deviation from a baseline."""
    status_score = float(_STATUS_WEIGHT.get(metric.status, 10))
    deviation = 0.0
    if baseline is not None and baseline != 0 and metric.value is not None:
        deviation = abs((metric.value - baseline) / baseline) * 10.0
    return status_score + deviation


def rank_metrics(
    metrics: List[Metric],
    baselines: Optional[dict[str, float]] = None,
) -> List[RankedMetric]:
    """Return metrics sorted from worst to best with 1-based rank assigned."""
    baselines = baselines or {}
    ranked = [
        RankedMetric(
            metric=m,
            score=_compute_score(m, baselines.get(m.name)),
        )
        for m in metrics
    ]
    ranked.sort(key=lambda r: r.score, reverse=True)
    for idx, entry in enumerate(ranked, start=1):
        entry.rank = idx
    return ranked
