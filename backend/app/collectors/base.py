from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CollectedItem:
    title: str
    content: str
    source_url: str | None = None
    published_at: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base class for all source ingestion collectors."""

    @abstractmethod
    def collect(self, target_url: str) -> list[CollectedItem]:
        """Fetch and extract raw items from a target URL."""
        pass
