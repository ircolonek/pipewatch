"""Data models for pipeline health metrics."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """Represents a single health metric from a pipeline source."""

    source: str
    name: str
    value: float
    unit: str = ""
    status: MetricStatus = MetricStatus.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "message": self.message,
        }

    def __repr__(self) -> str:
        return (
            f"Metric(source={self.source!r}, name={self.name!r}, "
            f"value={self.value}, status={self.status.value})"
        )
