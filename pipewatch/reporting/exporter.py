"""Export pipeline summary reports to various formats (JSON, CSV)."""

from __future__ import annotations

import csv
import json
import io
from typing import List

from pipewatch.reporting.summary import SummaryReport


def export_json(report: SummaryReport, indent: int = 2) -> str:
    """Serialise a SummaryReport to a JSON string."""
    return json.dumps(report.to_dict(), indent=indent, default=str)


def export_csv(report: SummaryReport) -> str:
    """Serialise the per-metric rows of a SummaryReport to CSV.

    Each row contains: name, source, status, value, threshold, timestamp.
    """
    output = io.StringIO()
    fieldnames = ["name", "source", "status", "value", "threshold", "timestamp"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for entry in report.to_dict().get("metrics", []):
        writer.writerow(
            {
                "name": entry.get("name", ""),
                "source": entry.get("source", ""),
                "status": entry.get("status", ""),
                "value": entry.get("value", ""),
                "threshold": entry.get("threshold", ""),
                "timestamp": entry.get("timestamp", ""),
            }
        )

    return output.getvalue()


def export_to_file(report: SummaryReport, path: str, fmt: str = "json") -> None:
    """Write a SummaryReport to *path* in the requested format.

    Args:
        report: The report to export.
        path:   Destination file path.
        fmt:    Either ``"json"`` (default) or ``"csv"``.

    Raises:
        ValueError: If *fmt* is not ``"json"`` or ``"csv"``.
    """
    fmt = fmt.lower()
    if fmt == "json":
        content = export_json(report)
    elif fmt == "csv":
        content = export_csv(report)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Use 'json' or 'csv'.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
