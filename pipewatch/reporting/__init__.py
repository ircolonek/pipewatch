"""Reporting sub-package.

This package provides tools for generating, formatting, and exporting
pipeline monitoring reports. Key capabilities include:

- Summary report generation (``SummaryReport``, ``build_summary``)
- Data export to JSON and CSV formats (``export_json``, ``export_csv``, ``export_to_file``)
- Human-readable formatting of summaries and alerts (``format_summary``, ``format_alerts``)
- Interactive dashboard rendering (``render_dashboard``)
- Metric trend tracking over time (``MetricTrend``, ``TrendPoint``)
- Alert notifications (``AlertNotifier``)
- Historical metric storage and retrieval (``MetricHistory``, ``HistoryEntry``)
"""

from pipewatch.reporting.summary import SummaryReport, build_summary
from pipewatch.reporting.exporter import export_json, export_csv, export_to_file
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.dashboard import render_dashboard
from pipewatch.reporting.trend import MetricTrend, TrendPoint
from pipewatch.reporting.notifier import AlertNotifier
from pipewatch.reporting.history import MetricHistory, HistoryEntry

__all__ = [
    "SummaryReport",
    "build_summary",
    "export_json",
    "export_csv",
    "export_to_file",
    "format_summary",
    "format_alerts",
    "render_dashboard",
    "MetricTrend",
    "TrendPoint",
    "AlertNotifier",
    "MetricHistory",
    "HistoryEntry",
]
