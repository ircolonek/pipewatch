"""Tests for pipewatch.reporting.digest."""
import datetime
from unittest.mock import patch

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.alerts.rules import AlertRule, AlertSeverity
from pipewatch.reporting.digest import DigestReport, build_digest


def _make_metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, source="test", status=status)


# ---------------------------------------------------------------------------
# DigestReport.to_dict
# ---------------------------------------------------------------------------

class TestDigestReportToDict:
    def test_keys_present(self):
        report = build_digest([])
        d = report.to_dict()
        assert set(d.keys()) == {"generated_at", "summary", "anomalies", "triggered_alerts"}

    def test_anomalies_is_list(self):
        report = build_digest([])
        assert isinstance(report.to_dict()["anomalies"], list)

    def test_triggered_alerts_is_list(self):
        report = build_digest([])
        assert isinstance(report.to_dict()["triggered_alerts"], list)


# ---------------------------------------------------------------------------
# build_digest – basic behaviour
# ---------------------------------------------------------------------------

class TestBuildDigest:
    def test_empty_metrics(self):
        report = build_digest([])
        assert report.summary.total == 0
        assert report.anomalies == []
        assert report.triggered_alerts == []

    def test_summary_total_matches_input(self):
        metrics = [_make_metric(f"m{i}", float(i)) for i in range(5)]
        report = build_digest(metrics)
        assert report.summary.total == 5

    def test_custom_timestamp_preserved(self):
        ts = "2024-01-01T00:00:00"
        report = build_digest([], timestamp=ts)
        assert report.generated_at == ts

    def test_default_timestamp_is_iso_string(self):
        report = build_digest([])
        # Should parse without error
        datetime.datetime.fromisoformat(report.generated_at)

    def test_anomalies_detected(self):
        # One outlier among otherwise uniform values
        metrics = [
            _make_metric("cpu", 10.0),
            _make_metric("cpu", 10.0),
            _make_metric("cpu", 10.0),
            _make_metric("cpu", 10.0),
            _make_metric("cpu", 999.0),
        ]
        report = build_digest(metrics, z_threshold=2.0)
        assert len(report.anomalies) >= 1

    def test_triggered_alerts_populated(self):
        metrics = [_make_metric("cpu", 95.0, MetricStatus.CRITICAL)]
        rule = AlertRule(
            name="cpu-critical",
            metric_name="cpu",
            trigger_status=MetricStatus.CRITICAL,
            severity=AlertSeverity.HIGH,
            message_template="CPU critical: {value}",
        )
        report = build_digest(metrics, rules=[rule])
        assert "cpu-critical" in report.triggered_alerts

    def test_non_matching_rule_not_triggered(self):
        metrics = [_make_metric("cpu", 10.0, MetricStatus.OK)]
        rule = AlertRule(
            name="cpu-critical",
            metric_name="cpu",
            trigger_status=MetricStatus.CRITICAL,
            severity=AlertSeverity.HIGH,
            message_template="CPU critical: {value}",
        )
        report = build_digest(metrics, rules=[rule])
        assert "cpu-critical" not in report.triggered_alerts

    def test_no_rules_no_triggered_alerts(self):
        metrics = [_make_metric("cpu", 95.0, MetricStatus.CRITICAL)]
        report = build_digest(metrics, rules=None)
        assert report.triggered_alerts == []
