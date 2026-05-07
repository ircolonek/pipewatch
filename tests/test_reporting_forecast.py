"""Tests for pipewatch.reporting.forecast."""
from __future__ import annotations

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.forecast import (
    ForecastPoint,
    MetricForecast,
    forecast_metric,
    _linear_regression,
)


def _make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


# ---------------------------------------------------------------------------
# ForecastPoint
# ---------------------------------------------------------------------------

class TestForecastPoint:
    def test_to_dict_keys(self):
        fp = ForecastPoint(step=1, value=3.14159, lower=2.5, upper=3.8)
        d = fp.to_dict()
        assert set(d.keys()) == {"step", "value", "lower", "upper"}

    def test_to_dict_rounded(self):
        fp = ForecastPoint(step=2, value=1.123456789, lower=0.9, upper=1.3)
        assert fp.to_dict()["value"] == round(1.123456789, 4)

    def test_step_preserved(self):
        fp = ForecastPoint(step=5, value=10.0, lower=9.0, upper=11.0)
        assert fp.to_dict()["step"] == 5


# ---------------------------------------------------------------------------
# MetricForecast
# ---------------------------------------------------------------------------

class TestMetricForecast:
    def test_to_dict_keys(self):
        mf = MetricForecast(metric_name="lag", horizon=3)
        d = mf.to_dict()
        assert "metric_name" in d
        assert "horizon" in d
        assert "points" in d
        assert "insufficient_data" in d

    def test_insufficient_data_flag(self):
        mf = MetricForecast(metric_name="lag", horizon=2, insufficient_data=True)
        assert mf.to_dict()["insufficient_data"] is True

    def test_slope_none_serialises(self):
        mf = MetricForecast(metric_name="x", horizon=1)
        assert mf.to_dict()["slope"] is None


# ---------------------------------------------------------------------------
# _linear_regression
# ---------------------------------------------------------------------------

class TestLinearRegression:
    def test_perfect_line(self):
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [1.0, 3.0, 5.0, 7.0]  # y = 2x + 1
        slope, intercept, std_err = _linear_regression(xs, ys)
        assert abs(slope - 2.0) < 1e-9
        assert abs(intercept - 1.0) < 1e-9
        assert std_err < 1e-9

    def test_flat_line(self):
        xs = [0.0, 1.0, 2.0]
        ys = [5.0, 5.0, 5.0]
        slope, intercept, _ = _linear_regression(xs, ys)
        assert abs(slope) < 1e-9
        assert abs(intercept - 5.0) < 1e-9


# ---------------------------------------------------------------------------
# forecast_metric
# ---------------------------------------------------------------------------

class TestForecastMetric:
    def _metrics(self, name: str, values):
        return [_make_metric(name, v) for v in values]

    def test_insufficient_data_below_min_points(self):
        metrics = self._metrics("lag", [1.0, 2.0])
        result = forecast_metric(metrics, "lag", horizon=3, min_points=3)
        assert result.insufficient_data is True
        assert result.points == []

    def test_correct_number_of_points(self):
        metrics = self._metrics("lag", [1.0, 2.0, 3.0, 4.0, 5.0])
        result = forecast_metric(metrics, "lag", horizon=4)
        assert len(result.points) == 4

    def test_forecast_values_increasing_for_rising_trend(self):
        metrics = self._metrics("lag", [10.0, 20.0, 30.0, 40.0])
        result = forecast_metric(metrics, "lag", horizon=3)
        vals = [p.value for p in result.points]
        assert vals[0] < vals[1] < vals[2]

    def test_lower_less_than_upper(self):
        metrics = self._metrics("lag", [5.0, 6.0, 7.0, 8.0])
        result = forecast_metric(metrics, "lag", horizon=2)
        for p in result.points:
            assert p.lower <= p.upper

    def test_ignores_other_metric_names(self):
        metrics = self._metrics("lag", [1.0, 2.0, 3.0]) + self._metrics("throughput", [100.0, 200.0])
        result = forecast_metric(metrics, "lag", horizon=1)
        assert not result.insufficient_data
        assert len(result.points) == 1

    def test_slope_and_intercept_stored(self):
        metrics = self._metrics("lag", [0.0, 1.0, 2.0, 3.0])
        result = forecast_metric(metrics, "lag", horizon=1)
        assert result.slope is not None
        assert result.intercept is not None

    def test_to_dict_roundtrip(self):
        metrics = self._metrics("lag", [1.0, 2.0, 3.0, 4.0])
        result = forecast_metric(metrics, "lag", horizon=2)
        d = result.to_dict()
        assert d["metric_name"] == "lag"
        assert len(d["points"]) == 2
