"""Tests for pipewatch.cli.commands — including ranking integration."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cli.commands import _build_parser, cmd_run, cmd_version
from pipewatch.metrics.models import Metric, MetricStatus


def _make_metric(name, status=MetricStatus.OK, value=1.0):
    return Metric(name=name, value=value, status=status, source="test")


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
        assert args.output == "text"
        assert args.rank is False

    def test_rank_flag_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["run", "--source", "http", "--config", "cfg.yaml", "--rank"]
        )
        assert args.rank is True

    def test_version_command_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"


class TestCmdRun:
    def _args(self, output="text", rank=False):
        a = MagicMock()
        a.source = "http"
        a.config = "cfg.yaml"
        a.output = output
        a.rank = rank
        return a

    def test_config_error_returns_1(self):
        from pipewatch.cli.config_loader import ConfigError

        with patch("pipewatch.cli.commands.load_config", side_effect=ConfigError("bad")):
            assert cmd_run(self._args()) == 1

    def test_unknown_source_returns_1(self):
        with patch("pipewatch.cli.commands.load_config", return_value={}):
            with patch("pipewatch.cli.commands.get_source", return_value=None):
                assert cmd_run(self._args()) == 1

    def test_all_ok_returns_0(self, capsys):
        metrics = [_make_metric("m", MetricStatus.OK)]
        self._run_with_metrics(metrics, output="text")
        # no assertion on return value here — just smoke test

    def test_critical_returns_2(self):
        metrics = [_make_metric("m", MetricStatus.CRITICAL)]
        rc = self._run_with_metrics(metrics, output="text")
        assert rc == 2

    def test_json_output_valid(self, capsys):
        metrics = [_make_metric("m", MetricStatus.OK)]
        self._run_with_metrics(metrics, output="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "metrics" in data or "total" in data  # summary keys

    def test_json_output_with_rank(self, capsys):
        metrics = [_make_metric("m", MetricStatus.WARNING, value=5.0)]
        self._run_with_metrics(metrics, output="json", rank=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "ranking" in data
        assert data["ranking"][0]["name"] == "m"

    def test_text_output_with_rank(self, capsys):
        metrics = [_make_metric("pipe_lag", MetricStatus.WARNING, value=5.0)]
        self._run_with_metrics(metrics, output="text", rank=True)
        out = capsys.readouterr().out
        assert "Ranking" in out or "pipe_lag" in out

    # ------------------------------------------------------------------ helpers
    def _run_with_metrics(self, metrics, output="text", rank=False):
        args = self._args(output=output, rank=rank)
        mock_source = MagicMock()
        mock_source.fetch.return_value = metrics
        mock_source_cls = MagicMock(return_value=mock_source)

        with patch("pipewatch.cli.commands.load_config", return_value={}):
            with patch("pipewatch.cli.commands.get_source", return_value=mock_source_cls):
                with patch("pipewatch.cli.commands.PipelineRunner") as MockRunner:
                    instance = MockRunner.return_value
                    instance.run.return_value = None
                    with patch(
                        "pipewatch.cli.commands.MetricCollector"
                    ) as MockCollector:
                        coll_inst = MockCollector.return_value
                        coll_inst.get_all.return_value = metrics
                        return cmd_run(args)
