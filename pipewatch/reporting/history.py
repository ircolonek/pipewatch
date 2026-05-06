"""Persistent metric history store backed by a simple JSON file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.metrics.models import Metric


@dataclass
class HistoryEntry:
    metric_name: str
    value: float
    status: str
    source: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "status": self.status,
            "source": self.source,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            metric_name=data["metric_name"],
            value=data["value"],
            status=data["status"],
            source=data["source"],
            timestamp=data["timestamp"],
        )


class MetricHistory:
    """Append-only history store for metrics, persisted as JSON."""

    def __init__(self, path: str, max_entries: int = 1000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._path = path
        self._max_entries = max_entries
        self._entries: List[HistoryEntry] = []
        if os.path.exists(path):
            self._load()

    # ------------------------------------------------------------------
    def record(self, metric: Metric) -> None:
        """Append a new entry derived from *metric*."""
        entry = HistoryEntry(
            metric_name=metric.name,
            value=metric.value,
            status=metric.status.value,
            source=metric.source,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

    def get(self, metric_name: Optional[str] = None) -> List[HistoryEntry]:
        """Return all entries, optionally filtered by *metric_name*."""
        if metric_name is None:
            return list(self._entries)
        return [e for e in self._entries if e.metric_name == metric_name]

    def save(self) -> None:
        """Persist entries to disk."""
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump([e.to_dict() for e in self._entries], fh, indent=2)

    # ------------------------------------------------------------------
    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self._entries = [HistoryEntry.from_dict(d) for d in raw]
