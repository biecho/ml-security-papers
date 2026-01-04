"""Filters to exclude false positives."""

import re

from src.config import get_config
from src.filters.base import Confidence, FilterResult, PaperFilter
from src.models.paper import Paper


class ExclusionFilter(PaperFilter):
    """Filter out papers that are clearly not about the target domain."""

    def __init__(self):
        """Initialize filter with configuration."""
        self.config = get_config()

    def filter(self, paper: Paper) -> FilterResult:
        """Check if paper should be excluded."""
        # Check for problematic keywords (electromagnetic, side-channel, etc.)
        if result := self._check_problematic_keywords(paper):
            return result

        # Check for wrong type of stealing (prompt, link, data)
        if result := self._check_exclusion_signals(paper):
            return result

        # Check for citation-only mentions
        if result := self._check_citation_only(paper):
            return result

        # Paper passes exclusion filters
        return FilterResult(
            is_relevant=True, reason="No exclusion criteria matched", confidence=Confidence.HIGH
        )

    def _check_problematic_keywords(self, paper: Paper) -> FilterResult | None:
        """Check for keywords that are known false positives."""
        problematic_in_keywords = [
            kw
            for kw in self.config.problematic_keywords
            if kw in " ".join(paper.keywords_matched).lower()
        ]

        if not problematic_in_keywords:
            return None

        # If paper has problematic keyword but doesn't mention domain terms in abstract
        if not paper.has_abstract:
            return FilterResult(
                is_relevant=False,
                reason=f"Problematic keyword: {problematic_in_keywords[0]}",
                confidence=Confidence.MEDIUM,
            )

        abstract = paper.abstract_lower
        domain_terms = ["model extraction", "model stealing"]
        if not any(term in abstract for term in domain_terms):
            return FilterResult(
                is_relevant=False,
                reason=f"Problematic keyword without domain context: {problematic_in_keywords[0]}",
                confidence=Confidence.HIGH,
            )

        return None

    def _check_exclusion_signals(self, paper: Paper) -> FilterResult | None:
        """Check if paper matches exclusion signals (wrong domain)."""
        title = paper.title_lower
        abstract = paper.abstract_lower if paper.has_abstract else ""

        for signal_type, terms in self.config.exclusion_signals.items():
            # Check title for exclusion patterns
            for term in terms:
                if term in title:
                    # Verify it's not actually about the domain
                    if not paper.has_abstract or "model" not in abstract[:300]:
                        reason = signal_type.replace("_", " ").title()
                        return FilterResult(
                            is_relevant=False,
                            reason=f"{reason}, not model stealing",
                            confidence=Confidence.HIGH,
                        )

            # Check abstract for dominant exclusion patterns
            if paper.has_abstract:
                # Count occurrences of exclusion terms
                count = sum(abstract.count(term) for term in terms)
                if count > 2 and "model" not in title:
                    reason = signal_type.replace("_", " ").title()
                    return FilterResult(
                        is_relevant=False,
                        reason=f"Primarily about {reason.lower()}",
                        confidence=Confidence.MEDIUM,
                    )

        return None

    def _check_citation_only(self, paper: Paper) -> FilterResult | None:
        """Check if domain terms are only mentioned in citations."""
        # If only matched keyword is "(via citation)"
        if paper.keywords_matched == ["(via citation)"]:
            return FilterResult(
                is_relevant=False,
                reason="Only mentioned in citations",
                confidence=Confidence.HIGH,
            )

        # If matched "(via citation)" and only one other generic keyword
        if "(via citation)" in paper.keywords_matched and len(paper.keywords_matched) <= 2:
            other_keywords = [k for k in paper.keywords_matched if k != "(via citation)"]
            if other_keywords and other_keywords[0] in ["model extraction", "model stealing"]:
                # Check if these terms actually appear in abstract
                if paper.has_abstract:
                    abstract = paper.abstract_lower
                    if "model extraction" not in abstract and "model stealing" not in abstract:
                        return FilterResult(
                            is_relevant=False,
                            reason="Only mentioned in citations",
                            confidence=Confidence.HIGH,
                        )

        return None


class TopicFilter(PaperFilter):
    """Filter papers where the target domain is not the primary topic."""

    def __init__(self):
        """Initialize filter with configuration."""
        self.config = get_config()

    def filter(self, paper: Paper) -> FilterResult:
        """Check if paper's primary topic is the target domain."""
        if not paper.has_abstract:
            # Can't determine without abstract
            return FilterResult(
                is_relevant=True,
                reason="Cannot determine primary topic without abstract",
                confidence=Confidence.LOW,
            )

        abstract = paper.abstract_lower

        # Count mentions of domain terms vs other topics
        domain_count = self._count_domain_terms(abstract)
        other_topic_counts = self._count_other_topics(abstract)

        # No domain terms at all
        if domain_count == 0:
            return FilterResult(
                is_relevant=False,
                reason=f"No {self.config.domain_name.replace('_', ' ')} terminology in abstract",
                confidence=Confidence.HIGH,
            )

        # Check if another topic is dominant
        for topic, count in other_topic_counts.items():
            if self._is_topic_dominant(topic, count, domain_count, abstract):
                return FilterResult(
                    is_relevant=False,
                    reason=f"Primarily about {topic}, not {self.config.domain_name.replace('_', ' ')}",
                    confidence=Confidence.MEDIUM,
                )

        # Domain appears to be primary or significant topic
        return FilterResult(
            is_relevant=True,
            reason=f"{self.config.domain_name.replace('_', ' ')} is primary topic",
            confidence=Confidence.HIGH,
        )

    def _count_domain_terms(self, abstract: str) -> int:
        """Count occurrences of domain terminology."""
        # Use core keywords as domain terms
        return sum(abstract.count(term) for term in self.config.required_abstract_terms)

    def _count_other_topics(self, abstract: str) -> dict[str, int]:
        """Count mentions of other topics."""
        counts = {}
        for topic, terms in self.config.other_topics.items():
            count = sum(abstract.count(term) for term in terms)
            if count > 0:
                counts[topic] = count
        return counts

    def _is_topic_dominant(self, topic: str, topic_count: int, domain_count: int, abstract: str) -> bool:
        """Determine if another topic is dominant over the target domain."""
        # Watermarking with high frequency
        if topic == "watermarking" and topic_count >= self.config.watermark_dominance_threshold:
            if domain_count <= 2:
                # Exception: if explicitly about defense against domain attacks
                if "against model stealing" in abstract or "prevent model extraction" in abstract:
                    return False
                return True

        # Other topics with configured ratio
        if topic_count > domain_count * self.config.topic_dominance_ratio:
            return True

        # Membership inference (different attack type)
        if topic == "privacy" and "membership inference" in abstract:
            if topic_count > domain_count:
                return True

        return False
