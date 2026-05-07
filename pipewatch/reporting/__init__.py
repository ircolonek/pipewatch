"""Reporting sub-package for pipewatch."""

from pipewatch.reporting.summary import SummaryReport, build_summary
from pipewatch.reporting.exporter import export_json, export_csv, export_to_file
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.dashboard import render_dashboard
from pipewatch.reporting.trend import TrendPoint, MetricTrend
from pipewatch.reporting.notifier import AlertNotifier
from pipewatch.reporting.history import HistoryEntry, MetricHistory
from pipewatch.reporting.aggregator import AggregatedStats, aggregate_metrics
from pipewatch.reporting.comparator import MetricDiff, compare_metrics
from pipewatch.reporting.baseline import BaselineEntry, BaselineReport
from pipewatch.reporting.anomaly import AnomalyResult, detect_anomalies
from pipewatch.reporting.correlation import CorrelationResult, correlate_metrics
from pipewatch.reporting.forecast import ForecastPoint, MetricForecast, forecast_metric

__all__ = [
    "SummaryReport",
    "build_summary",
    "export_json",
    "export_csv",
    "export_to_file",
    "format_summary",
    "format_alerts",
    "render_dashboard",
    "TrendPoint",
    "MetricTrend",
    "AlertNotifier",
    "HistoryEntry",
    "MetricHistory",
    "AggregatedStats",
    "aggregate_metrics",
    "MetricDiff",
    "compare_metrics",
    "BaselineEntry",
    "BaselineReport",
    "AnomalyResult",
    "detect_anomalies",
    "CorrelationResult",
    "correlate_metrics",
    "ForecastPoint",
    "MetricForecast",
    "forecast_metric",
]
