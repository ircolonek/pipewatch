"""Baseline comparison: compare current metric values against a stored baseline."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric


@dataclass
class BaselineEntry:
    metric_name: str
    expected_value: float
    tolerance: float = 0.1  # fractional tolerance, e.g. 0.1 = 10%

    def is_within_tolerance(self, actual_value: float) -> bool:
        """Return True when *actual_value* is within the allowed tolerance band."""
        if self.expected_value == 0:
            return actual_value == 0
        delta = abs(actual_value - self.expected_value) / abs(self.expected_value)
        return delta <= self.tolerance

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "expected_value": self.expected_value,
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineEntry":
        return cls(
            metric_name=data["metric_name"],
            expected_value=float(data["expected_value"]),
            tolerance=float(data.get("tolerance", 0.1)),
        )


@dataclass
class BaselineReport:
    entries: List[dict] = field(default_factory=list)

    def add(self, metric_name: str, within: bool, expected: float, actual: Optional[float]) -> None:
        self.entries.append(
            {
                "metric_name": metric_name,
                "within_tolerance": within,
                "expected_value": expected,
                "actual_value": actual,
            }
        )

    @property
    def all_pass(self) -> bool:
        return all(e["within_tolerance"] for e in self.entries)

    def to_dict(self) -> dict:
        return {"all_pass": self.all_pass, "checks": self.entries}


def load_baseline(path: str) -> Dict[str, BaselineEntry]:
    """Load baseline entries from a JSON file keyed by metric name."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {item["metric_name"]: BaselineEntry.from_dict(item) for item in raw}


def compare_to_baseline(
    metrics: List[Metric], baseline: Dict[str, BaselineEntry]
) -> BaselineReport:
    """Compare a list of *metrics* against *baseline* entries."""
    report = BaselineReport()
    for metric in metrics:
        entry = baseline.get(metric.name)
        if entry is None:
            continue
        within = entry.is_within_tolerance(metric.value) if metric.value is not None else False
        report.add(
            metric_name=metric.name,
            within=within,
            expected=entry.expected_value,
            actual=metric.value,
        )
    return report
