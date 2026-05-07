"""Simple anomaly detection for pipeline metrics using z-score."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric


@dataclass
class AnomalyResult:
    metric_name: str
    value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool
    threshold: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "mean": round(self.mean, 6),
            "stddev": round(self.stddev, 6),
            "z_score": round(self.z_score, 6),
            "is_anomaly": self.is_anomaly,
            "threshold": self.threshold,
        }

    def __repr__(self) -> str:  # pragma: no cover
        flag = "ANOMALY" if self.is_anomaly else "ok"
        return (
            f"<AnomalyResult {self.metric_name} z={self.z_score:.2f} [{flag}]>"
        )


def detect_anomalies(
    metrics: List[Metric],
    history: Dict[str, List[float]],
    threshold: float = 3.0,
) -> List[AnomalyResult]:
    """Return an AnomalyResult for each metric that has enough history.

    Args:
        metrics:   Current metric snapshot.
        history:   Mapping of metric name -> list of past float values.
        threshold: Z-score magnitude above which a value is flagged.

    Returns:
        List of AnomalyResult objects (one per metric with sufficient history).
    """
    if threshold <= 0:
        raise ValueError("threshold must be a positive number")

    results: List[AnomalyResult] = []

    for metric in metrics:
        past = history.get(metric.name, [])
        if len(past) < 2:
            continue

        mean = sum(past) / len(past)
        variance = sum((x - mean) ** 2 for x in past) / len(past)
        stddev = math.sqrt(variance)

        if stddev == 0.0:
            z_score = 0.0
        else:
            z_score = abs((metric.value - mean) / stddev)

        results.append(
            AnomalyResult(
                metric_name=metric.name,
                value=metric.value,
                mean=mean,
                stddev=stddev,
                z_score=z_score,
                is_anomaly=z_score > threshold,
                threshold=threshold,
            )
        )

    return results
