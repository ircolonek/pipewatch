"""Tests for pipewatch.reporting.exporter."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from datetime import datetime

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.summary import build_summary
from pipewatch.reporting.exporter import export_csv, export_json, export_to_file


def _make_metric(name: str, status: MetricStatus, value: float = 1.0) -> Metric:
    return Metric(
        name=name,
        source="test_source",
        value=value,
        status=status,
        timestamp=datetime(2024, 1, 15, 12, 0, 0),
    )


@pytest.fixture()
def sample_report():
    metrics = [
        _make_metric("row_count", MetricStatus.OK, 500),
        _make_metric("error_rate", MetricStatus.WARNING, 0.08),
        _make_metric("latency_ms", MetricStatus.CRITICAL, 9500),
    ]
    return build_summary(metrics)


class TestExportJson:
    def test_returns_valid_json(self, sample_report):
        raw = export_json(sample_report)
        data = json.loads(raw)  # must not raise
        assert isinstance(data, dict)

    def test_contains_metric_names(self, sample_report):
        raw = export_json(sample_report)
        assert "row_count" in raw
        assert "error_rate" in raw
        assert "latency_ms" in raw

    def test_summary_counts_present(self, sample_report):
        data = json.loads(export_json(sample_report))
        assert data["total"] == 3
        assert data["ok"] == 1
        assert data["warning"] == 1
        assert data["critical"] == 1

    def test_empty_report(self):
        report = build_summary([])
        data = json.loads(export_json(report))
        assert data["total"] == 0
        assert data["metrics"] == []


class TestExportCsv:
    def test_returns_string_with_header(self, sample_report):
        raw = export_csv(sample_report)
        assert "name" in raw
        assert "status" in raw

    def test_row_count_matches_metrics(self, sample_report):
        raw = export_csv(sample_report)
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        assert len(rows) == 3

    def test_status_values_present(self, sample_report):
        raw = export_csv(sample_report)
        assert "ok" in raw.lower() or "OK" in raw
        assert "warning" in raw.lower() or "WARNING" in raw

    def test_empty_report_has_only_header(self):
        report = build_summary([])
        raw = export_csv(report)
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)
        assert rows == []


class TestExportToFile:
    def test_writes_json_file(self, sample_report):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            path = tmp.name
        try:
            export_to_file(sample_report, path, fmt="json")
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            assert data["total"] == 3
        finally:
            os.unlink(path)

    def test_writes_csv_file(self, sample_report):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            path = tmp.name
        try:
            export_to_file(sample_report, path, fmt="csv")
            with open(path, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 3
        finally:
            os.unlink(path)

    def test_raises_on_unknown_format(self, sample_report):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_to_file(sample_report, "/tmp/out.xml", fmt="xml")
