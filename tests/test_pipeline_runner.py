"""Tests for PipelineRunner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.alerts.dispatcher import AlertDispatcher


def _make_metric(name: str = "latency", value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, source="test")


class TestPipelineRunner:
    def _runner(self, metrics=None, thresholds=None):
        config = PipelineConfig(
            name="test-pipe",
            source_type="dummy",
            source_options={},
            thresholds=thresholds or {},
        )
        dispatcher = AlertDispatcher()
        runner = PipelineRunner(config=config, dispatcher=dispatcher)
        return runner, dispatcher

    def test_run_calls_source_fetch(self):
        metrics = [_make_metric()]
        mock_source_instance = MagicMock()
        mock_source_instance.source_name.return_value = "dummy"
        mock_source_instance.fetch.return_value = metrics
        mock_source_cls = MagicMock(return_value=mock_source_instance)

        runner, _ = self._runner()
        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_source_cls):
            runner.run()

        mock_source_instance.fetch.assert_called_once()

    def test_run_records_metrics_in_collector(self):
        metrics = [_make_metric("row_count", 50.0)]
        mock_source_instance = MagicMock()
        mock_source_instance.source_name.return_value = "dummy"
        mock_source_instance.fetch.return_value = metrics
        mock_source_cls = MagicMock(return_value=mock_source_instance)

        runner, _ = self._runner()
        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_source_cls):
            runner.run()

        collected = runner.collector.get_all()
        assert any(m.name == "row_count" for m in collected)

    def test_run_raises_on_unknown_source(self):
        runner, _ = self._runner()
        with patch("pipewatch.pipeline.runner.get_source", return_value=None):
            with pytest.raises(ValueError, match="Unknown source type"):
                runner.run()

    def test_run_returns_fired_alerts(self):
        from pipewatch.alerts.rules import AlertRule
        from pipewatch.metrics.models import MetricStatus

        metrics = [Metric(name="latency", value=9.9, source="test", status=MetricStatus.CRITICAL)]
        mock_source_instance = MagicMock()
        mock_source_instance.source_name.return_value = "dummy"
        mock_source_instance.fetch.return_value = metrics
        mock_source_cls = MagicMock(return_value=mock_source_instance)

        runner, dispatcher = self._runner()
        rule = AlertRule(
            metric_name="latency",
            severity="critical",
            on_status=[MetricStatus.CRITICAL],
            message_template="latency is critical",
        )
        dispatcher.add_rule(rule)

        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_source_cls):
            fired = runner.run()

        assert len(fired) >= 1
