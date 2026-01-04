"""Paper data model."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Paper:
    """Represents a research paper."""

    paper_id: str
    title: str
    abstract: Optional[str]
    year: int
    venue: str
    authors: list[str]
    citation_count: int
    url: str
    pdf_url: str
    publication_date: Optional[str]
    keywords_matched: list[str] = field(default_factory=list)
    first_seen: str = ""

    @property
    def has_abstract(self) -> bool:
        """Check if paper has an abstract."""
        return bool(self.abstract and self.abstract.strip())

    @property
    def abstract_lower(self) -> str:
        """Get lowercase abstract for matching."""
        return self.abstract.lower() if self.abstract else ""

    @property
    def title_lower(self) -> str:
        """Get lowercase title for matching."""
        return self.title.lower()

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        """Create Paper from dictionary."""
        return cls(
            paper_id=data.get("paper_id", ""),
            title=data.get("title", ""),
            abstract=data.get("abstract"),
            year=data.get("year", 0),
            venue=data.get("venue", ""),
            authors=data.get("authors", []),
            citation_count=data.get("citation_count", 0),
            url=data.get("url", ""),
            pdf_url=data.get("pdf_url", ""),
            publication_date=data.get("publication_date"),
            keywords_matched=data.get("keywords_matched", []),
            first_seen=data.get("first_seen", ""),
        )

    def to_dict(self) -> dict:
        """Convert Paper to dictionary."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "venue": self.venue,
            "authors": self.authors,
            "citation_count": self.citation_count,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "publication_date": self.publication_date,
            "keywords_matched": self.keywords_matched,
            "first_seen": self.first_seen,
        }
