"""Heatmap generation for metric status over time slots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric, MetricStatus

# Symbols used when rendering the heatmap to a string
_CELL: Dict[MetricStatus, str] = {
    MetricStatus.OK: "\u2588",       # full block  (green)
    MetricStatus.WARNING: "\u2592",  # medium shade (yellow)
    MetricStatus.CRITICAL: "\u2591", # light shade  (red)
    MetricStatus.UNKNOWN: ".",
}

_COLOUR: Dict[MetricStatus, str] = {
    MetricStatus.OK: "\033[32m",
    MetricStatus.WARNING: "\033[33m",
    MetricStatus.CRITICAL: "\033[31m",
    MetricStatus.UNKNOWN: "\033[90m",
}
RESET = "\033[0m"


@dataclass
class HeatmapCell:
    slot: int
    status: MetricStatus
    value: Optional[float]

    def to_dict(self) -> dict:
        return {
            "slot": self.slot,
            "status": self.status.value,
            "value": self.value,
        }


@dataclass
class MetricHeatmap:
    metric_name: str
    cells: List[HeatmapCell] = field(default_factory=list)

    def add(self, slot: int, metric: Metric) -> None:
        self.cells.append(HeatmapCell(slot=slot, status=metric.status, value=metric.value))

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "cells": [c.to_dict() for c in self.cells],
        }

    def render(self, colour: bool = True) -> str:
        parts: List[str] = []
        for cell in self.cells:
            symbol = _CELL.get(cell.status, ".")
            if colour:
                symbol = _COLOUR.get(cell.status, "") + symbol + RESET
            parts.append(symbol)
        return f"{self.metric_name:30s} " + "".join(parts)


def build_heatmap(slots: List[List[Metric]]) -> Dict[str, MetricHeatmap]:
    """Build per-metric heatmaps from a sequence of metric snapshots.

    Args:
        slots: Ordered list of snapshots; each snapshot is a list of Metric
               objects captured at that time slot.

    Returns:
        Mapping of metric_name -> MetricHeatmap.
    """
    heatmaps: Dict[str, MetricHeatmap] = {}
    for slot_index, snapshot in enumerate(slots):
        for metric in snapshot:
            if metric.name not in heatmaps:
                heatmaps[metric.name] = MetricHeatmap(metric_name=metric.name)
            heatmaps[metric.name].add(slot_index, metric)
    return heatmaps
