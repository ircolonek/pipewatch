"""Tests for pipewatch.reporting.aggregator."""
from __future__ import annotations

import math
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.aggregator import AggregatedStats, aggregate_metrics


def _make_metric(name: str, value: float | None, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


class TestAggregateMetrics:
    def test_empty_list_returns_empty_dict(self):
        assert aggregate_metrics([]) == {}

    def test_single_metric_no_stddev(self):
        m = _make_metric("latency", 42.0)
        result = aggregate_metrics([m])
        assert "latency" in result
        stats = result["latency"]
        assert stats.count == 1
        assert stats.minimum == 42.0
        assert stats.maximum == 42.0
        assert stats.mean == 42.0
        assert stats.median == 42.0
        assert stats.stddev is None

    def test_multiple_values_stddev_present(self):
        metrics = [
            _make_metric("latency", 10.0),
            _make_metric("latency", 20.0),
            _make_metric("latency", 30.0),
        ]
        stats = aggregate_metrics(metrics)["latency"]
        assert stats.count == 3
        assert stats.minimum == 10.0
        assert stats.maximum == 30.0
        assert math.isclose(stats.mean, 20.0)
        assert math.isclose(stats.median, 20.0)
        assert stats.stddev is not None
        assert stats.stddev > 0

    def test_groups_by_name(self):
        metrics = [
            _make_metric("cpu", 80.0),
            _make_metric("mem", 50.0),
            _make_metric("cpu", 90.0),
        ]
        result = aggregate_metrics(metrics)
        assert set(result.keys()) == {"cpu", "mem"}
        assert result["cpu"].count == 2
        assert result["mem"].count == 1

    def test_status_counts_populated(self):
        metrics = [
            _make_metric("cpu", 10.0, MetricStatus.OK),
            _make_metric("cpu", 95.0, MetricStatus.CRITICAL),
            _make_metric("cpu", 80.0, MetricStatus.WARNING),
            _make_metric("cpu", 5.0, MetricStatus.OK),
        ]
        stats = aggregate_metrics(metrics)["cpu"]
        assert stats.status_counts[MetricStatus.OK.value] == 2
        assert stats.status_counts[MetricStatus.CRITICAL.value] == 1
        assert stats.status_counts[MetricStatus.WARNING.value] == 1

    def test_none_value_skipped_in_numeric_stats(self):
        metrics = [
            _make_metric("errors", None, MetricStatus.CRITICAL),
            _make_metric("errors", None, MetricStatus.CRITICAL),
        ]
        stats = aggregate_metrics(metrics)["errors"]
        assert stats.count == 2
        assert math.isnan(stats.minimum)
        assert math.isnan(stats.mean)
        assert stats.stddev is None

    def test_to_dict_keys(self):
        m = _make_metric("q", 1.0)
        stats = aggregate_metrics([m])["q"]
        d = stats.to_dict()
        for key in ("name", "count", "minimum", "maximum", "mean", "median", "stddev", "status_counts"):
            assert key in d

    def test_to_dict_stddev_none_when_single(self):
        stats = aggregate_metrics([_make_metric("x", 5.0)])["x"]
        assert stats.to_dict()["stddev"] is None

    def test_mean_rounded_in_to_dict(self):
        metrics = [_make_metric("v", v) for v in [1.0, 2.0, 3.0]]
        stats = aggregate_metrics(metrics)["v"]
        d = stats.to_dict()
        assert isinstance(d["mean"], float)
