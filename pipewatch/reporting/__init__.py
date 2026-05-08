"""Reporting sub-package for pipewatch.

Public re-exports for the most commonly used reporting utilities.
"""

from pipewatch.reporting.summary import SummaryReport, build_summary
from pipewatch.reporting.exporter import export_json, export_csv, export_to_file
from pipewatch.reporting.formatter import format_summary, format_alerts
from pipewatch.reporting.dashboard import render_dashboard
from pipewatch.reporting.trend import MetricTrend, TrendPoint
from pipewatch.reporting.notifier import AlertNotifier
from pipewatch.reporting.history import MetricHistory, HistoryEntry
from pipewatch.reporting.aggregator import AggregatedStats, aggregate_metrics
from pipewatch.reporting.comparator import MetricDiff, compare_metrics
from pipewatch.reporting.baseline import BaselineReport, BaselineEntry
from pipewatch.reporting.anomaly import AnomalyResult, detect_anomalies
from pipewatch.reporting.correlation import CorrelationResult, correlate_metrics
from pipewatch.reporting.forecast import MetricForecast, ForecastPoint
from pipewatch.reporting.ranking import RankedMetric, rank_metrics
from pipewatch.reporting.tagging import TaggedMetric, tag_metrics
from pipewatch.reporting.heatmap import MetricHeatmap, HeatmapCell
from pipewatch.reporting.digest import DigestReport, build_digest

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
    "AggregatedStats",
    "aggregate_metrics",
    "MetricDiff",
    "compare_metrics",
    "BaselineReport",
    "BaselineEntry",
    "AnomalyResult",
    "detect_anomalies",
    "CorrelationResult",
    "correlate_metrics",
    "MetricForecast",
    "ForecastPoint",
    "RankedMetric",
    "rank_metrics",
    "TaggedMetric",
    "tag_metrics",
    "MetricHeatmap",
    "HeatmapCell",
    "DigestReport",
    "build_digest",
]
