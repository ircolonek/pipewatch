"""HTTP-based metric source for pipewatch."""

import time
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error
import json

from pipewatch.sources.base import BaseSource, register_source
from pipewatch.metrics.models import Metric


@register_source("http")
class HttpSource(BaseSource):
    """Fetches metrics from an HTTP endpoint returning JSON.

    Expected JSON response format:
        [
            {"name": "pipeline.lag", "value": 42.0, "tags": {"env": "prod"}},
            ...
        ]
    """

    def __init__(
        self,
        url: str,
        timeout: int = 10,
        headers: Optional[Dict[str, str]] = None,
        metric_prefix: str = "",
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.headers = headers or {}
        self.metric_prefix = metric_prefix

    @property
    def source_name(self) -> str:
        return "http"

    def fetch(self) -> List[Metric]:
        """Perform the HTTP request and parse metrics from the response."""
        req = urllib.request.Request(self.url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"HttpSource failed to reach {self.url}: {exc}") from exc

        try:
            data: List[Dict[str, Any]] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"HttpSource received invalid JSON from {self.url}: {exc}") from exc

        metrics: List[Metric] = []
        for entry in data:
            name = self.metric_prefix + entry["name"]
            value = float(entry["value"])
            tags: Dict[str, str] = entry.get("tags", {})
            metrics.append(Metric(name=name, value=value, tags=tags, timestamp=time.time()))

        return metrics
