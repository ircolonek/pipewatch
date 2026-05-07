"""Tests for pipewatch.reporting.anomaly."""
import math
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.anomaly import AnomalyResult, detect_anomalies


def _make_metric(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, source="test", status=MetricStatus.OK)


# ---------------------------------------------------------------------------
# AnomalyResult
# ---------------------------------------------------------------------------

class TestAnomalyResult:
    def test_to_dict_keys(self):
        result = AnomalyResult(
            metric_name="latency",
            value=10.0,
            mean=5.0,
            stddev=2.0,
            z_score=2.5,
            is_anomaly=False,
            threshold=3.0,
        )
        d = result.to_dict()
        assert set(d.keys()) == {
            "metric_name", "value", "mean", "stddev",
            "z_score", "is_anomaly", "threshold",
        }

    def test_to_dict_values_rounded(self):
        result = AnomalyResult(
            metric_name="m", value=1.0, mean=1.123456789,
            stddev=0.123456789, z_score=1.123456789,
            is_anomaly=False, threshold=3.0,
        )
        d = result.to_dict()
        assert d["mean"] == round(1.123456789, 6)
        assert d["stddev"] == round(0.123456789, 6)
        assert d["z_score"] == round(1.123456789, 6)


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

class TestDetectAnomalies:
    def test_empty_metrics_returns_empty(self):
        assert detect_anomalies([], {}) == []

    def test_metric_without_history_skipped(self):
        m = _make_metric("cpu", 99.0)
        results = detect_anomalies([m], {})
        assert results == []

    def test_metric_with_single_history_point_skipped(self):
        m = _make_metric("cpu", 99.0)
        results = detect_anomalies([m], {"cpu": [50.0]})
        assert results == []

    def test_normal_value_not_flagged(self):
        history = {"cpu": [50.0, 52.0, 48.0, 51.0, 49.0]}
        m = _make_metric("cpu", 51.0)
        results = detect_anomalies([m], history, threshold=3.0)
        assert len(results) == 1
        assert results[0].is_anomaly is False

    def test_extreme_value_flagged(self):
        history = {"cpu": [10.0, 10.0, 10.0, 10.0, 10.0]}
        m = _make_metric("cpu", 10000.0)
        results = detect_anomalies([m], history, threshold=3.0)
        assert len(results) == 1
        assert results[0].is_anomaly is True

    def test_zero_stddev_gives_zero_z_score(self):
        history = {"cpu": [5.0, 5.0, 5.0]}
        m = _make_metric("cpu", 5.0)
        results = detect_anomalies([m], history)
        assert results[0].z_score == 0.0
        assert results[0].is_anomaly is False

    def test_multiple_metrics_only_matching_returned(self):
        history = {"cpu": [10.0, 10.0, 10.0]}
        metrics = [_make_metric("cpu", 10.0), _make_metric("mem", 80.0)]
        results = detect_anomalies(metrics, history)
        assert len(results) == 1
        assert results[0].metric_name == "cpu"

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold must be a positive number"):
            detect_anomalies([], {}, threshold=0)

    def test_z_score_computed_correctly(self):
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        mean = sum(values) / len(values)  # 5.0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = math.sqrt(variance)
        m = _make_metric("x", 9.0)
        results = detect_anomalies([m], {"x": values})
        expected_z = abs((9.0 - mean) / stddev)
        assert abs(results[0].z_score - expected_z) < 1e-9
