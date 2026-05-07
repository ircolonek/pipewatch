"""Tests for pipewatch.reporting.baseline."""
import json
import os
import tempfile

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.baseline import (
    BaselineEntry,
    BaselineReport,
    compare_to_baseline,
    load_baseline,
)


def _make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


# ---------------------------------------------------------------------------
# BaselineEntry
# ---------------------------------------------------------------------------

class TestBaselineEntry:
    def test_within_tolerance_exact(self):
        entry = BaselineEntry(metric_name="m", expected_value=100.0, tolerance=0.1)
        assert entry.is_within_tolerance(100.0) is True

    def test_within_tolerance_edge(self):
        entry = BaselineEntry(metric_name="m", expected_value=100.0, tolerance=0.1)
        assert entry.is_within_tolerance(110.0) is True

    def test_outside_tolerance(self):
        entry = BaselineEntry(metric_name="m", expected_value=100.0, tolerance=0.1)
        assert entry.is_within_tolerance(115.0) is False

    def test_zero_expected_zero_actual(self):
        entry = BaselineEntry(metric_name="m", expected_value=0.0)
        assert entry.is_within_tolerance(0.0) is True

    def test_zero_expected_nonzero_actual(self):
        entry = BaselineEntry(metric_name="m", expected_value=0.0)
        assert entry.is_within_tolerance(1.0) is False

    def test_roundtrip(self):
        entry = BaselineEntry(metric_name="latency", expected_value=42.5, tolerance=0.05)
        restored = BaselineEntry.from_dict(entry.to_dict())
        assert restored.metric_name == entry.metric_name
        assert restored.expected_value == entry.expected_value
        assert restored.tolerance == entry.tolerance


# ---------------------------------------------------------------------------
# BaselineReport
# ---------------------------------------------------------------------------

class TestBaselineReport:
    def test_all_pass_empty(self):
        report = BaselineReport()
        assert report.all_pass is True

    def test_all_pass_when_all_within(self):
        report = BaselineReport()
        report.add("m1", True, 10.0, 10.0)
        report.add("m2", True, 20.0, 19.5)
        assert report.all_pass is True

    def test_not_all_pass_when_one_fails(self):
        report = BaselineReport()
        report.add("m1", True, 10.0, 10.0)
        report.add("m2", False, 20.0, 30.0)
        assert report.all_pass is False

    def test_to_dict_structure(self):
        report = BaselineReport()
        report.add("m1", True, 5.0, 5.0)
        d = report.to_dict()
        assert "all_pass" in d
        assert "checks" in d
        assert d["checks"][0]["metric_name"] == "m1"


# ---------------------------------------------------------------------------
# load_baseline
# ---------------------------------------------------------------------------

class TestLoadBaseline:
    def test_missing_file_returns_empty(self, tmp_path):
        result = load_baseline(str(tmp_path / "nonexistent.json"))
        assert result == {}

    def test_loads_entries(self, tmp_path):
        data = [
            {"metric_name": "row_count", "expected_value": 500, "tolerance": 0.05}
        ]
        p = tmp_path / "baseline.json"
        p.write_text(json.dumps(data))
        result = load_baseline(str(p))
        assert "row_count" in result
        assert result["row_count"].tolerance == 0.05


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

class TestCompareToBaseline:
    def test_skips_metrics_not_in_baseline(self):
        metrics = [_make_metric("unknown", 99.0)]
        report = compare_to_baseline(metrics, {})
        assert report.entries == []

    def test_records_passing_check(self):
        baseline = {"latency": BaselineEntry("latency", 100.0, 0.1)}
        metrics = [_make_metric("latency", 105.0)]
        report = compare_to_baseline(metrics, baseline)
        assert len(report.entries) == 1
        assert report.entries[0]["within_tolerance"] is True

    def test_records_failing_check(self):
        baseline = {"latency": BaselineEntry("latency", 100.0, 0.1)}
        metrics = [_make_metric("latency", 200.0)]
        report = compare_to_baseline(metrics, baseline)
        assert report.entries[0]["within_tolerance"] is False
        assert report.all_pass is False

    def test_none_value_fails(self):
        baseline = {"m": BaselineEntry("m", 50.0)}
        m = Metric(name="m", value=None, status=MetricStatus.UNKNOWN, source="test")
        report = compare_to_baseline([m], baseline)
        assert report.entries[0]["within_tolerance"] is False
