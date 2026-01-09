#!/usr/bin/env python3
"""
Daily discovery: find new papers citing our pool.

Uses OpenAlex API (free, generous limits) as primary source.

For papers that haven't been checked recently:
1. Query OpenAlex for new citations
2. Add new citing papers to the queue
3. Update citations_checked_at timestamp

This finds newly published papers that reference known ML security papers.
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from state import PaperState

# OpenAlex API
OPENALEX_API = "https://api.openalex.org"
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "ml-security-papers@example.com")


def reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words.keys()))


def get_recent_citations_openalex(openalex_id: str, limit: int = 50, min_year: int = None) -> list[dict]:
    """Get recent papers that cite this paper using OpenAlex."""
    work_id = openalex_id.split("/")[-1] if "/" in openalex_id else openalex_id

    # Filter for recent papers if min_year specified
    year_filter = f",publication_year:>{min_year - 1}" if min_year else ""
    url = f"{OPENALEX_API}/works?filter=cites:{work_id}{year_filter}&per_page={limit}&sort=publication_year:desc&mailto={OPENALEX_EMAIL}"

    headers = {"User-Agent": f"ml-security-papers/1.0 (mailto:{OPENALEX_EMAIL})"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            results = []
            for work in data.get("results", []):
                results.append({
                    "openalex_id": work.get("id"),
                    "title": work.get("title"),
                    "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
                    "year": work.get("publication_year"),
                    "venue": (work.get("primary_location") or {}).get("source", {}).get("display_name") if (work.get("primary_location") or {}).get("source") else None,
                    "authors": [a.get("author", {}).get("display_name") for a in work.get("authorships", [])],
                    "doi": work.get("doi"),
                    "url": work.get("id"),
                })
            return results
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise
        print(f"  HTTP Error {e.code}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)

    return []


def search_openalex_by_title(title: str) -> dict | None:
    """Search OpenAlex by title to get work ID."""
    import urllib.parse
    query = urllib.parse.quote(title)
    url = f"{OPENALEX_API}/works?search={query}&per_page=1&mailto={OPENALEX_EMAIL}"

    headers = {"User-Agent": f"ml-security-papers/1.0 (mailto:{OPENALEX_EMAIL})"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            if data.get("results"):
                return data["results"][0]
    except Exception as e:
        print(f"  OpenAlex search error: {e}", flush=True)
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Discover new papers citing our pool")
    parser.add_argument("--state-file", type=Path, default=Path("data/paper_state.json"))
    parser.add_argument("--days", type=int, default=7, help="Check papers not checked in N days")
    parser.add_argument("--limit", type=int, default=0, help="Limit papers to check (0=all)")
    parser.add_argument("--rate-limit", type=float, default=0.2, help="Seconds between requests")
    parser.add_argument("--min-year", type=int, default=None, help="Only find citations from this year or later")
    args = parser.parse_args()

    # Default to current year - 1 for finding recent papers
    if args.min_year is None:
        args.min_year = datetime.now().year - 1

    state = PaperState(args.state_file)

    # Get papers that need citation checking
    to_check = state.get_papers_for_discovery(days_since_check=args.days)

    print(f"Papers to check for new citations: {len(to_check)}", flush=True)
    print(f"Looking for citations from {args.min_year}+", flush=True)

    if args.limit > 0:
        to_check = to_check[:args.limit]
        print(f"Limited to {len(to_check)} papers", flush=True)

    if not to_check:
        print("No papers to check", flush=True)
        return

    total_new_papers = 0
    checked_count = 0

    for i, paper in enumerate(to_check):
        paper_id = paper["paper_id"]
        title = paper["title"]

        # Get OpenAlex ID
        openalex_id = paper.get("openalex_id")

        # If no OpenAlex ID, try to find it
        if not openalex_id:
            work = search_openalex_by_title(title)
            if work:
                openalex_id = work.get("id")
                state.papers[paper_id]["openalex_id"] = openalex_id
            time.sleep(args.rate_limit)

        if not openalex_id:
            continue

        try:
            citations = get_recent_citations_openalex(openalex_id, min_year=args.min_year)

            new_papers = 0
            for citing in citations:
                if not citing or not citing.get("openalex_id"):
                    continue

                citing_id = citing["openalex_id"].split("/")[-1]

                # Check if this is a new paper
                if not state.has_paper(citing_id):
                    was_added = state.add_paper(
                        paper_id=citing_id,
                        title=citing.get("title", "Unknown"),
                        source="citation",
                        source_paper_id=paper_id,
                        abstract=citing.get("abstract"),
                        year=citing.get("year"),
                        venue=citing.get("venue"),
                        authors=citing.get("authors", []),
                        url=citing.get("url"),
                        depth=paper.get("depth", 0) + 1,
                    )
                    if was_added:
                        state.papers[citing_id]["openalex_id"] = citing.get("openalex_id")
                        if citing.get("doi"):
                            state.papers[citing_id]["doi"] = citing.get("doi")
                        new_papers += 1

            # Update checked timestamp
            state.set_citations_checked(paper_id)
            checked_count += 1
            total_new_papers += new_papers

            if new_papers > 0:
                print(f"[{i+1}/{len(to_check)}] +{new_papers} new: {title[:40]}...", flush=True)
            elif (i + 1) % 20 == 0:
                print(f"[{i+1}/{len(to_check)}] checked: {title[:40]}...", flush=True)

            # Save checkpoint
            if (i + 1) % 25 == 0:
                state.save()
                print(f"  Checkpoint saved", flush=True)

            time.sleep(args.rate_limit)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited, waiting 60s...", flush=True)
                time.sleep(60)
                continue
            else:
                print(f"Error: {e}", flush=True)

    # Final save
    state.save()

    print(f"\nDone!", flush=True)
    print(f"  Papers checked: {checked_count}", flush=True)
    print(f"  New papers discovered: {total_new_papers}", flush=True)

    stats = state.stats()
    print(f"\nCurrent state:", flush=True)
    print(f"  Total papers: {stats['total_papers']}", flush=True)
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}", flush=True)


if __name__ == "__main__":
    main()
