"""Tests for pipewatch.reporting.ranking."""
import pytest
from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.ranking import RankedMetric, rank_metrics, _compute_score


def _make_metric(
    name: str,
    status: MetricStatus = MetricStatus.OK,
    value: float = 1.0,
    source: str = "test",
) -> Metric:
    return Metric(name=name, value=value, status=status, source=source)


class TestComputeScore:
    def test_critical_highest_base(self):
        m = _make_metric("x", MetricStatus.CRITICAL)
        assert _compute_score(m) == 100.0

    def test_ok_zero_base(self):
        m = _make_metric("x", MetricStatus.OK)
        assert _compute_score(m) == 0.0

    def test_warning_base(self):
        m = _make_metric("x", MetricStatus.WARNING)
        assert _compute_score(m) == 50.0

    def test_deviation_adds_to_score(self):
        m = _make_metric("x", MetricStatus.OK, value=120.0)
        score = _compute_score(m, baseline=100.0)
        # deviation = |120-100|/100 * 10 = 2.0
        assert abs(score - 2.0) < 1e-9

    def test_zero_baseline_no_deviation(self):
        m = _make_metric("x", MetricStatus.OK, value=50.0)
        score = _compute_score(m, baseline=0.0)
        assert score == 0.0

    def test_none_value_no_deviation(self):
        m = Metric(name="x", value=None, status=MetricStatus.OK, source="s")
        score = _compute_score(m, baseline=100.0)
        assert score == 0.0


class TestRankMetrics:
    def test_empty_list(self):
        assert rank_metrics([]) == []

    def test_single_metric_rank_one(self):
        m = _make_metric("a", MetricStatus.OK)
        result = rank_metrics([m])
        assert len(result) == 1
        assert result[0].rank == 1

    def test_critical_ranked_first(self):
        ok = _make_metric("ok", MetricStatus.OK)
        warn = _make_metric("warn", MetricStatus.WARNING)
        crit = _make_metric("crit", MetricStatus.CRITICAL)
        result = rank_metrics([ok, warn, crit])
        assert result[0].metric.name == "crit"
        assert result[1].metric.name == "warn"
        assert result[2].metric.name == "ok"

    def test_ranks_are_sequential(self):
        metrics = [_make_metric(f"m{i}", MetricStatus.OK) for i in range(5)]
        result = rank_metrics(metrics)
        assert [r.rank for r in result] == [1, 2, 3, 4, 5]

    def test_baseline_breaks_tie(self):
        # Both OK, but m2 deviates more from its baseline
        m1 = _make_metric("m1", MetricStatus.OK, value=100.0)
        m2 = _make_metric("m2", MetricStatus.OK, value=200.0)
        result = rank_metrics([m1, m2], baselines={"m1": 100.0, "m2": 100.0})
        assert result[0].metric.name == "m2"

    def test_to_dict_has_expected_keys(self):
        m = _make_metric("pipe_lag", MetricStatus.WARNING, value=42.0)
        result = rank_metrics([m])
        d = result[0].to_dict()
        assert set(d.keys()) == {"rank", "name", "source", "status", "value", "score"}

    def test_to_dict_values(self):
        m = _make_metric("pipe_lag", MetricStatus.WARNING, value=42.0)
        result = rank_metrics([m])
        d = result[0].to_dict()
        assert d["rank"] == 1
        assert d["name"] == "pipe_lag"
        assert d["status"] == "warning"
        assert d["value"] == 42.0

    def test_repr_contains_rank_and_name(self):
        m = _make_metric("my_metric", MetricStatus.OK)
        result = rank_metrics([m])
        r = repr(result[0])
        assert "rank=1" in r
        assert "my_metric" in r

    def test_unknown_status_has_small_weight(self):
        ok = _make_metric("ok", MetricStatus.OK)
        unk = _make_metric("unk", MetricStatus.UNKNOWN)
        result = rank_metrics([ok, unk])
        assert result[0].metric.name == "unk"
        assert result[1].metric.name == "ok"
