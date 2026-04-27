"""Tests for pipewatch.sources.base."""

import pytest
from typing import List, Dict, Any

from pipewatch.metrics.models import Metric
from pipewatch.sources.base import (
    BaseSource,
    register_source,
    get_source,
    _SOURCE_REGISTRY,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@register_source("dummy")
class DummySource(BaseSource):
    """Minimal concrete source used only in tests."""

    @property
    def source_name(self) -> str:
        return "dummy"

    def fetch(self, config: Dict[str, Any]) -> List[Metric]:
        return [
            Metric(
                name=config.get("metric_name", "test.metric"),
                value=config.get("value", 42.0),
                source=self.source_name,
            )
        ]


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestSourceRegistry:
    def test_register_and_retrieve(self):
        assert "dummy" in _SOURCE_REGISTRY
        assert _SOURCE_REGISTRY["dummy"] is DummySource

    def test_get_source_returns_instance(self):
        src = get_source("dummy")
        assert isinstance(src, DummySource)

    def test_get_source_unknown_raises(self):
        with pytest.raises(KeyError, match="unknown_source"):
            get_source("unknown_source")

    def test_error_message_lists_available_sources(self):
        with pytest.raises(KeyError) as exc_info:
            get_source("nope")
        assert "dummy" in str(exc_info.value)


# ---------------------------------------------------------------------------
# BaseSource / DummySource behaviour tests
# ---------------------------------------------------------------------------

class TestBaseSource:
    def setup_method(self):
        self.src = DummySource()

    def test_source_name(self):
        assert self.src.source_name == "dummy"

    def test_fetch_returns_metrics(self):
        metrics = self.src.fetch({})
        assert len(metrics) == 1
        assert isinstance(metrics[0], Metric)

    def test_fetch_uses_config(self):
        metrics = self.src.fetch({"metric_name": "pipeline.lag", "value": 7.5})
        m = metrics[0]
        assert m.name == "pipeline.lag"
        assert m.value == 7.5

    def test_fetch_sets_source_field(self):
        metrics = self.src.fetch({})
        assert metrics[0].source == "dummy"

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            BaseSource()  # type: ignore[abstract]
