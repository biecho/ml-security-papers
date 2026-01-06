"""Base filter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ml_security.models.paper import Paper


class Confidence(Enum):
    """Confidence level for filtering decisions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FilterResult:
    """Result of a filter operation."""

    is_relevant: bool
    reason: str
    confidence: Confidence

    def __bool__(self) -> bool:
        """Allow using FilterResult in boolean context."""
        return self.is_relevant


class PaperFilter(ABC):
    """Base class for paper filters."""

    @abstractmethod
    def filter(self, paper: Paper) -> FilterResult:
        """
        Determine if a paper is relevant.

        Args:
            paper: The paper to filter

        Returns:
            FilterResult with decision, reason, and confidence
        """
        pass

    def __call__(self, paper: Paper) -> FilterResult:
        """Allow filter to be called directly."""
        return self.filter(paper)
