"""Terminal dashboard for live pipeline health overview."""
from __future__ import annotations

import datetime
from typing import List, Optional

from pipewatch.metrics.models import MetricStatus
from pipewatch.reporting.summary import SummaryReport
from pipewatch.reporting.formatter import _colour

_STATUS_ICON = {
    MetricStatus.OK: "✔",
    MetricStatus.WARNING: "⚠",
    MetricStatus.CRITICAL: "✖",
    MetricStatus.UNKNOWN: "?",
}

_STATUS_COLOUR = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
    MetricStatus.UNKNOWN: "white",
}


def _bar(ratio: float, width: int = 20) -> str:
    """Return a simple ASCII progress bar."""
    filled = max(0, min(width, int(ratio * width)))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render_dashboard(
    report: SummaryReport,
    title: str = "PipeWatch Dashboard",
    timestamp: Optional[datetime.datetime] = None,
) -> str:
    """Render a full-width terminal dashboard string from a SummaryReport."""
    ts = (timestamp or datetime.datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: List[str] = []
    width = 60

    lines.append("=" * width)
    lines.append(f"  {title}")
    lines.append(f"  Generated : {ts}")
    lines.append("-" * width)

    total = report.total
    ok_ratio = report.ok_count / total if total else 0.0
    lines.append(
        f"  Health : {_bar(ok_ratio)}  "
        f"{report.ok_count}/{total} OK"
    )
    lines.append("-" * width)
    lines.append(f"  {'Metric':<30} {'Status':<10} {'Value'}")
    lines.append("-" * width)

    for m in report.metrics:
        icon = _STATUS_ICON.get(m.status, "?")
        colour = _STATUS_COLOUR.get(m.status, "white")
        status_str = _colour(f"{icon} {m.status.value}", colour)
        value_str = str(m.value) if m.value is not None else "—"
        lines.append(f"  {m.name:<30} {status_str:<10} {value_str}")

    lines.append("=" * width)
    return "\n".join(lines)
