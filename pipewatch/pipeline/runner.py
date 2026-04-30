"""Pipeline runner: orchestrates source fetching, metric collection, and alert dispatch."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pipewatch.metrics.collector import MetricCollector
from pipewatch.alerts.dispatcher import AlertDispatcher
from pipewatch.sources.base import get_source

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for a single pipeline run."""

    name: str
    source_type: str
    source_options: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, tuple[float, float]] = field(default_factory=dict)


class PipelineRunner:
    """Coordinates fetching metrics from a source and evaluating alert rules."""

    def __init__(
        self,
        config: PipelineConfig,
        dispatcher: AlertDispatcher,
        collector: MetricCollector | None = None,
    ) -> None:
        self.config = config
        self.dispatcher = dispatcher
        self.collector = collector or MetricCollector(
            thresholds=config.thresholds
        )

    def run(self) -> list[dict[str, Any]]:
        """Fetch metrics, record them, evaluate alerts, and return fired alerts."""
        source_cls = get_source(self.config.source_type)
        if source_cls is None:
            raise ValueError(
                f"Unknown source type: {self.config.source_type!r}"
            )

        source = source_cls(**self.config.source_options)
        logger.info("[%s] fetching from %s", self.config.name, source.source_name())

        metrics = source.fetch()
        for metric in metrics:
            self.collector.record(metric)

        fired = self.dispatcher.evaluate(self.collector.get_all())
        logger.info(
            "[%s] %d metric(s) collected, %d alert(s) fired",
            self.config.name,
            len(metrics),
            len(fired),
        )
        return fired
