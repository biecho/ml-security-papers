"""Filter for determining paper relevance to the target domain."""

import re

from ml_security.config import get_config
from ml_security.filters.base import Confidence, FilterResult, PaperFilter
from ml_security.models.paper import Paper


class RelevanceFilter(PaperFilter):
    """Determine if paper is relevant to the target research domain."""

    def __init__(self):
        """Initialize filter with configuration."""
        self.config = get_config()

    def filter(self, paper: Paper) -> FilterResult:
        """Check if paper is relevant to the target domain."""
        # Papers without abstracts need manual review
        if not paper.has_abstract:
            return FilterResult(
                is_relevant=False,
                reason="No abstract available for verification",
                confidence=Confidence.LOW,
            )

        abstract = paper.abstract_lower
        title = paper.title_lower

        # Check for high-quality indicators (strong signals)
        if self._has_strong_indicators(abstract, title):
            return FilterResult(
                is_relevant=True,
                reason=f"Strong {self.config.domain_name.replace('_', ' ')} indicators present",
                confidence=Confidence.HIGH,
            )

        # Check for required terminology in abstract
        if not self._has_required_terms(abstract):
            return FilterResult(
                is_relevant=False,
                reason=f"No {self.config.domain_name.replace('_', ' ')} terminology in abstract",
                confidence=Confidence.MEDIUM,
            )

        # Has required terms but no strong indicators
        # Check context to ensure it's actually about the domain
        if self._verify_context(abstract):
            return FilterResult(
                is_relevant=True,
                reason=f"{self.config.domain_name.replace('_', ' ')} terminology with proper context",
                confidence=Confidence.MEDIUM,
            )

        return FilterResult(
            is_relevant=False,
            reason=f"{self.config.domain_name.replace('_', ' ')} mentioned only in passing",
            confidence=Confidence.MEDIUM,
        )

    def _has_strong_indicators(self, abstract: str, title: str) -> bool:
        """Check for strong indicators of domain-relevant research."""
        # Check for high-quality keywords
        for keyword in self.config.high_quality_keywords:
            if keyword.lower() in abstract or keyword.lower() in title:
                return True

        # Additional strong phrases (domain-specific patterns)
        strong_phrases = [
            "steal the model",
            "extract the model",
            "clone the model",
            "replicate the model",
            "query the victim model",
            "surrogate model",
        ]

        for phrase in strong_phrases:
            if phrase in abstract:
                return True

        # Check for query-based extraction pattern
        if ("query" in abstract or "api" in abstract) and ("extract" in abstract or "steal" in abstract):
            # Verify it's about models
            if "model" in abstract[: self.config.first_paragraph_length]:
                return True

        # Check for black-box extraction pattern
        if "black-box" in abstract and ("extract" in abstract or "steal" in abstract):
            if "model" in abstract[: self.config.first_paragraph_length]:
                return True

        return False

    def _has_required_terms(self, abstract: str) -> bool:
        """Check if abstract contains required domain terminology."""
        # Direct term match
        for term in self.config.required_abstract_terms:
            if term in abstract:
                return True

        # Check for compound terms (action words near "model")
        if self._has_compound_term(abstract):
            return True

        return False

    def _has_compound_term(self, abstract: str) -> bool:
        """Check for action words appearing near 'model'."""
        action_words = ["steal", "extract", "clone", "replicate", "copy"]

        for action in action_words:
            # Find all occurrences of action word
            for match in re.finditer(rf"\b{action}\w*\b", abstract):
                start = max(0, match.start() - self.config.context_window)
                end = min(len(abstract), match.end() + self.config.context_window)
                context = abstract[start:end]

                # Check if "model" appears nearby
                if "model" in context:
                    return True

        return False

    def _verify_context(self, abstract: str) -> bool:
        """
        Verify that domain is mentioned in a meaningful context,
        not just in passing.
        """
        # Phrases that indicate tangential mention
        passing_phrases = [
            f"such as {term}"
            for term in ["model stealing", "model extraction"]
        ] + [
            f"including {term}"
            for term in ["model stealing", "model extraction"]
        ] + [
            f"e.g., {term}"
            for term in ["model stealing", "model extraction"]
        ] + [
            "like model stealing",
            "or model stealing",
            "model stealing, and other",
            "model stealing among",
            "beyond model stealing",
            "unlike model stealing",
        ]

        # If mentioned only in passing, not primary focus
        for phrase in passing_phrases:
            if phrase in abstract:
                # Count total mentions
                total_mentions = self._count_total_mentions(abstract)
                if total_mentions <= 2:
                    return False

        # Check if first paragraph mentions domain
        # (indicates it's a primary topic)
        first_para = abstract[: self.config.first_paragraph_length]
        domain_terms = self.config.required_abstract_terms[:3]  # Use top 3
        if any(term in first_para for term in domain_terms):
            return True

        # Count total mentions - should be mentioned multiple times if primary topic
        total_mentions = self._count_total_mentions(abstract)
        return total_mentions >= self.config.min_term_mentions

    def _count_total_mentions(self, abstract: str) -> int:
        """Count total mentions of domain concepts."""
        return sum(abstract.count(term) for term in self.config.required_abstract_terms)
