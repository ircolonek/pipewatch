"""Tests for the metrics collection module."""

import pytest
from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.metrics.collector import MetricCollector


class TestMetricModel:
    def test_metric_defaults(self):
        m = Metric(source="db", name="row_count", value=100.0)
        assert m.status == MetricStatus.UNKNOWN
        assert m.unit == ""
        assert m.tags == {}
        assert m.message is None

    def test_metric_to_dict(self):
        m = Metric(source="db", name="latency", value=42.5, unit="ms", status=MetricStatus.OK)
        d = m.to_dict()
        assert d["source"] == "db"
        assert d["name"] == "latency"
        assert d["value"] == 42.5
        assert d["unit"] == "ms"
        assert d["status"] == "ok"
        assert "timestamp" in d

    def test_metric_repr(self):
        m = Metric(source="etl", name="errors", value=3.0, status=MetricStatus.WARNING)
        assert "etl" in repr(m)
        assert "errors" in repr(m)
        assert "warning" in repr(m)


class TestMetricCollector:
    def test_record_no_thresholds(self):
        collector = MetricCollector(source="pipeline_a")
        metric = collector.record("row_count", 500)
        assert metric.status == MetricStatus.OK
        assert metric.source == "pipeline_a"

    def test_record_warning_threshold(self):
        thresholds = {"error_rate": {"warning": 5.0, "critical": 10.0}}
        collector = MetricCollector(source="pipeline_b", thresholds=thresholds)
        metric = collector.record("error_rate", 7.0)
        assert metric.status == MetricStatus.WARNING

    def test_record_critical_threshold(self):
        thresholds = {"latency_ms": {"warning": 200, "critical": 500}}
        collector = MetricCollector(source="pipeline_c", thresholds=thresholds)
        metric = collector.record("latency_ms", 600)
        assert metric.status == MetricStatus.CRITICAL

    def test_record_ok_below_warning(self):
        thresholds = {"queue_depth": {"warning": 100, "critical": 500}}
        collector = MetricCollector(source="pipeline_d", thresholds=thresholds)
        metric = collector.record("queue_depth", 50)
        assert metric.status == MetricStatus.OK

    def test_get_by_status(self):
        thresholds = {"errors": {"warning": 1, "critical": 10}}
        collector = MetricCollector(source="src", thresholds=thresholds)
        collector.record("errors", 0)
        collector.record("errors", 5)
        collector.record("errors", 15)
        assert len(collector.get_by_status(MetricStatus.OK)) == 1
        assert len(collector.get_by_status(MetricStatus.WARNING)) == 1
        assert len(collector.get_by_status(MetricStatus.CRITICAL)) == 1

    def test_summary(self):
        collector = MetricCollector(source="src")
        collector.record("a", 1)
        collector.record("b", 2)
        summary = collector.summary()
        assert summary["total"] == 2
        assert summary["ok"] == 2

    def test_clear(self):
        collector = MetricCollector(source="src")
        collector.record("x", 1)
        collector.clear()
        assert collector.get_all() == []

    def test_tags_stored(self):
        collector = MetricCollector(source="src")
        metric = collector.record("rows", 100, tags={"env": "prod"})
        assert metric.tags["env"] == "prod"
