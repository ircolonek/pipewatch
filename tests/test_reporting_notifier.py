"""Tests for pipewatch.reporting.notifier.AlertNotifier."""
import time
import pytest

from pipewatch.alerts.rules import AlertRule, AlertSeverity
from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.notifier import AlertNotifier


def _make_metric(name: str = "row_count", source: str = "db", status: MetricStatus = MetricStatus.CRITICAL) -> Metric:
    return Metric(name=name, value=0.0, source=source, status=status)


def _make_rule(metric_name: str = "row_count", severity: AlertSeverity = AlertSeverity.CRITICAL) -> AlertRule:
    return AlertRule(
        metric_name=metric_name,
        on_status=MetricStatus.CRITICAL,
        severity=severity,
        message_template="{metric_name} is {status}",
    )


class TestAlertNotifierInit:
    def test_positive_cooldown_accepted(self):
        n = AlertNotifier(cooldown_seconds=60)
        assert n.cooldown_seconds == 60

    def test_zero_cooldown_raises(self):
        with pytest.raises(ValueError):
            AlertNotifier(cooldown_seconds=0)

    def test_negative_cooldown_raises(self):
        with pytest.raises(ValueError):
            AlertNotifier(cooldown_seconds=-1)


class TestShouldSend:
    def test_first_call_always_sends(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule, metric = _make_rule(), _make_metric()
        assert n.should_send(rule, metric) is True

    def test_second_call_within_cooldown_suppressed(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule, metric = _make_rule(), _make_metric()
        n.should_send(rule, metric)
        assert n.should_send(rule, metric) is False

    def test_call_after_cooldown_sends_again(self, monkeypatch):
        n = AlertNotifier(cooldown_seconds=1)
        rule, metric = _make_rule(), _make_metric()
        n.should_send(rule, metric)
        monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 2)
        assert n.should_send(rule, metric) is True

    def test_different_sources_are_independent(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule = _make_rule()
        m1 = _make_metric(source="db")
        m2 = _make_metric(source="http")
        assert n.should_send(rule, m1) is True
        assert n.should_send(rule, m2) is True

    def test_different_severities_are_independent(self):
        n = AlertNotifier(cooldown_seconds=300)
        metric = _make_metric()
        r1 = _make_rule(severity=AlertSeverity.CRITICAL)
        r2 = _make_rule(severity=AlertSeverity.WARNING)
        assert n.should_send(r1, metric) is True
        assert n.should_send(r2, metric) is True


class TestSuppressedCount:
    def test_zero_before_any_call(self):
        n = AlertNotifier()
        rule, metric = _make_rule(), _make_metric()
        assert n.suppressed_count(rule, metric) == 0

    def test_increments_on_suppression(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule, metric = _make_rule(), _make_metric()
        n.should_send(rule, metric)  # sends
        n.should_send(rule, metric)  # suppressed
        n.should_send(rule, metric)  # suppressed
        assert n.suppressed_count(rule, metric) == 2


class TestReset:
    def test_reset_all_clears_history(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule, metric = _make_rule(), _make_metric()
        n.should_send(rule, metric)
        n.reset()
        assert n.should_send(rule, metric) is True

    def test_reset_specific_key(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule, metric = _make_rule(), _make_metric()
        n.should_send(rule, metric)
        n.reset(rule=rule, metric=metric)
        assert n.should_send(rule, metric) is True

    def test_reset_specific_does_not_affect_other(self):
        n = AlertNotifier(cooldown_seconds=300)
        rule = _make_rule()
        m1 = _make_metric(source="db")
        m2 = _make_metric(source="http")
        n.should_send(rule, m1)
        n.should_send(rule, m2)
        n.reset(rule=rule, metric=m1)
        assert n.should_send(rule, m1) is True   # reset
        assert n.should_send(rule, m2) is False  # still throttled
