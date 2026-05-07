"""Metric tagging and tag-based filtering utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from pipewatch.metrics.models import Metric


@dataclass
class TaggedMetric:
    """A metric decorated with a set of string tags."""

    metric: Metric
    tags: Dict[str, str] = field(default_factory=dict)

    def has_tag(self, key: str, value: Optional[str] = None) -> bool:
        """Return True if the tag key exists (and optionally matches *value*)."""
        if key not in self.tags:
            return False
        if value is not None:
            return self.tags[key] == value
        return True

    def to_dict(self) -> dict:
        return {
            "metric": self.metric.to_dict(),
            "tags": dict(self.tags),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedMetric(name={self.metric.name!r}, tags={self.tags!r})"


def tag_metrics(
    metrics: Iterable[Metric],
    tags: Dict[str, str],
) -> List[TaggedMetric]:
    """Wrap every metric in *metrics* with the given *tags*."""
    return [TaggedMetric(metric=m, tags=dict(tags)) for m in metrics]


def filter_by_tag(
    tagged: Iterable[TaggedMetric],
    key: str,
    value: Optional[str] = None,
) -> List[TaggedMetric]:
    """Return only those TaggedMetrics that carry the requested tag."""
    return [tm for tm in tagged if tm.has_tag(key, value)]


def group_by_tag(
    tagged: Iterable[TaggedMetric],
    key: str,
) -> Dict[str, List[TaggedMetric]]:
    """Partition *tagged* metrics into buckets keyed by the value of *key*."""
    result: Dict[str, List[TaggedMetric]] = {}
    for tm in tagged:
        bucket = tm.tags.get(key, "")
        result.setdefault(bucket, []).append(tm)
    return result
