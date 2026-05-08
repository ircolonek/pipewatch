"""Tests for pipewatch.reporting.heatmap."""
import pytest
from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.heatmap import (
    HeatmapCell,
    MetricHeatmap,
    build_heatmap,
)


def _make_metric(name: str, value: float, status: MetricStatus) -> Metric:
    m = Metric(name=name, value=value, source="test")
    m.status = status
    return m


# ---------------------------------------------------------------------------
# HeatmapCell
# ---------------------------------------------------------------------------

class TestHeatmapCell:
    def test_to_dict_keys(self):
        cell = HeatmapCell(slot=0, status=MetricStatus.OK, value=1.0)
        d = cell.to_dict()
        assert set(d.keys()) == {"slot", "status", "value"}

    def test_to_dict_status_is_string(self):
        cell = HeatmapCell(slot=1, status=MetricStatus.CRITICAL, value=99.0)
        assert isinstance(cell.to_dict()["status"], str)

    def test_to_dict_none_value(self):
        cell = HeatmapCell(slot=2, status=MetricStatus.UNKNOWN, value=None)
        assert cell.to_dict()["value"] is None


# ---------------------------------------------------------------------------
# MetricHeatmap
# ---------------------------------------------------------------------------

class TestMetricHeatmap:
    def test_add_increases_cell_count(self):
        hm = MetricHeatmap(metric_name="latency")
        m = _make_metric("latency", 10.0, MetricStatus.OK)
        hm.add(0, m)
        assert len(hm.cells) == 1

    def test_to_dict_structure(self):
        hm = MetricHeatmap(metric_name="latency")
        hm.add(0, _make_metric("latency", 5.0, MetricStatus.WARNING))
        d = hm.to_dict()
        assert d["metric_name"] == "latency"
        assert len(d["cells"]) == 1

    def test_render_contains_metric_name(self):
        hm = MetricHeatmap(metric_name="cpu_usage")
        hm.add(0, _make_metric("cpu_usage", 80.0, MetricStatus.CRITICAL))
        rendered = hm.render(colour=False)
        assert "cpu_usage" in rendered

    def test_render_no_colour(self):
        hm = MetricHeatmap(metric_name="mem")
        hm.add(0, _make_metric("mem", 1.0, MetricStatus.OK))
        rendered = hm.render(colour=False)
        assert "\033[" not in rendered

    def test_render_with_colour(self):
        hm = MetricHeatmap(metric_name="mem")
        hm.add(0, _make_metric("mem", 1.0, MetricStatus.OK))
        rendered = hm.render(colour=True)
        assert "\033[" in rendered

    def test_render_length_matches_slots(self):
        hm = MetricHeatmap(metric_name="x")
        for i in range(5):
            hm.add(i, _make_metric("x", float(i), MetricStatus.OK))
        # strip ANSI and leading name portion; each slot = 1 char
        import re
        plain = re.sub(r"\033\[[0-9;]*m", "", hm.render(colour=True)).strip()
        # name is padded to 30 chars; remaining chars = number of slots
        assert len(plain) - 30 == 5


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

class TestBuildHeatmap:
    def test_empty_slots(self):
        result = build_heatmap([])
        assert result == {}

    def test_single_slot_single_metric(self):
        m = _make_metric("latency", 42.0, MetricStatus.OK)
        result = build_heatmap([[m]])
        assert "latency" in result
        assert len(result["latency"].cells) == 1

    def test_multiple_slots_same_metric(self):
        snapshots = [
            [_make_metric("latency", float(i), MetricStatus.OK)]
            for i in range(4)
        ]
        result = build_heatmap(snapshots)
        assert len(result["latency"].cells) == 4

    def test_multiple_metrics_isolated(self):
        snap = [
            _make_metric("a", 1.0, MetricStatus.OK),
            _make_metric("b", 2.0, MetricStatus.WARNING),
        ]
        result = build_heatmap([snap])
        assert "a" in result and "b" in result
        assert len(result["a"].cells) == 1
        assert len(result["b"].cells) == 1

    def test_slot_index_stored_correctly(self):
        snapshots = [
            [_make_metric("x", 0.0, MetricStatus.OK)],
            [_make_metric("x", 1.0, MetricStatus.WARNING)],
        ]
        result = build_heatmap(snapshots)
        assert result["x"].cells[0].slot == 0
        assert result["x"].cells[1].slot == 1

    def test_status_preserved(self):
        snap = [_make_metric("y", 99.0, MetricStatus.CRITICAL)]
        result = build_heatmap([snap])
        assert result["y"].cells[0].status == MetricStatus.CRITICAL
