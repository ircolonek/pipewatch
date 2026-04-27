"""Base class and registry for metric source adapters."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from pipewatch.metrics.models import Metric

_SOURCE_REGISTRY: Dict[str, type] = {}


def register_source(name: str):
    """Class decorator to register a source adapter by name."""
    def decorator(cls):
        _SOURCE_REGISTRY[name] = cls
        return cls
    return decorator


def get_source(name: str) -> "BaseSource":
    """Instantiate a registered source by name.

    Args:
        name: The registered source identifier.

    Returns:
        An instance of the corresponding BaseSource subclass.

    Raises:
        KeyError: If no source is registered under *name*.
    """
    if name not in _SOURCE_REGISTRY:
        raise KeyError(
            f"Unknown source '{name}'. "
            f"Available sources: {list(_SOURCE_REGISTRY.keys())}"
        )
    return _SOURCE_REGISTRY[name]()


class BaseSource(ABC):
    """Abstract base class for all metric source adapters.

    Subclasses must implement :meth:`fetch` to pull raw metric data
    and return a list of :class:`~pipewatch.metrics.models.Metric` objects.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of this source."""

    @abstractmethod
    def fetch(self, config: Dict[str, Any]) -> List[Metric]:
        """Fetch metrics from the source.

        Args:
            config: Source-specific configuration dictionary.

        Returns:
            A list of :class:`~pipewatch.metrics.models.Metric` instances.
        """

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} source='{self.source_name}'>"
