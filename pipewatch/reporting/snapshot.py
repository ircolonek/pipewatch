"""Point-in-time snapshot of all pipeline metrics."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric, MetricStatus


@dataclass
class MetricSnapshot:
    """Immutable record of a single metric's state at capture time."""

    name: str
    value: Optional[float]
    status: MetricStatus
    source: str
    captured_at: datetime.datetime

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status.value,
            "source": self.source,
            "captured_at": self.captured_at.isoformat(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MetricSnapshot(name={self.name!r}, status={self.status.value!r}, "
            f"captured_at={self.captured_at.isoformat()!r})"
        )


@dataclass
class PipelineSnapshot:
    """Collection of metric snapshots taken at the same instant."""

    taken_at: datetime.datetime = field(
        default_factory=datetime.datetime.utcnow
    )
    metrics: List[MetricSnapshot] = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "taken_at": self.taken_at.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def by_status(self, status: MetricStatus) -> List[MetricSnapshot]:
        """Return all snapshots whose status matches *status*."""
        return [m for m in self.metrics if m.status == status]

    def by_source(self, source: str) -> List[MetricSnapshot]:
        """Return all snapshots from a given source."""
        return [m for m in self.metrics if m.source == source]

    def sources(self) -> List[str]:
        """Unique source names present in this snapshot."""
        seen: Dict[str, None] = {}
        for m in self.metrics:
            seen[m.source] = None
        return list(seen)


def capture_snapshot(
    metrics: List[Metric],
    taken_at: Optional[datetime.datetime] = None,
) -> PipelineSnapshot:
    """Build a :class:`PipelineSnapshot` from a list of live metrics."""
    ts = taken_at or datetime.datetime.utcnow()
    snaps = [
        MetricSnapshot(
            name=m.name,
            value=m.value,
            status=m.status,
            source=m.source,
            captured_at=ts,
        )
        for m in metrics
    ]
    return PipelineSnapshot(taken_at=ts, metrics=snaps)
