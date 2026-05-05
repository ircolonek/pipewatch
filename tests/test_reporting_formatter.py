"""Tests for pipewatch.reporting.formatter."""

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.formatter import format_summary, format_alerts


def _make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    m = Metric(name=name, value=value)
    m.status = status
    return m


@pytest.fixture()
def mixed_report():
    metrics = [
        _make_metric("pipeline.rows", 1000.0, MetricStatus.OK),
        _make_metric("pipeline.latency", 9.5, MetricStatus.WARNING),
        _make_metric("pipeline.errors", 42.0, MetricStatus.CRITICAL),
    ]
    return build_summary(metrics)


@pytest.fixture()
def empty_report():
    return build_summary([])


class TestFormatSummary:
    def test_contains_header(self, mixed_report):
        output = format_summary(mixed_report, use_colour=False)
        assert "PipeWatch Pipeline Summary" in output

    def test_counts_are_correct(self, mixed_report):
        output = format_summary(mixed_report, use_colour=False)
        assert "Total metrics : 3" in output
        assert "OK            : 1" in output
        assert "Warning       : 1" in output
        assert "Critical      : 1" in output

    def test_metric_names_present(self, mixed_report):
        output = format_summary(mixed_report, use_colour=False)
        assert "pipeline.rows" in output
        assert "pipeline.latency" in output
        assert "pipeline.errors" in output

    def test_empty_report_placeholder(self, empty_report):
        output = format_summary(empty_report, use_colour=False)
        assert "(no metrics recorded)" in output

    def test_colour_codes_present_when_enabled(self, mixed_report):
        output = format_summary(mixed_report, use_colour=True)
        assert "\033[" in output

    def test_no_colour_codes_when_disabled(self, mixed_report):
        output = format_summary(mixed_report, use_colour=False)
        assert "\033[" not in output

    def test_returns_string(self, mixed_report):
        assert isinstance(format_summary(mixed_report, use_colour=False), str)


class TestFormatAlerts:
    def test_all_ok_returns_healthy_message(self):
        metrics = [_make_metric("a", 1.0, MetricStatus.OK)]
        report = build_summary(metrics)
        output = format_alerts(report, use_colour=False)
        assert "healthy" in output.lower()

    def test_non_ok_metrics_listed(self, mixed_report):
        output = format_alerts(mixed_report, use_colour=False)
        assert "pipeline.latency" in output
        assert "pipeline.errors" in output

    def test_ok_metrics_excluded(self, mixed_report):
        output = format_alerts(mixed_report, use_colour=False)
        assert "pipeline.rows" not in output

    def test_empty_report_returns_healthy(self, empty_report):
        output = format_alerts(empty_report, use_colour=False)
        assert "healthy" in output.lower()

    def test_colour_in_alert_digest(self, mixed_report):
        output = format_alerts(mixed_report, use_colour=True)
        assert "\033[" in output
