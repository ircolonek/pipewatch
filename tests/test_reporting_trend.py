"""Tests for pipewatch.reporting.trend."""
from __future__ import annotations

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.trend import (
    MetricTrend,
    TrendPoint,
    TrendTracker,
    _DEFAULT_WINDOW,
)


def _make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


# ---------------------------------------------------------------------------
# TrendPoint
# ---------------------------------------------------------------------------
class TestTrendPoint:
    def test_to_dict_keys(self):
        tp = TrendPoint(value=3.14, status=MetricStatus.OK, timestamp="2024-01-01")
        d = tp.to_dict()
        assert set(d.keys()) == {"value", "status", "timestamp"}

    def test_to_dict_status_is_string(self):
        tp = TrendPoint(value=1.0, status=MetricStatus.CRITICAL)
        assert isinstance(tp.to_dict()["status"], str)


# ---------------------------------------------------------------------------
# MetricTrend
# ---------------------------------------------------------------------------
class TestMetricTrend:
    def test_add_single_point(self):
        trend = MetricTrend(name="latency")
        trend.add(_make_metric("latency", 42.0))
        assert len(trend.points) == 1
        assert trend.latest.value == 42.0

    def test_direction_stable_single_point(self):
        trend = MetricTrend(name="latency")
        trend.add(_make_metric("latency", 10.0))
        assert trend.direction == "stable"

    def test_direction_up(self):
        trend = MetricTrend(name="latency")
        trend.add(_make_metric("latency", 10.0))
        trend.add(_make_metric("latency", 20.0))
        assert trend.direction == "up"

    def test_direction_down(self):
        trend = MetricTrend(name="latency")
        trend.add(_make_metric("latency", 20.0))
        trend.add(_make_metric("latency", 5.0))
        assert trend.direction == "down"

    def test_average(self):
        trend = MetricTrend(name="latency")
        for v in [10.0, 20.0, 30.0]:
            trend.add(_make_metric("latency", v))
        assert trend.average == pytest.approx(20.0)

    def test_average_empty(self):
        trend = MetricTrend(name="latency")
        assert trend.average is None

    def test_window_evicts_old_points(self):
        trend = MetricTrend(name="latency", window=3)
        for v in range(10):
            trend.add(_make_metric("latency", float(v)))
        assert len(trend.points) == 3
        assert trend.latest.value == 9.0

    def test_to_dict_structure(self):
        trend = MetricTrend(name="errors")
        trend.add(_make_metric("errors", 1.0))
        d = trend.to_dict()
        assert d["name"] == "errors"
        assert "average" in d
        assert "direction" in d
        assert isinstance(d["points"], list)


# ---------------------------------------------------------------------------
# TrendTracker
# ---------------------------------------------------------------------------
class TestTrendTracker:
    def test_raises_on_zero_window(self):
        with pytest.raises(ValueError):
            TrendTracker(window=0)

    def test_record_and_retrieve(self):
        tracker = TrendTracker()
        tracker.record(_make_metric("cpu", 55.0))
        trend = tracker.get("cpu")
        assert trend is not None
        assert trend.latest.value == 55.0

    def test_get_unknown_returns_none(self):
        tracker = TrendTracker()
        assert tracker.get("nonexistent") is None

    def test_multiple_metrics_tracked_independently(self):
        tracker = TrendTracker()
        tracker.record(_make_metric("cpu", 10.0))
        tracker.record(_make_metric("memory", 80.0))
        assert len(tracker.all_trends()) == 2

    def test_summary_returns_list_of_dicts(self):
        tracker = TrendTracker()
        tracker.record(_make_metric("cpu", 10.0))
        summary = tracker.summary()
        assert isinstance(summary, list)
        assert summary[0]["name"] == "cpu"

    def test_default_window_applied(self):
        tracker = TrendTracker(window=5)
        for i in range(10):
            tracker.record(_make_metric("cpu", float(i)))
        assert len(tracker.get("cpu").points) == 5
