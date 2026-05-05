"""Tests for pipewatch.reporting.summary."""
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.summary import SummaryReport, build_summary


def _make_metric(
    name: str = "m",
    value: float = 1.0,
    status: MetricStatus = MetricStatus.OK,
    source: str = "test_src",
) -> Metric:
    return Metric(name=name, value=value, status=status, source=source)


class TestBuildSummary:
    def test_empty_list(self):
        report = build_summary([])
        assert report.total == 0
        assert report.ok == 0
        assert report.warning == 0
        assert report.critical == 0
        assert report.unknown == 0
        assert report.sources == {}

    def test_all_ok(self):
        metrics = [_make_metric(status=MetricStatus.OK) for _ in range(3)]
        report = build_summary(metrics)
        assert report.total == 3
        assert report.ok == 3
        assert report.warning == 0
        assert report.critical == 0

    def test_mixed_statuses(self):
        metrics = [
            _make_metric(status=MetricStatus.OK),
            _make_metric(status=MetricStatus.WARNING),
            _make_metric(status=MetricStatus.CRITICAL),
            _make_metric(status=MetricStatus.UNKNOWN),
        ]
        report = build_summary(metrics)
        assert report.total == 4
        assert report.ok == 1
        assert report.warning == 1
        assert report.critical == 1
        assert report.unknown == 1

    def test_source_breakdown(self):
        metrics = [
            _make_metric(status=MetricStatus.OK, source="src_a"),
            _make_metric(status=MetricStatus.WARNING, source="src_a"),
            _make_metric(status=MetricStatus.CRITICAL, source="src_b"),
        ]
        report = build_summary(metrics)
        assert report.sources["src_a"]["ok"] == 1
        assert report.sources["src_a"]["warning"] == 1
        assert report.sources["src_b"]["critical"] == 1

    def test_none_source_uses_unknown_key(self):
        metric = Metric(name="m", value=0.0, status=MetricStatus.OK, source=None)
        report = build_summary([metric])
        assert "__unknown__" in report.sources

    def test_generated_at_is_set(self):
        report = build_summary([])
        assert report.generated_at != ""

    def test_to_dict_keys(self):
        report = build_summary([_make_metric()])
        d = report.to_dict()
        expected_keys = {"generated_at", "total", "ok", "warning", "critical", "unknown", "sources"}
        assert expected_keys == set(d.keys())

    def test_to_dict_values_match_report(self):
        metrics = [
            _make_metric(status=MetricStatus.OK),
            _make_metric(status=MetricStatus.CRITICAL),
        ]
        report = build_summary(metrics)
        d = report.to_dict()
        assert d["total"] == 2
        assert d["ok"] == 1
        assert d["critical"] == 1


class TestSummaryReport:
    def test_default_counts_are_zero(self):
        r = SummaryReport()
        assert r.total == r.ok == r.warning == r.critical == r.unknown == 0

    def test_sources_default_empty(self):
        r = SummaryReport()
        assert r.sources == {}
