"""Utilities for loading and validating pipeline JSON config files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset({"source_params"})


class ConfigError(ValueError):
    """Raised when a pipeline config file is invalid."""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON pipeline config from *path* and return the parsed dict.

    Raises
    ------
    ConfigError
        If the file cannot be parsed or is missing required keys.
    FileNotFoundError
        If *path* does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with path.open() as fh:
            data: dict[str, Any] = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a JSON object at the top level.")

    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise ConfigError(f"Config file is missing required keys: {sorted(missing)}")

    _validate_alert_rules(data.get("alert_rules", []))
    return data


def _validate_alert_rules(rules: Any) -> None:
    if not isinstance(rules, list):
        raise ConfigError("'alert_rules' must be a list.")
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ConfigError(f"alert_rules[{i}] must be a dict.")
        for key in ("metric_name", "status", "severity", "message"):
            if key not in rule:
                raise ConfigError(f"alert_rules[{i}] is missing required key '{key}'.")
