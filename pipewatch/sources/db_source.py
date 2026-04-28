"""Database source for pipewatch — polls SQL query row counts or scalar values."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pipewatch.metrics.models import Metric
from pipewatch.sources.base import BaseSource, register_source


@register_source("db")
class DbSource(BaseSource):
    """Fetch metrics by executing a scalar SQL query via a DB-API 2.0 connection.

    Config keys
    -----------
    dsn         : str  – passed to the *connect_fn* (required)
    connect_fn  : callable – a DB-API 2.0 ``connect`` function (required when
                  used programmatically; omit in unit tests via *_conn* override)
    queries     : list[dict] – each entry must have:
                      ``name``  (str)  metric name
                      ``sql``   (str)  query returning a single numeric value
                  optional: ``warning_threshold``, ``critical_threshold``
    timeout     : float – query timeout hint passed to cursor (default 10 s)
    """

    def source_name(self) -> str:  # noqa: D102
        return "db"

    def fetch(self) -> List[Metric]:  # noqa: D102
        connect_fn = self.config.get("connect_fn")
        dsn: str = self.config.get("dsn", "")
        queries: List[Dict[str, Any]] = self.config.get("queries", [])
        timeout: float = float(self.config.get("timeout", 10))

        # Allow tests to inject a ready-made connection.
        conn = self.config.get("_conn") or connect_fn(dsn)

        metrics: List[Metric] = []
        try:
            cursor = conn.cursor()
            for entry in queries:
                name: str = entry["name"]
                sql: str = entry["sql"]
                t0 = time.monotonic()
                try:
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    elapsed = time.monotonic() - t0
                    value = float(row[0]) if row and row[0] is not None else 0.0
                    metrics.append(
                        Metric(
                            name=name,
                            value=value,
                            source=self.source_name(),
                            warning_threshold=entry.get("warning_threshold"),
                            critical_threshold=entry.get("critical_threshold"),
                            metadata={"query_time_s": round(elapsed, 4), "sql": sql},
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    metrics.append(
                        Metric(
                            name=name,
                            value=0.0,
                            source=self.source_name(),
                            metadata={"error": str(exc), "sql": sql},
                        )
                    )
        finally:
            conn.close()

        return metrics
