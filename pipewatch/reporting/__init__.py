"""Reporting package: summary, export, formatting, dashboard, trend, and notifier."""
from pipewatch.reporting.summary import SummaryReport, build_summary
from pipewatch.reporting.exporter import export_json, export_csv, export_to_file
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.dashboard import render_dashboard
from pipewatch.reporting.trend import MetricTrend, TrendPoint
from pipewatch.reporting.notifier import AlertNotifier

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
]
