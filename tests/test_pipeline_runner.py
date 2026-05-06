"""Tests for pipewatch.pipeline.runner (with history integration)."""

import pytest
from unittest.mock import MagicMock, patch

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.metrics.collector import MetricCollector
from pipewatch.pipeline.runner import PipelineConfig, PipelineRunner
from pipewatch.reporting.history import MetricHistory


def _make_metric(name: str, value: float = 1.0, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


@pytest.fixture()
def _runner(tmp_path):
    """Return a (runner, history) pair wired to a temp history file."""
    path = str(tmp_path / "history.json")
    history = MetricHistory(path)
    config = PipelineConfig(source_name="dummy", source_config={})
    collector = MetricCollector()
    runner = PipelineRunner(config, collector=collector, history=history)
    return runner, history


class TestPipelineRunner:
    def test_run_calls_source_fetch(self, tmp_path):
        config = PipelineConfig(source_name="http", source_config={})
        mock_source_instance = MagicMock()
        mock_source_instance.fetch.return_value = []
        mock_source_cls = MagicMock(return_value=mock_source_instance)

        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_source_cls):
            runner = PipelineRunner(config)
            runner.run()

        mock_source_instance.fetch.assert_called_once()

    def test_run_records_metrics_in_collector(self, tmp_path):
        config = PipelineConfig(source_name="dummy", source_config={})
        metrics = [_make_metric("cpu"), _make_metric("mem")]
        mock_source = MagicMock()
        mock_source.fetch.return_value = metrics
        mock_cls = MagicMock(return_value=mock_source)

        collector = MetricCollector()
        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_cls):
            runner = PipelineRunner(config, collector=collector)
            runner.run()

        names = [m.name for m in collector.get_all()]
        assert "cpu" in names and "mem" in names

    def test_run_persists_history(self, tmp_path):
        path = str(tmp_path / "h.json")
        history = MetricHistory(path)
        config = PipelineConfig(source_name="dummy", source_config={})
        metrics = [_make_metric("disk", 90.0, MetricStatus.CRITICAL)]
        mock_source = MagicMock()
        mock_source.fetch.return_value = metrics
        mock_cls = MagicMock(return_value=mock_source)

        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_cls):
            runner = PipelineRunner(config, history=history)
            runner.run()

        # Reload from disk
        h2 = MetricHistory(path)
        assert len(h2.get("disk")) == 1
        assert h2.get("disk")[0].status == "critical"

    def test_unknown_source_raises(self):
        config = PipelineConfig(source_name="nonexistent")
        with patch("pipewatch.pipeline.runner.get_source", return_value=None):
            runner = PipelineRunner(config)
            with pytest.raises(ValueError, match="Unknown source"):
                runner.run()

    def test_run_without_history_does_not_crash(self):
        config = PipelineConfig(source_name="dummy")
        mock_source = MagicMock()
        mock_source.fetch.return_value = [_make_metric("x")]
        mock_cls = MagicMock(return_value=mock_source)

        with patch("pipewatch.pipeline.runner.get_source", return_value=mock_cls):
            runner = PipelineRunner(config)  # no history kwarg
            result = runner.run()

        assert isinstance(result, list)
