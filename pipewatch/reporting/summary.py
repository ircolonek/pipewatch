"""Pipeline health summary report generator."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from pipewatch.metrics.models import Metric, MetricStatus


@dataclass
class SummaryReport:
    """Aggregated health summary for a pipeline run."""

    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total: int = 0
    ok: int = 0
    warning: int = 0
    critical: int = 0
    unknown: int = 0
    sources: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total": self.total,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
            "unknown": self.unknown,
            "sources": self.sources,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SummaryReport(total={self.total}, ok={self.ok}, "
            f"warning={self.warning}, critical={self.critical})"
        )


def build_summary(metrics: List[Metric]) -> SummaryReport:
    """Build a :class:`SummaryReport` from a list of metrics."""
    report = SummaryReport(total=len(metrics))

    _counter_map = {
        MetricStatus.OK: "ok",
        MetricStatus.WARNING: "warning",
        MetricStatus.CRITICAL: "critical",
        MetricStatus.UNKNOWN: "unknown",
    }

    for metric in metrics:
        attr = _counter_map.get(metric.status, "unknown")
        setattr(report, attr, getattr(report, attr) + 1)

        source = metric.source or "__unknown__"
        bucket = report.sources.setdefault(
            source, {"ok": 0, "warning": 0, "critical": 0, "unknown": 0}
        )
        bucket[attr] += 1

    return report
