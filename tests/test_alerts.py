import pytest
from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.alerts.rules import AlertRule, AlertSeverity
from pipewatch.alerts.dispatcher import AlertDispatcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metric(name="latency", value=120.0, status=MetricStatus.CRITICAL):
    return Metric(name=name, value=value, status=status, unit="ms")


# ---------------------------------------------------------------------------
# AlertRule tests
# ---------------------------------------------------------------------------

class TestAlertRule:
    def test_matches_on_status(self):
        rule = AlertRule(name="high_latency", metric_name="latency")
        metric = _make_metric(status=MetricStatus.CRITICAL)
        assert rule.matches(metric) is True

    def test_no_match_wrong_metric_name(self):
        rule = AlertRule(name="high_latency", metric_name="throughput")
        metric = _make_metric()
        assert rule.matches(metric) is False

    def test_no_match_ok_status(self):
        rule = AlertRule(name="high_latency", metric_name="latency")
        metric = _make_metric(status=MetricStatus.OK)
        assert rule.matches(metric) is False

    def test_custom_condition(self):
        rule = AlertRule(
            name="very_high",
            metric_name="latency",
            condition=lambda m: m.value > 200,
        )
        assert rule.matches(_make_metric(value=250)) is True
        assert rule.matches(_make_metric(value=100)) is False

    def test_format_message(self):
        rule = AlertRule(name="high_latency", metric_name="latency")
        msg = rule.format_message(_make_metric())
        assert "latency" in msg
        assert "critical" in msg

    def test_to_dict(self):
        rule = AlertRule(
            name="high_latency",
            metric_name="latency",
            severity=AlertSeverity.CRITICAL,
        )
        d = rule.to_dict()
        assert d["name"] == "high_latency"
        assert d["severity"] == "critical"
        assert "critical" in d["trigger_on"]

    def test_repr(self):
        rule = AlertRule(name="r", metric_name="m")
        assert "AlertRule" in repr(rule)


# ---------------------------------------------------------------------------
# AlertDispatcher tests
# ---------------------------------------------------------------------------

class TestAlertDispatcher:
    def test_evaluate_fires_alert(self):
        fired = []
        dispatcher = AlertDispatcher(on_alert=lambda a: fired.append(a))
        rule = AlertRule(name="high_latency", metric_name="latency")
        dispatcher.add_rule(rule)
        dispatcher.evaluate(_make_metric(status=MetricStatus.CRITICAL))
        assert len(fired) == 1
        assert fired[0]["rule"] == "high_latency"

    def test_evaluate_no_alert_on_ok(self):
        fired = []
        dispatcher = AlertDispatcher(on_alert=lambda a: fired.append(a))
        rule = AlertRule(name="high_latency", metric_name="latency")
        dispatcher.add_rule(rule)
        dispatcher.evaluate(_make_metric(status=MetricStatus.OK))
        assert len(fired) == 0

    def test_multiple_rules(self):
        fired = []
        dispatcher = AlertDispatcher(on_alert=lambda a: fired.append(a))
        dispatcher.add_rule(AlertRule("r1", "latency", trigger_on=[MetricStatus.WARNING]))
        dispatcher.add_rule(AlertRule("r2", "latency", trigger_on=[MetricStatus.CRITICAL]))
        dispatcher.evaluate(_make_metric(status=MetricStatus.WARNING))
        assert len(fired) == 1
        assert fired[0]["rule"] == "r1"

    def test_history_recorded(self):
        dispatcher = AlertDispatcher()
        rule = AlertRule("r", "latency")
        dispatcher.add_rule(rule)
        dispatcher.evaluate(_make_metric())
        assert len(dispatcher.history) == 1
