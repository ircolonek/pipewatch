"""Tests for pipewatch.sources.db_source.DbSource."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.metrics.models import MetricStatus
from pipewatch.sources.base import get_source
from pipewatch.sources.db_source import DbSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(return_values: list):
    """Build a mock DB-API 2.0 connection whose cursor returns *return_values* in order."""
    cursor = MagicMock()
    cursor.fetchone.side_effect = return_values
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestDbSourceRegistration:
    def test_registered_under_db_key(self):
        cls = get_source("db")
        assert cls is DbSource

    def test_source_name(self):
        src = DbSource(config={"queries": [], "_conn": _make_conn([])})
        assert src.source_name() == "db"


# ---------------------------------------------------------------------------
# Fetch behaviour
# ---------------------------------------------------------------------------

class TestDbSourceFetch:
    def _make_source(self, queries, return_values):
        conn = _make_conn(return_values)
        return DbSource(
            config={
                "queries": queries,
                "_conn": conn,
            }
        )

    def test_returns_metric_objects(self):
        src = self._make_source(
            queries=[{"name": "row_count", "sql": "SELECT COUNT(*) FROM t"}],
            return_values=[(42,)],
        )
        metrics = src.fetch()
        assert len(metrics) == 1
        assert metrics[0].name == "row_count"
        assert metrics[0].value == 42.0
        assert metrics[0].source == "db"

    def test_multiple_queries(self):
        src = self._make_source(
            queries=[
                {"name": "a", "sql": "SELECT 1"},
                {"name": "b", "sql": "SELECT 2"},
            ],
            return_values=[(1,), (2,)],
        )
        metrics = src.fetch()
        assert [m.name for m in metrics] == ["a", "b"]
        assert [m.value for m in metrics] == [1.0, 2.0]

    def test_critical_threshold_sets_status(self):
        src = self._make_source(
            queries=[{"name": "lag", "sql": "SELECT 99", "critical_threshold": 50.0}],
            return_values=[(99,)],
        )
        metrics = src.fetch()
        assert metrics[0].status == MetricStatus.CRITICAL

    def test_null_row_defaults_to_zero(self):
        src = self._make_source(
            queries=[{"name": "empty", "sql": "SELECT NULL"}],
            return_values=[(None,)],
        )
        metrics = src.fetch()
        assert metrics[0].value == 0.0

    def test_query_error_captured_in_metadata(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = RuntimeError("table not found")
        conn.cursor.return_value = cursor
        src = DbSource(config={"queries": [{"name": "bad", "sql": "SELECT bad"}], "_conn": conn})
        metrics = src.fetch()
        assert metrics[0].value == 0.0
        assert "table not found" in metrics[0].metadata["error"]

    def test_query_time_recorded_in_metadata(self):
        src = self._make_source(
            queries=[{"name": "t", "sql": "SELECT 1"}],
            return_values=[(1,)],
        )
        metrics = src.fetch()
        assert "query_time_s" in metrics[0].metadata
