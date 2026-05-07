"""Simple linear-regression forecast for metric values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from pipewatch.metrics.models import Metric


@dataclass
class ForecastPoint:
    """A single forecasted value at a future step."""

    step: int          # steps ahead from the last observed value
    value: float
    lower: float       # simple confidence band (±1 std-err)
    upper: float

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "value": round(self.value, 4),
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ForecastPoint(step={self.step}, value={self.value:.4f}, "
            f"lower={self.lower:.4f}, upper={self.upper:.4f})"
        )


@dataclass
class MetricForecast:
    """Forecast result for a single metric."""

    metric_name: str
    horizon: int
    points: List[ForecastPoint] = field(default_factory=list)
    slope: Optional[float] = None
    intercept: Optional[float] = None
    insufficient_data: bool = False

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "horizon": self.horizon,
            "slope": round(self.slope, 6) if self.slope is not None else None,
            "intercept": round(self.intercept, 6) if self.intercept is not None else None,
            "insufficient_data": self.insufficient_data,
            "points": [p.to_dict() for p in self.points],
        }


def _linear_regression(xs: List[float], ys: List[float]):
    """Return (slope, intercept, std_err) for the given paired samples."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = ss_xy / ss_xx if ss_xx != 0 else 0.0
    intercept = mean_y - slope * mean_x
    residuals = [(y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys)]
    std_err = (sum(residuals) / n) ** 0.5
    return slope, intercept, std_err


def forecast_metric(
    metrics: Sequence[Metric],
    name: str,
    horizon: int = 3,
    min_points: int = 3,
) -> MetricForecast:
    """Forecast *horizon* future steps for *name* using linear regression.

    Metrics are assumed to be ordered oldest-first.
    """
    values = [m.value for m in metrics if m.name == name and m.value is not None]

    result = MetricForecast(metric_name=name, horizon=horizon)

    if len(values) < min_points:
        result.insufficient_data = True
        return result

    xs = list(range(len(values)))
    slope, intercept, std_err = _linear_regression(xs, values)
    result.slope = slope
    result.intercept = intercept
    last_x = len(values) - 1

    for step in range(1, horizon + 1):
        x_future = last_x + step
        predicted = slope * x_future + intercept
        result.points.append(
            ForecastPoint(
                step=step,
                value=predicted,
                lower=predicted - std_err,
                upper=predicted + std_err,
            )
        )

    return result
