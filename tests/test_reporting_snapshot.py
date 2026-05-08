"""Tests for pipewatch.reporting.snapshot."""
from __future__ import annotations

import datetime
from typing import Optional

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.snapshot import (
    MetricSnapshot,
    PipelineSnapshot,
    capture_snapshot,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_metric(
    name: str = "rows_processed",
    value: float = 100.0,
    status: MetricStatus = MetricStatus.OK,
    source: str = "db",
) -> Metric:
    m = Metric(name=name, value=value, source=source)
    m.status = status
    return m


FIXED_TS = datetime.datetime(2024, 6, 1, 12, 0, 0)


# ---------------------------------------------------------------------------
# MetricSnapshot
# ---------------------------------------------------------------------------

class TestMetricSnapshot:
    def _snap(self, **kw) -> MetricSnapshot:
        defaults = dict(
            name="latency",
            value=42.0,
            status=MetricStatus.WARNING,
            source="http",
            captured_at=FIXED_TS,
        )
        defaults.update(kw)
        return MetricSnapshot(**defaults)

    def test_to_dict_keys(self):
        d = self._snap().to_dict()
        assert set(d) == {"name", "value", "status", "source", "captured_at"}

    def test_to_dict_status_is_string(self):
        d = self._snap(status=MetricStatus.CRITICAL).to_dict()
        assert d["status"] == "critical"

    def test_to_dict_captured_at_is_iso(self):
        d = self._snap().to_dict()
        assert d["captured_at"] == FIXED_TS.isoformat()

    def test_to_dict_none_value(self):
        d = self._snap(value=None).to_dict()
        assert d["value"] is None


# ---------------------------------------------------------------------------
# PipelineSnapshot
# ---------------------------------------------------------------------------

class TestPipelineSnapshot:
    def _build(self) -> PipelineSnapshot:
        metrics = [
            _make_metric("a", status=MetricStatus.OK, source="db"),
            _make_metric("b", status=MetricStatus.WARNING, source="http"),
            _make_metric("c", status=MetricStatus.CRITICAL, source="db"),
        ]
        return capture_snapshot(metrics, taken_at=FIXED_TS)

    def test_to_dict_keys(self):
        d = self._build().to_dict()
        assert "taken_at" in d and "metrics" in d

    def test_metrics_length(self):
        snap = self._build()
        assert len(snap.metrics) == 3

    def test_by_status_ok(self):
        snap = self._build()
        assert len(snap.by_status(MetricStatus.OK)) == 1

    def test_by_status_critical(self):
        snap = self._build()
        assert len(snap.by_status(MetricStatus.CRITICAL)) == 1

    def test_by_source(self):
        snap = self._build()
        assert len(snap.by_source("db")) == 2
        assert len(snap.by_source("http")) == 1

    def test_sources_unique(self):
        snap = self._build()
        assert sorted(snap.sources()) == ["db", "http"]

    def test_taken_at_preserved(self):
        snap = self._build()
        assert snap.taken_at == FIXED_TS


# ---------------------------------------------------------------------------
# capture_snapshot
# ---------------------------------------------------------------------------

class TestCaptureSnapshot:
    def test_empty_metrics(self):
        snap = capture_snapshot([], taken_at=FIXED_TS)
        assert snap.metrics == []

    def test_snapshot_names_match(self):
        metrics = [_make_metric(name="x"), _make_metric(name="y")]
        snap = capture_snapshot(metrics, taken_at=FIXED_TS)
        names = [s.name for s in snap.metrics]
        assert names == ["x", "y"]

    def test_default_taken_at_is_recent(self):
        before = datetime.datetime.utcnow()
        snap = capture_snapshot([])
        after = datetime.datetime.utcnow()
        assert before <= snap.taken_at <= after
