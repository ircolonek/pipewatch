"""Tests for pipewatch.reporting.correlation."""
from __future__ import annotations

import math
from datetime import datetime

import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.correlation import (
    CorrelationResult,
    _pearson,
    correlate_metrics,
)


def _make_metric(name: str, value: float) -> Metric:
    return Metric(
        name=name,
        value=value,
        status=MetricStatus.OK,
        source="test",
        timestamp=datetime(2024, 1, 1),
    )


# ---------------------------------------------------------------------------
# _pearson unit tests
# ---------------------------------------------------------------------------

class TestPearson:
    def test_perfect_positive(self):
        r = _pearson([1, 2, 3, 4], [1, 2, 3, 4])
        assert r == pytest.approx(1.0)

    def test_perfect_negative(self):
        r = _pearson([1, 2, 3, 4], [4, 3, 2, 1])
        assert r == pytest.approx(-1.0)

    def test_no_correlation(self):
        r = _pearson([1, 2, 3, 4], [2, 2, 2, 2])
        assert r is None  # zero variance in y

    def test_too_few_points(self):
        assert _pearson([1.0], [1.0]) is None

    def test_empty(self):
        assert _pearson([], []) is None


# ---------------------------------------------------------------------------
# CorrelationResult
# ---------------------------------------------------------------------------

class TestCorrelationResult:
    def test_to_dict_keys(self):
        result = CorrelationResult("a", "b", 0.95, 10)
        d = result.to_dict()
        assert set(d) == {"metric_a", "metric_b", "coefficient", "sample_size"}

    def test_to_dict_rounds_coefficient(self):
        result = CorrelationResult("a", "b", 1 / 3, 5)
        assert result.to_dict()["coefficient"] == pytest.approx(0.333333, rel=1e-4)

    def test_to_dict_none_coefficient(self):
        result = CorrelationResult("a", "b", None, 0)
        assert result.to_dict()["coefficient"] is None


# ---------------------------------------------------------------------------
# correlate_metrics
# ---------------------------------------------------------------------------

class TestCorrelateMetrics:
    def test_perfect_positive_correlation(self):
        a = [_make_metric("cpu", float(v)) for v in [10, 20, 30, 40]]
        b = [_make_metric("mem", float(v)) for v in [10, 20, 30, 40]]
        result = correlate_metrics(a, b)
        assert result.coefficient == pytest.approx(1.0)
        assert result.sample_size == 4

    def test_negative_correlation(self):
        a = [_make_metric("cpu", float(v)) for v in [1, 2, 3, 4]]
        b = [_make_metric("mem", float(v)) for v in [4, 3, 2, 1]]
        result = correlate_metrics(a, b)
        assert result.coefficient == pytest.approx(-1.0)

    def test_empty_sequences_returns_none_coefficient(self):
        result = correlate_metrics([], [])
        assert result.coefficient is None
        assert result.sample_size == 0

    def test_shorter_sequence_limits_pairs(self):
        a = [_make_metric("x", float(v)) for v in [1, 2, 3, 4, 5]]
        b = [_make_metric("y", float(v)) for v in [1, 2, 3]]
        result = correlate_metrics(a, b)
        assert result.sample_size == 3

    def test_custom_labels_used(self):
        a = [_make_metric("x", 1.0)]
        b = [_make_metric("y", 1.0)]
        result = correlate_metrics(a, b, name_a="alpha", name_b="beta")
        assert result.metric_a == "alpha"
        assert result.metric_b == "beta"

    def test_labels_inferred_from_metrics(self):
        a = [_make_metric("cpu_usage", 1.0)]
        b = [_make_metric("mem_usage", 1.0)]
        result = correlate_metrics(a, b)
        assert result.metric_a == "cpu_usage"
        assert result.metric_b == "mem_usage"

    def test_none_values_skipped(self):
        a = [_make_metric("x", 1.0), _make_metric("x", 2.0)]
        b = [_make_metric("y", 1.0), _make_metric("y", 2.0)]
        a[0].value = None  # type: ignore[assignment]
        result = correlate_metrics(a, b)
        # Only one valid pair — cannot compute r
        assert result.coefficient is None
        assert result.sample_size == 1
