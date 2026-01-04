"""Utility functions for I/O operations."""

import json
from datetime import datetime
from pathlib import Path

from src.models.paper import Paper


def load_papers(filepath: str | Path) -> tuple[list[Paper], dict]:
    """
    Load papers from JSON file.

    Args:
        filepath: Path to papers.json file

    Returns:
        Tuple of (list of Paper objects, metadata dict)
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    papers = [Paper.from_dict(p) for p in data.get("papers", [])]

    metadata = {
        "updated": data.get("updated"),
        "total": data.get("total", len(papers)),
        "keywords": data.get("keywords", []),
        "seed_papers": data.get("seed_papers", []),
    }

    return papers, metadata


def save_papers(
    papers: list[Paper],
    filepath: str | Path,
    metadata: dict | None = None,
    note: str | None = None,
) -> None:
    """
    Save papers to JSON file.

    Args:
        papers: List of Paper objects to save
        filepath: Path to output file
        metadata: Optional metadata to include
        note: Optional note about the data
    """
    data = {
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "total": len(papers),
    }

    # Include metadata if provided
    if metadata:
        data.update(metadata)

    # Add note if provided
    if note:
        data["note"] = note

    # Convert papers to dicts
    data["papers"] = [p.to_dict() for p in papers]

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def save_results(results: list, filepath: str | Path) -> None:
    """
    Save filtering results to JSON file.

    Args:
        results: List of PipelineResult objects
        filepath: Path to output file
    """
    data = {
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "total": len(results),
        "papers": [r.to_dict() for r in results],
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def print_sample_papers(papers: list[Paper], title: str, max_papers: int = 10) -> None:
    """
    Print a sample of papers for review.

    Args:
        papers: List of papers to display
        title: Title for the section
        max_papers: Maximum number of papers to display
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    for i, paper in enumerate(papers[:max_papers], 1):
        print(f"\n{i}. {paper.title} ({paper.year})")
        print(f"   Venue: {paper.venue}")
        print(f"   Keywords matched: {', '.join(paper.keywords_matched[:5])}")
        if hasattr(paper, "filter_reason"):
            print(f"   Reason: {paper.filter_reason}")

        if paper.has_abstract:
            # Show first sentence of abstract
            first_sentence = paper.abstract.split(".")[0][:150]
            print(f"   Abstract: {first_sentence}...")

    if len(papers) > max_papers:
        print(f"\n   ... and {len(papers) - max_papers} more")
