"""Tests for pipewatch.cli.config_loader."""
import json
import pytest
from pathlib import Path

from pipewatch.cli.config_loader import load_config, ConfigError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, data: object, filename: str = "cfg.json") -> Path:
    p = tmp_path / filename
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestLoadConfigValid:
    def test_minimal_config(self, tmp_path):
        p = _write(tmp_path, {"source_params": {"url": "http://x"}})
        cfg = load_config(p)
        assert cfg["source_params"]["url"] == "http://x"

    def test_alert_rules_parsed(self, tmp_path):
        data = {
            "source_params": {},
            "alert_rules": [
                {"metric_name": "lag", "status": "CRITICAL", "severity": "high", "message": "lag high"},
            ],
        }
        p = _write(tmp_path, data)
        cfg = load_config(p)
        assert len(cfg["alert_rules"]) == 1

    def test_missing_alert_rules_defaults_to_empty(self, tmp_path):
        p = _write(tmp_path, {"source_params": {}})
        cfg = load_config(p)
        assert cfg.get("alert_rules", []) == []


# ---------------------------------------------------------------------------
# Error-path tests
# ---------------------------------------------------------------------------

class TestLoadConfigErrors:
    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "missing.json")

    def test_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            load_config(p)

    def test_top_level_not_dict(self, tmp_path):
        p = _write(tmp_path, [1, 2, 3])
        with pytest.raises(ConfigError, match="JSON object"):
            load_config(p)

    def test_missing_source_params(self, tmp_path):
        p = _write(tmp_path, {"alert_rules": []})
        with pytest.raises(ConfigError, match="source_params"):
            load_config(p)

    def test_alert_rules_not_list(self, tmp_path):
        p = _write(tmp_path, {"source_params": {}, "alert_rules": "bad"})
        with pytest.raises(ConfigError, match="list"):
            load_config(p)

    def test_alert_rule_missing_key(self, tmp_path):
        data = {
            "source_params": {},
            "alert_rules": [{"metric_name": "x"}],  # missing status/severity/message
        }
        p = _write(tmp_path, data)
        with pytest.raises(ConfigError, match="missing required key"):
            load_config(p)
