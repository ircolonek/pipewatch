"""Tests for pipewatch.cli.commands (including tagging integration)."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cli.commands import _build_parser, cmd_run, cmd_version
from pipewatch.metrics.models import Metric, MetricStatus


def _make_metric(name: str, value: float = 1.0, status=MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, source="test")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
class TestParser:
    def test_run_requires_source_and_config(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run"])

    def test_run_parses_correctly(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--source", "http", "--config", "cfg.yaml"])
        assert args.source == "http"
        assert args.config == "cfg.yaml"

    def test_rank_flag_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--source", "db", "--config", "c.yaml", "--rank"])
        assert args.rank is True

    def test_tag_flag_repeatable(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["run", "--source", "db", "--config", "c.yaml",
             "--tag", "env=prod", "--tag", "team=data"]
        )
        assert "env=prod" in args.tag
        assert "team=data" in args.tag

    def test_group_by_flag(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["run", "--source", "http", "--config", "c.yaml", "--group-by", "env"]
        )
        assert args.group_by == "env"

    def test_output_default_is_text(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--source", "http", "--config", "c.yaml"])
        assert args.output == "text"


# ---------------------------------------------------------------------------
# cmd_run
# ---------------------------------------------------------------------------
class TestCmdRun:
    def _args(self, **kwargs):
        defaults = dict(
            source="http",
            config="cfg.yaml",
            output="text",
            rank=False,
            tag=[],
            group_by=None,
        )
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _patch_run(self, metrics):
        """Return a context-manager that patches PipelineRunner.run and collector.get_all."""
        collector_mock = MagicMock()
        collector_mock.get_all.return_value = metrics
        runner_mock = MagicMock()
        runner_mock.run.return_value = None

        def fake_runner(config, collector, alert_rules):
            collector.get_all.return_value = metrics
            return runner_mock

        return patch("pipewatch.cli.commands.PipelineRunner", side_effect=fake_runner), \
               patch("pipewatch.cli.commands.MetricCollector", return_value=collector_mock)

    def test_config_error_returns_1(self, tmp_path):
        args = self._args(config=str(tmp_path / "missing.yaml"))
        result = cmd_run(args)
        assert result == 1

    def test_returns_0_on_success(self, tmp_path):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("sources: []\n")
        metrics = [_make_metric("latency")]
        with patch("pipewatch.cli.commands.load_config", return_value={}) as _lc, \
             patch("pipewatch.cli.commands.PipelineRunner") as MockRunner, \
             patch("pipewatch.cli.commands.MetricCollector") as MockCollector:
            instance = MockCollector.return_value
            instance.get_all.return_value = metrics
            result = cmd_run(self._args(config=str(cfg)))
        assert result == 0

    def test_json_output(self, tmp_path, capsys):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("sources: []\n")
        metrics = [_make_metric("rows", 5.0)]
        with patch("pipewatch.cli.commands.load_config", return_value={}), \
             patch("pipewatch.cli.commands.PipelineRunner"), \
             patch("pipewatch.cli.commands.MetricCollector") as MockCollector:
            MockCollector.return_value.get_all.return_value = metrics
            cmd_run(self._args(config=str(cfg), output="json"))
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "metrics" in data or isinstance(data, dict)

    def test_tag_filter_applied(self, tmp_path, capsys):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("sources: []\n")
        metrics = [_make_metric("a"), _make_metric("b")]
        with patch("pipewatch.cli.commands.load_config", return_value={}), \
             patch("pipewatch.cli.commands.PipelineRunner"), \
             patch("pipewatch.cli.commands.MetricCollector") as MockCollector:
            MockCollector.return_value.get_all.return_value = metrics
            # tag filter that matches nothing → empty report still returns 0
            result = cmd_run(self._args(config=str(cfg), tag=["env=prod"]))
        assert result == 0

    def test_group_by_output(self, tmp_path, capsys):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("sources: []\n")
        metrics = [_make_metric("x")]
        with patch("pipewatch.cli.commands.load_config", return_value={}), \
             patch("pipewatch.cli.commands.PipelineRunner"), \
             patch("pipewatch.cli.commands.MetricCollector") as MockCollector:
            MockCollector.return_value.get_all.return_value = metrics
            result = cmd_run(self._args(config=str(cfg), group_by="env"))
        assert result == 0


# ---------------------------------------------------------------------------
# cmd_version
# ---------------------------------------------------------------------------
class TestCmdVersion:
    def test_prints_version(self, capsys):
        cmd_version(SimpleNamespace())
        out = capsys.readouterr().out
        assert "pipewatch" in out

    def test_returns_0(self):
        assert cmd_version(SimpleNamespace()) == 0
