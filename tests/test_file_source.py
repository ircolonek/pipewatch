"""Tests for pipewatch.sources.file_source.FileSource."""

import csv
import json
import os
import tempfile
from datetime import datetime

import pytest

from pipewatch.sources.base import get_source
from pipewatch.sources.file_source import FileSource


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {"name": "row_count", "value": 1200, "source": "etl", "timestamp": "2024-01-15T10:00:00"},
    {"name": "error_rate", "value": 0.03, "source": "etl", "timestamp": "2024-01-15T10:00:00"},
]


def _write_json(path: str, rows):
    with open(path, "w") as fh:
        json.dump(rows, fh)


def _write_csv(path: str, rows):
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

class TestFileSourceRegistration:
    def test_registered_under_file_key(self):
        cls = get_source("file")
        assert cls is FileSource

    def test_source_name(self):
        src = FileSource(path="/dev/null", format="json")
        assert src.source_name() == "file"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            FileSource(path="/dev/null", format="xml")


# ---------------------------------------------------------------------------
# JSON fetching
# ---------------------------------------------------------------------------

class TestFileSourceJsonFetch:
    def test_returns_metric_objects(self, tmp_path):
        p = tmp_path / "metrics.json"
        _write_json(str(p), SAMPLE_ROWS)
        src = FileSource(path=str(p), format="json")
        metrics = src.fetch()
        assert len(metrics) == 2
        assert metrics[0].name == "row_count"
        assert metrics[0].value == 1200.0

    def test_timestamp_parsed(self, tmp_path):
        p = tmp_path / "metrics.json"
        _write_json(str(p), SAMPLE_ROWS)
        src = FileSource(path=str(p), format="json")
        m = src.fetch()[0]
        assert isinstance(m.timestamp, datetime)

    def test_missing_file_raises(self):
        src = FileSource(path="/nonexistent/metrics.json", format="json")
        with pytest.raises(FileNotFoundError):
            src.fetch()


# ---------------------------------------------------------------------------
# CSV fetching
# ---------------------------------------------------------------------------

class TestFileSourceCsvFetch:
    def test_returns_metric_objects(self, tmp_path):
        p = tmp_path / "metrics.csv"
        _write_csv(str(p), SAMPLE_ROWS)
        src = FileSource(path=str(p), format="csv")
        metrics = src.fetch()
        assert len(metrics) == 2
        assert metrics[1].name == "error_rate"
        assert metrics[1].value == pytest.approx(0.03)

    def test_source_field_preserved(self, tmp_path):
        p = tmp_path / "metrics.csv"
        _write_csv(str(p), SAMPLE_ROWS)
        src = FileSource(path=str(p), format="csv")
        assert src.fetch()[0].source == "etl"

    def test_missing_file_raises(self):
        src = FileSource(path="/nonexistent/metrics.csv", format="csv")
        with pytest.raises(FileNotFoundError):
            src.fetch()
