"""Tests for pipewatch.reporting.dashboard."""
import datetime
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.dashboard import render_dashboard, _bar


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_metric(name: str, status: MetricStatus, value=1.0) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


_FIXED_TS = datetime.datetime(2024, 6, 1, 12, 0, 0)


# ---------------------------------------------------------------------------
# _bar
# ---------------------------------------------------------------------------

class TestBar:
    def test_full(self):
        assert _bar(1.0, 10) == "[##########]"

    def test_empty(self):
        assert _bar(0.0, 10) == "[----------]"

    def test_half(self):
        result = _bar(0.5, 10)
        assert result.count("#") == 5
        assert result.count("-") == 5

    def test_clamps_above_one(self):
        assert _bar(2.0, 4) == "[####]"

    def test_clamps_below_zero(self):
        assert _bar(-1.0, 4) == "[----]"


# ---------------------------------------------------------------------------
# render_dashboard
# ---------------------------------------------------------------------------

class TestRenderDashboard:
    def _report(self, metrics):
        return build_summary(metrics)

    def test_contains_title(self):
        report = self._report([])
        out = render_dashboard(report, title="My Dashboard", timestamp=_FIXED_TS)
        assert "My Dashboard" in out

    def test_contains_timestamp(self):
        report = self._report([])
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "2024-06-01 12:00:00 UTC" in out

    def test_empty_metrics_zero_total(self):
        report = self._report([])
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "0/0 OK" in out

    def test_all_ok_shows_full_bar(self):
        metrics = [_make_metric("m1", MetricStatus.OK), _make_metric("m2", MetricStatus.OK)]
        report = self._report(metrics)
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "2/2 OK" in out

    def test_metric_names_present(self):
        metrics = [_make_metric("pipeline.latency", MetricStatus.WARNING, value=3.5)]
        report = self._report(metrics)
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "pipeline.latency" in out

    def test_metric_value_present(self):
        metrics = [_make_metric("row_count", MetricStatus.OK, value=42)]
        report = self._report(metrics)
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "42" in out

    def test_critical_status_icon_present(self):
        metrics = [_make_metric("dead_pipe", MetricStatus.CRITICAL)]
        report = self._report(metrics)
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "✖" in out or "critical" in out.lower()

    def test_none_value_renders_dash(self):
        m = Metric(name="no_val", value=None, status=MetricStatus.UNKNOWN, source="test")
        report = self._report([m])
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "—" in out

    def test_default_timestamp_used_when_none(self):
        report = self._report([])
        out = render_dashboard(report)  # no timestamp kwarg
        assert "UTC" in out

    def test_separator_lines_present(self):
        report = self._report([])
        out = render_dashboard(report, timestamp=_FIXED_TS)
        assert "===" in out
        assert "---" in out
