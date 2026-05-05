"""Human-readable text formatting for pipeline summary reports."""

from __future__ import annotations

from typing import List

from pipewatch.metrics.models import MetricStatus
from pipewatch.reporting.summary import SummaryReport

# ANSI colour codes (disabled when NO_COLOR is set or output is not a tty)
_COLOURS = {
    MetricStatus.OK: "\033[32m",       # green
    MetricStatus.WARNING: "\033[33m",  # yellow
    MetricStatus.CRITICAL: "\033[31m", # red
    MetricStatus.UNKNOWN: "\033[90m",  # dark grey
}
_RESET = "\033[0m"


def _colour(status: MetricStatus, text: str, use_colour: bool) -> str:
    if not use_colour:
        return text
    return f"{_COLOURS.get(status, '')}{text}{_RESET}"


def format_summary(report: SummaryReport, *, use_colour: bool = True) -> str:
    """Return a multi-line string representation of *report*.

    Parameters
    ----------
    report:
        A :class:`~pipewatch.reporting.summary.SummaryReport` instance.
    use_colour:
        When *True* (default) ANSI escape codes are embedded in the output.
    """
    lines: List[str] = []
    lines.append("=" * 50)
    lines.append("PipeWatch Pipeline Summary")
    lines.append(f"  Total metrics : {report.total}")
    lines.append(f"  OK            : {report.ok_count}")
    lines.append(f"  Warning       : {report.warning_count}")
    lines.append(f"  Critical      : {report.critical_count}")
    lines.append(f"  Unknown       : {report.unknown_count}")
    lines.append("-" * 50)

    if not report.metrics:
        lines.append("  (no metrics recorded)")
    else:
        for m in report.metrics:
            status_label = _colour(m.status, m.status.value.upper(), use_colour)
            value_str = f"{m.value:.4g}" if m.value is not None else "N/A"
            lines.append(f"  [{status_label}] {m.name} = {value_str}")

    lines.append("=" * 50)
    return "\n".join(lines)


def format_alerts(report: SummaryReport, *, use_colour: bool = True) -> str:
    """Return only the non-OK metrics from *report* as a compact alert digest."""
    non_ok = [
        m for m in report.metrics
        if m.status not in (MetricStatus.OK, MetricStatus.UNKNOWN)
    ]
    if not non_ok:
        return _colour(MetricStatus.OK, "All metrics are healthy.", use_colour)

    lines = ["Alert digest:"] + [
        f"  {_colour(m.status, m.status.value.upper(), use_colour)} {m.name} = {m.value:.4g}"
        for m in non_ok
    ]
    return "\n".join(lines)
