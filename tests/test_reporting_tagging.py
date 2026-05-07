"""Tests for pipewatch.reporting.tagging."""
import pytest

from pipewatch.metrics.models import Metric, MetricStatus
from pipewatch.reporting.tagging import (
    TaggedMetric,
    filter_by_tag,
    group_by_tag,
    tag_metrics,
)


def _make_metric(name: str, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, source="test")


# ---------------------------------------------------------------------------
# TaggedMetric
# ---------------------------------------------------------------------------
class TestTaggedMetric:
    def test_has_tag_key_only(self):
        tm = TaggedMetric(metric=_make_metric("m"), tags={"env": "prod"})
        assert tm.has_tag("env") is True

    def test_has_tag_key_and_value_match(self):
        tm = TaggedMetric(metric=_make_metric("m"), tags={"env": "prod"})
        assert tm.has_tag("env", "prod") is True

    def test_has_tag_key_and_value_mismatch(self):
        tm = TaggedMetric(metric=_make_metric("m"), tags={"env": "prod"})
        assert tm.has_tag("env", "staging") is False

    def test_has_tag_missing_key(self):
        tm = TaggedMetric(metric=_make_metric("m"), tags={})
        assert tm.has_tag("env") is False

    def test_to_dict_contains_metric_and_tags(self):
        m = _make_metric("latency", 42.0)
        tm = TaggedMetric(metric=m, tags={"region": "us-east"})
        d = tm.to_dict()
        assert d["tags"] == {"region": "us-east"}
        assert d["metric"]["name"] == "latency"

    def test_to_dict_tags_are_copy(self):
        tags = {"env": "prod"}
        tm = TaggedMetric(metric=_make_metric("m"), tags=tags)
        tm.to_dict()["tags"]["env"] = "staging"
        assert tags["env"] == "prod"


# ---------------------------------------------------------------------------
# tag_metrics
# ---------------------------------------------------------------------------
class TestTagMetrics:
    def test_returns_tagged_metric_for_each_input(self):
        metrics = [_make_metric(f"m{i}") for i in range(3)]
        result = tag_metrics(metrics, {"env": "dev"})
        assert len(result) == 3
        assert all(isinstance(r, TaggedMetric) for r in result)

    def test_tags_applied_to_all(self):
        metrics = [_make_metric("a"), _make_metric("b")]
        result = tag_metrics(metrics, {"team": "data"})
        assert all(r.tags == {"team": "data"} for r in result)

    def test_tags_are_independent_copies(self):
        original_tags = {"env": "prod"}
        metrics = [_make_metric("x"), _make_metric("y")]
        result = tag_metrics(metrics, original_tags)
        result[0].tags["env"] = "staging"
        assert result[1].tags["env"] == "prod"

    def test_empty_input(self):
        assert tag_metrics([], {"env": "prod"}) == []


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------
class TestFilterByTag:
    def _sample(self):
        return [
            TaggedMetric(_make_metric("a"), {"env": "prod", "team": "data"}),
            TaggedMetric(_make_metric("b"), {"env": "staging"}),
            TaggedMetric(_make_metric("c"), {"team": "data"}),
        ]

    def test_filter_key_only(self):
        result = filter_by_tag(self._sample(), "team")
        assert {r.metric.name for r in result} == {"a", "c"}

    def test_filter_key_and_value(self):
        result = filter_by_tag(self._sample(), "env", "prod")
        assert len(result) == 1
        assert result[0].metric.name == "a"

    def test_filter_no_match(self):
        result = filter_by_tag(self._sample(), "region")
        assert result == []


# ---------------------------------------------------------------------------
# group_by_tag
# ---------------------------------------------------------------------------
class TestGroupByTag:
    def test_groups_correctly(self):
        tagged = [
            TaggedMetric(_make_metric("a"), {"env": "prod"}),
            TaggedMetric(_make_metric("b"), {"env": "staging"}),
            TaggedMetric(_make_metric("c"), {"env": "prod"}),
        ]
        groups = group_by_tag(tagged, "env")
        assert set(groups.keys()) == {"prod", "staging"}
        assert len(groups["prod"]) == 2
        assert len(groups["staging"]) == 1

    def test_missing_key_goes_to_empty_string_bucket(self):
        tagged = [
            TaggedMetric(_make_metric("a"), {}),
            TaggedMetric(_make_metric("b"), {"env": "prod"}),
        ]
        groups = group_by_tag(tagged, "env")
        assert "" in groups
        assert len(groups[""] ) == 1

    def test_empty_input(self):
        assert group_by_tag([], "env") == {}
