"""File-based metric source for pipewatch.

Reads metrics from JSON or CSV files on disk.
"""

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from pipewatch.metrics.models import Metric
from pipewatch.sources.base import BaseSource, register_source


@register_source("file")
class FileSource(BaseSource):
    """Reads metrics from a local JSON or CSV file."""

    def source_name(self) -> str:
        return "file"

    def __init__(self, path: str, format: str = "json", **kwargs):
        """
        Args:
            path: Absolute or relative path to the metric file.
            format: File format — 'json' or 'csv'.
        """
        if format not in ("json", "csv"):
            raise ValueError(f"Unsupported format '{format}'. Use 'json' or 'csv'.")
        self.path = path
        self.format = format

    def fetch(self) -> List[Metric]:
        """Read the file and return a list of Metric objects."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Metric file not found: {self.path}")

        if self.format == "json":
            return self._fetch_json()
        return self._fetch_csv()

    def _fetch_json(self) -> List[Metric]:
        with open(self.path, "r", encoding="utf-8") as fh:
            data: List[Dict[str, Any]] = json.load(fh)
        return [self._row_to_metric(row) for row in data]

    def _fetch_csv(self) -> List[Metric]:
        metrics: List[Metric] = []
        with open(self.path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                metrics.append(self._row_to_metric(row))
        return metrics

    @staticmethod
    def _row_to_metric(row: Dict[str, Any]) -> Metric:
        return Metric(
            name=str(row["name"]),
            value=float(row["value"]),
            source=str(row.get("source", "file")),
            timestamp=datetime.fromisoformat(row["timestamp"])
            if "timestamp" in row
            else datetime.utcnow(),
            tags={k: v for k, v in row.items()
                  if k not in ("name", "value", "source", "timestamp")},
        )
