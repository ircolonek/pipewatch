"""Periodic digest report: bundles summary, alerts, and anomalies into one payload."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics.models import Metric
from pipewatch.reporting.summary import build_summary, SummaryReport
from pipewatch.reporting.anomaly import detect_anomalies, AnomalyResult
from pipewatch.alerts.rules import AlertRule


@dataclass
class DigestReport:
    """Top-level digest bundling summary, anomalies, and triggered alert names."""

    generated_at: str
    summary: SummaryReport
    anomalies: List[AnomalyResult] = field(default_factory=list)
    triggered_alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "summary": self.summary.to_dict(),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "triggered_alerts": self.triggered_alerts,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DigestReport(generated_at={self.generated_at!r}, "
            f"total={self.summary.total}, "
            f"anomalies={len(self.anomalies)}, "
            f"alerts={len(self.triggered_alerts)})"
        )


def build_digest(
    metrics: List[Metric],
    rules: Optional[List[AlertRule]] = None,
    z_threshold: float = 2.0,
    timestamp: Optional[str] = None,
) -> DigestReport:
    """Build a DigestReport from a list of metrics.

    Args:
        metrics: Collected metrics to analyse.
        rules: Optional alert rules to evaluate for triggered alerts.
        z_threshold: Z-score threshold for anomaly detection.
        timestamp: ISO timestamp string; defaults to UTC now.

    Returns:
        A populated DigestReport.
    """
    ts = timestamp or datetime.datetime.utcnow().isoformat()
    summary = build_summary(metrics)
    anomalies = detect_anomalies(metrics, z_threshold=z_threshold)

    triggered: List[str] = []
    if rules:
        for rule in rules:
            if any(rule.matches(m) for m in metrics):
                triggered.append(rule.name)

    return DigestReport(
        generated_at=ts,
        summary=summary,
        anomalies=anomalies,
        triggered_alerts=triggered,
    )
