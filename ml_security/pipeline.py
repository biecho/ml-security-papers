"""Paper filtering pipeline."""

from dataclasses import dataclass
from typing import Callable

from ml_security.filters.base import Confidence, FilterResult, PaperFilter
from ml_security.filters.exclusion_filter import ExclusionFilter, TopicFilter
from ml_security.filters.relevance_filter import RelevanceFilter
from ml_security.models.paper import Paper


@dataclass
class PipelineResult:
    """Result from the filtering pipeline."""

    paper: Paper
    is_relevant: bool
    reason: str
    confidence: Confidence
    stage: str  # Which stage made the decision

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = self.paper.to_dict()
        result["filter_reason"] = self.reason
        result["filter_confidence"] = self.confidence.value
        result["filter_stage"] = self.stage
        return result


class FilterPipeline:
    """
    Pipeline for filtering papers through multiple stages.

    The pipeline runs filters in order:
    1. ExclusionFilter - Remove obvious false positives
    2. RelevanceFilter - Check for model stealing terminology
    3. TopicFilter - Ensure model stealing is primary topic
    """

    def __init__(self):
        """Initialize the pipeline with default filters."""
        self.filters: list[tuple[str, PaperFilter]] = [
            ("exclusion", ExclusionFilter()),
            ("relevance", RelevanceFilter()),
            ("topic", TopicFilter()),
        ]

    def add_filter(self, name: str, filter_fn: PaperFilter) -> None:
        """Add a custom filter to the pipeline."""
        self.filters.append((name, filter_fn))

    def process(self, paper: Paper) -> PipelineResult:
        """
        Process a paper through the filtering pipeline.

        Args:
            paper: Paper to filter

        Returns:
            PipelineResult with final decision
        """
        for stage, filter_fn in self.filters:
            result = filter_fn(paper)

            # If filter says not relevant, stop here
            if not result.is_relevant:
                return PipelineResult(
                    paper=paper,
                    is_relevant=False,
                    reason=result.reason,
                    confidence=result.confidence,
                    stage=stage,
                )

        # All filters passed - paper is relevant
        # Get confidence from the last filter
        final_result = self.filters[-1][1](paper)
        return PipelineResult(
            paper=paper,
            is_relevant=True,
            reason=final_result.reason,
            confidence=final_result.confidence,
            stage="complete",
        )

    def process_batch(
        self,
        papers: list[Paper],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[PipelineResult]:
        """
        Process multiple papers through the pipeline.

        Args:
            papers: List of papers to process
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            List of PipelineResults
        """
        results = []
        total = len(papers)

        for i, paper in enumerate(papers, 1):
            result = self.process(paper)
            results.append(result)

            if progress_callback:
                progress_callback(i, total)

        return results


class FilterStats:
    """Statistics about filtering results."""

    def __init__(self, results: list[PipelineResult]):
        """Initialize stats from filtering results."""
        self.total = len(results)
        self.relevant = sum(1 for r in results if r.is_relevant)
        self.excluded = self.total - self.relevant

        # Count by confidence
        self.relevant_high = sum(
            1 for r in results if r.is_relevant and r.confidence == Confidence.HIGH
        )
        self.relevant_medium = sum(
            1 for r in results if r.is_relevant and r.confidence == Confidence.MEDIUM
        )
        self.relevant_low = sum(
            1 for r in results if r.is_relevant and r.confidence == Confidence.LOW
        )

        self.excluded_high = sum(
            1 for r in results if not r.is_relevant and r.confidence == Confidence.HIGH
        )
        self.excluded_medium = sum(
            1 for r in results if not r.is_relevant and r.confidence == Confidence.MEDIUM
        )
        self.excluded_low = sum(
            1 for r in results if not r.is_relevant and r.confidence == Confidence.LOW
        )

        # Count by stage
        self.by_stage = {}
        for result in results:
            stage = result.stage
            self.by_stage[stage] = self.by_stage.get(stage, 0) + 1

        # Reasons for exclusion
        self.exclusion_reasons = {}
        for result in results:
            if not result.is_relevant:
                reason = result.reason
                self.exclusion_reasons[reason] = self.exclusion_reasons.get(reason, 0) + 1

    def print_summary(self) -> None:
        """Print a summary of filtering statistics."""
        print("=" * 80)
        print("FILTERING STATISTICS")
        print("=" * 80)
        print(f"\nTotal papers: {self.total}")
        print(f"\nRelevant (KEEP): {self.relevant} ({self.relevant/self.total*100:.1f}%)")
        print(f"  - High confidence: {self.relevant_high}")
        print(f"  - Medium confidence: {self.relevant_medium}")
        print(f"  - Low confidence: {self.relevant_low}")
        print(f"\nExcluded (REMOVE): {self.excluded} ({self.excluded/self.total*100:.1f}%)")
        print(f"  - High confidence: {self.excluded_high}")
        print(f"  - Medium confidence: {self.excluded_medium}")
        print(f"  - Low confidence: {self.excluded_low}")

        print("\n" + "=" * 80)
        print("TOP EXCLUSION REASONS")
        print("=" * 80)
        sorted_reasons = sorted(self.exclusion_reasons.items(), key=lambda x: x[1], reverse=True)
        for reason, count in sorted_reasons[:10]:
            print(f"{count:4d} - {reason}")

    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            "total": self.total,
            "relevant": self.relevant,
            "excluded": self.excluded,
            "relevant_by_confidence": {
                "high": self.relevant_high,
                "medium": self.relevant_medium,
                "low": self.relevant_low,
            },
            "excluded_by_confidence": {
                "high": self.excluded_high,
                "medium": self.excluded_medium,
                "low": self.excluded_low,
            },
            "by_stage": self.by_stage,
            "exclusion_reasons": self.exclusion_reasons,
        }
