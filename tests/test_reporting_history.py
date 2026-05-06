"""Tests for pipewatch.reporting.history."""

import json
import os
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.history import HistoryEntry, MetricHistory


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_metric(name: str, value: float, status: MetricStatus, source: str = "test") -> Metric:
    return Metric(name=name, value=value, status=status, source=source)


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------

class TestHistoryEntry:
    def test_to_dict_keys(self):
        e = HistoryEntry(metric_name="m", value=1.0, status="ok", source="s")
        d = e.to_dict()
        assert set(d.keys()) == {"metric_name", "value", "status", "source", "timestamp"}

    def test_roundtrip(self):
        e = HistoryEntry(metric_name="lag", value=42.5, status="warning", source="db")
        restored = HistoryEntry.from_dict(e.to_dict())
        assert restored.metric_name == e.metric_name
        assert restored.value == e.value
        assert restored.status == e.status
        assert restored.timestamp == e.timestamp


# ---------------------------------------------------------------------------
# MetricHistory
# ---------------------------------------------------------------------------

class TestMetricHistoryInit:
    def test_invalid_max_entries_raises(self, tmp_path):
        with pytest.raises(ValueError, match="max_entries"):
            MetricHistory(str(tmp_path / "h.json"), max_entries=0)

    def test_empty_on_new_file(self, tmp_path):
        h = MetricHistory(str(tmp_path / "h.json"))
        assert h.get() == []

    def test_loads_existing_file(self, tmp_path):
        path = str(tmp_path / "h.json")
        entry = HistoryEntry(metric_name="x", value=1.0, status="ok", source="src")
        with open(path, "w") as fh:
            json.dump([entry.to_dict()], fh)
        h = MetricHistory(path)
        assert len(h.get()) == 1
        assert h.get()[0].metric_name == "x"


class TestMetricHistoryRecord:
    def test_record_appends(self, tmp_path):
        h = MetricHistory(str(tmp_path / "h.json"))
        m = _make_metric("cpu", 55.0, MetricStatus.OK)
        h.record(m)
        entries = h.get()
        assert len(entries) == 1
        assert entries[0].metric_name == "cpu"
        assert entries[0].value == 55.0
        assert entries[0].status == "ok"

    def test_max_entries_respected(self, tmp_path):
        h = MetricHistory(str(tmp_path / "h.json"), max_entries=3)
        for i in range(5):
            h.record(_make_metric(f"m{i}", float(i), MetricStatus.OK))
        assert len(h.get()) == 3
        # oldest entries dropped
        assert h.get()[0].metric_name == "m2"

    def test_filter_by_name(self, tmp_path):
        h = MetricHistory(str(tmp_path / "h.json"))
        h.record(_make_metric("cpu", 10.0, MetricStatus.OK))
        h.record(_make_metric("mem", 20.0, MetricStatus.WARNING))
        h.record(_make_metric("cpu", 30.0, MetricStatus.CRITICAL))
        cpu_entries = h.get("cpu")
        assert len(cpu_entries) == 2
        assert all(e.metric_name == "cpu" for e in cpu_entries)


class TestMetricHistorySave:
    def test_save_and_reload(self, tmp_path):
        path = str(tmp_path / "h.json")
        h = MetricHistory(path)
        h.record(_make_metric("disk", 80.0, MetricStatus.WARNING, source="file"))
        h.save()
        assert os.path.exists(path)
        h2 = MetricHistory(path)
        assert len(h2.get()) == 1
        assert h2.get()[0].source == "file"

    def test_save_produces_valid_json(self, tmp_path):
        path = str(tmp_path / "h.json")
        h = MetricHistory(path)
        h.record(_make_metric("net", 5.0, MetricStatus.OK))
        h.save()
        with open(path) as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert data[0]["metric_name"] == "net"
