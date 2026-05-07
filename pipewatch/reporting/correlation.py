"""Metric correlation: measure how similarly two metrics move over time."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from pipewatch.metrics.models import Metric


@dataclass
class CorrelationResult:
    """Pearson correlation coefficient between two named metric series."""

    metric_a: str
    metric_b: str
    coefficient: Optional[float]  # None when correlation cannot be computed
    sample_size: int

    def to_dict(self) -> Dict:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "coefficient": (
                round(self.coefficient, 6) if self.coefficient is not None else None
            ),
            "sample_size": self.sample_size,
        }

    def __repr__(self) -> str:  # pragma: no cover
        coeff = (
            f"{self.coefficient:.4f}" if self.coefficient is not None else "N/A"
        )
        return (
            f"CorrelationResult({self.metric_a!r} <-> {self.metric_b!r}, "
            f"r={coeff}, n={self.sample_size})"
        )


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Return Pearson r for two equal-length lists, or None if undefined."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0.0 or den_y == 0.0:
        return None
    return num / (den_x * den_y)


def correlate_metrics(
    metrics_a: Sequence[Metric],
    metrics_b: Sequence[Metric],
    name_a: Optional[str] = None,
    name_b: Optional[str] = None,
) -> CorrelationResult:
    """Compute Pearson correlation between the values of two metric sequences.

    Only numeric (non-None) values present in *both* sequences (by position)
    are included.  The shorter sequence determines the pairing length.
    """
    label_a = name_a or (metrics_a[0].name if metrics_a else "series_a")
    label_b = name_b or (metrics_b[0].name if metrics_b else "series_b")

    pairs = [
        (a.value, b.value)
        for a, b in zip(metrics_a, metrics_b)
        if a.value is not None and b.value is not None
    ]

    if not pairs:
        return CorrelationResult(label_a, label_b, None, 0)

    xs, ys = zip(*pairs)
    coeff = _pearson(list(xs), list(ys))
    return CorrelationResult(label_a, label_b, coeff, len(pairs))
