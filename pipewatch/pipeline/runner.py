"""Pipeline runner — fetches metrics from a source and records them."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.alerts.dispatcher import AlertDispatcher
from pipewatch.metrics.collector import MetricCollector
from pipewatch.reporting.history import MetricHistory
from pipewatch.sources.base import get_source


@dataclass
class PipelineConfig:
    source_name: str
    source_config: dict = field(default_factory=dict)
    alert_rules: list = field(default_factory=list)
    history_path: Optional[str] = None


class PipelineRunner:
    """Orchestrates a single pipeline run."""

    def __init__(
        self,
        config: PipelineConfig,
        collector: Optional[MetricCollector] = None,
        dispatcher: Optional[AlertDispatcher] = None,
        history: Optional[MetricHistory] = None,
    ) -> None:
        self._config = config
        self._collector = collector or MetricCollector()
        self._dispatcher = dispatcher or AlertDispatcher()
        self._history = history

        for rule in config.alert_rules:
            self._dispatcher.add_rule(rule)

    # ------------------------------------------------------------------
    def run(self) -> List:
        """Fetch metrics, record them, evaluate alerts, persist history.

        Returns the list of fired alert messages (may be empty).
        """
        source_cls = get_source(self._config.source_name)
        if source_cls is None:
            raise ValueError(f"Unknown source: {self._config.source_name!r}")

        source = source_cls(self._config.source_config)
        metrics = source.fetch()

        for metric in metrics:
            self._collector.record(metric)
            if self._history is not None:
                self._history.record(metric)

        if self._history is not None:
            self._history.save()

        alerts = self._dispatcher.evaluate(metrics)
        return alerts
