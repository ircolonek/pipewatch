"""Tests for pipewatch.reporting.comparator."""
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.comparator import (
    ComparisonReport,
    MetricDiff,
    compare_snapshots,
)


def _make_metric(name: str, value: float, status: MetricStatus, source: str = "test") -> Metric:
    return Metric(name=name, value=value, source=source, status=status)


# ---------------------------------------------------------------------------
# MetricDiff
# ---------------------------------------------------------------------------

class TestMetricDiff:
    def test_value_delta_computed(self):
        diff = MetricDiff(
            name="latency", source="db",
            previous_value=100.0, current_value=150.0,
            previous_status=MetricStatus.OK, current_status=MetricStatus.WARNING,
        )
        assert diff.value_delta == pytest.approx(50.0)

    def test_value_delta_none_when_previous_missing(self):
        diff = MetricDiff(
            name="latency", source="db",
            previous_value=None, current_value=150.0,
            previous_status=None, current_status=MetricStatus.OK,
        )
        assert diff.value_delta is None

    def test_status_changed_true(self):
        diff = MetricDiff(
            name="x", source="s",
            previous_value=1.0, current_value=2.0,
            previous_status=MetricStatus.OK, current_status=MetricStatus.CRITICAL,
        )
        assert diff.status_changed is True

    def test_status_changed_false(self):
        diff = MetricDiff(
            name="x", source="s",
            previous_value=1.0, current_value=1.5,
            previous_status=MetricStatus.OK, current_status=MetricStatus.OK,
        )
        assert diff.status_changed is False

    def test_to_dict_keys(self):
        diff = MetricDiff(
            name="x", source="s",
            previous_value=1.0, current_value=2.0,
            previous_status=MetricStatus.OK, current_status=MetricStatus.WARNING,
        )
        d = diff.to_dict()
        assert set(d.keys()) == {
            "name", "source", "previous_value", "current_value",
            "value_delta", "previous_status", "current_status", "status_changed",
        }

    def test_to_dict_status_serialised_as_string(self):
        diff = MetricDiff(
            name="x", source="s",
            previous_value=1.0, current_value=2.0,
            previous_status=MetricStatus.OK, current_status=MetricStatus.WARNING,
        )
        d = diff.to_dict()
        assert isinstance(d["previous_status"], str)
        assert isinstance(d["current_status"], str)


# ---------------------------------------------------------------------------
# compare_snapshots
# ---------------------------------------------------------------------------

class TestCompareSnapshots:
    def test_empty_snapshots(self):
        report = compare_snapshots([], [])
        assert report.diffs == []
        assert report.new_metrics == []
        assert report.removed_metrics == []

    def test_detects_new_metric(self):
        prev = [_make_metric("a", 1.0, MetricStatus.OK)]
        curr = [
            _make_metric("a", 1.0, MetricStatus.OK),
            _make_metric("b", 2.0, MetricStatus.WARNING),
        ]
        report = compare_snapshots(prev, curr)
        assert "b" in report.new_metrics
        assert "a" not in report.new_metrics

    def test_detects_removed_metric(self):
        prev = [
            _make_metric("a", 1.0, MetricStatus.OK),
            _make_metric("b", 2.0, MetricStatus.OK),
        ]
        curr = [_make_metric("a", 1.0, MetricStatus.OK)]
        report = compare_snapshots(prev, curr)
        assert "b" in report.removed_metrics

    def test_diff_value_delta(self):
        prev = [_make_metric("latency", 100.0, MetricStatus.OK)]
        curr = [_make_metric("latency", 200.0, MetricStatus.WARNING)]
        report = compare_snapshots(prev, curr)
        assert len(report.diffs) == 1
        assert report.diffs[0].value_delta == pytest.approx(100.0)

    def test_changed_filters_status_changes(self):
        prev = [
            _make_metric("a", 1.0, MetricStatus.OK),
            _make_metric("b", 1.0, MetricStatus.OK),
        ]
        curr = [
            _make_metric("a", 1.0, MetricStatus.OK),
            _make_metric("b", 5.0, MetricStatus.CRITICAL),
        ]
        report = compare_snapshots(prev, curr)
        assert len(report.changed) == 1
        assert report.changed[0].name == "b"

    def test_to_dict_structure(self):
        prev = [_make_metric("m", 1.0, MetricStatus.OK)]
        curr = [_make_metric("m", 2.0, MetricStatus.WARNING)]
        report = compare_snapshots(prev, curr)
        d = report.to_dict()
        assert "diffs" in d
        assert "new_metrics" in d
        assert "removed_metrics" in d
        assert d["changed_count"] == 1
