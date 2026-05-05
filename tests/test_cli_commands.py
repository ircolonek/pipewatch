"""Tests for pipewatch.cli.commands (main entry-point)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from pipewatch.cli.commands import _build_parser, main


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParser:
    def test_run_requires_source_and_config(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run"])

    def test_run_parses_correctly(self):
        parser = _build_parser()
        args = parser.parse_args(["run", "--source", "http", "--config", "cfg.json"])
        assert args.source == "http"
        assert args.config == "cfg.json"
        assert args.export is None
        assert args.no_color is False

    def test_version_command_parsed(self):
        parser = _build_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"


# ---------------------------------------------------------------------------
# cmd_run integration (mocked internals)
# ---------------------------------------------------------------------------

class TestCmdRun:
    def _config_file(self, tmp_path: Path) -> Path:
        data = {"source_params": {"url": "http://example.com"}, "alert_rules": []}
        p = tmp_path / "cfg.json"
        p.write_text(json.dumps(data))
        return p

    @patch("pipewatch.cli.commands.PipelineRunner")
    @patch("pipewatch.cli.commands.build_summary")
    @patch("pipewatch.cli.commands.format_summary", return_value="summary text")
    @patch("pipewatch.cli.commands.format_alerts", return_value="")
    def test_exits_zero_when_no_critical(self, _fa, _fs, mock_summary, mock_runner_cls, tmp_path):
        mock_summary.return_value = MagicMock(critical_count=0)
        mock_runner_cls.return_value.run = MagicMock()

        cfg = self._config_file(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["run", "--source", "http", "--config", str(cfg), "--no-color"])
        assert exc.value.code == 0

    @patch("pipewatch.cli.commands.PipelineRunner")
    @patch("pipewatch.cli.commands.build_summary")
    @patch("pipewatch.cli.commands.format_summary", return_value="summary text")
    @patch("pipewatch.cli.commands.format_alerts", return_value="alerts text")
    def test_exits_one_when_critical(self, _fa, _fs, mock_summary, mock_runner_cls, tmp_path):
        mock_summary.return_value = MagicMock(critical_count=2)
        mock_runner_cls.return_value.run = MagicMock()

        cfg = self._config_file(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["run", "--source", "http", "--config", str(cfg)])
        assert exc.value.code == 1
