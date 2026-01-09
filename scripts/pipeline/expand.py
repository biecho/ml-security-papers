#!/usr/bin/env python3
"""
Expand the paper graph via citations and references.

Uses OpenAlex API (free, generous limits) as primary source.
Falls back to Semantic Scholar if needed.

For each classified paper (ML01-ML10):
1. Fetch papers that cite it (citations)
2. Fetch papers it references (references)
3. Add new papers to the queue with status="pending" or "fetched"
4. Mark original paper as "expanded"

This implements BFS-style graph traversal.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from state import PaperState

# OpenAlex API (primary)
OPENALEX_API = "https://api.openalex.org"
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "ml-security-papers@example.com")

# Semantic Scholar API (fallback)
S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
S2_API_KEY = os.environ.get("S2_API_KEY")
PAPER_FIELDS = "paperId,title,abstract,year,venue,authors,url"


def reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words.keys()))


def get_openalex_id_from_paper(paper: dict) -> str | None:
    """Get OpenAlex ID from paper state."""
    # Direct OpenAlex ID
    if paper.get("openalex_id"):
        return paper["openalex_id"]
    # Try DOI
    if paper.get("doi"):
        return f"https://doi.org/{paper['doi'].replace('https://doi.org/', '')}"
    return None


def search_openalex_by_title(title: str) -> dict | None:
    """Search OpenAlex by title to get work ID."""
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


def get_citations_openalex(openalex_id: str, limit: int = 100) -> list[dict]:
    """Get papers that cite this paper using OpenAlex."""
    # OpenAlex uses the cites filter
    work_id = openalex_id.split("/")[-1] if "/" in openalex_id else openalex_id
    url = f"{OPENALEX_API}/works?filter=cites:{work_id}&per_page={limit}&mailto={OPENALEX_EMAIL}"

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
        print(f"  OpenAlex citations HTTP Error {e.code}", flush=True)
    except Exception as e:
        print(f"  OpenAlex citations Error: {e}", flush=True)

    return []


def get_references_openalex(openalex_id: str, limit: int = 50) -> list[dict]:
    """Get papers that this paper references using OpenAlex."""
    # Get the work first to access referenced_works
    work_id = openalex_id.split("/")[-1] if "/" in openalex_id else openalex_id
    url = f"{OPENALEX_API}/works/{work_id}?mailto={OPENALEX_EMAIL}"

    headers = {"User-Agent": f"ml-security-papers/1.0 (mailto:{OPENALEX_EMAIL})"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            referenced_works = data.get("referenced_works", [])[:limit]

            if not referenced_works:
                return []

            # Fetch details for referenced works
            # OpenAlex allows filtering by ID
            ids_filter = "|".join(w.split("/")[-1] for w in referenced_works)
            refs_url = f"{OPENALEX_API}/works?filter=openalex_id:{ids_filter}&per_page={limit}&mailto={OPENALEX_EMAIL}"

            req2 = urllib.request.Request(refs_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=30) as response2:
                refs_data = json.loads(response2.read().decode())
                results = []
                for work in refs_data.get("results", []):
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
        print(f"  OpenAlex refs HTTP Error {e.code}", flush=True)
    except Exception as e:
        print(f"  OpenAlex refs Error: {e}", flush=True)

    return []


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Expand paper graph via citations")
    parser.add_argument("--state-file", type=Path, default=Path("data/paper_state.json"))
    parser.add_argument("--limit", type=int, default=0, help="Limit papers to expand (0=all)")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth from seed papers")
    parser.add_argument("--max-citations", type=int, default=100, help="Max citations per paper")
    parser.add_argument("--max-references", type=int, default=50, help="Max references per paper")
    parser.add_argument("--rate-limit", type=float, default=0.2, help="Seconds between requests")
    args = parser.parse_args()

    state = PaperState(args.state_file)

    # Get papers to expand (classified but not yet expanded)
    to_expand = state.get_papers_to_expand()

    # Filter by depth
    to_expand = [p for p in to_expand if p.get("depth", 0) < args.max_depth]

    print(f"Papers to expand: {len(to_expand)}", flush=True)

    if args.limit > 0:
        to_expand = to_expand[:args.limit]
        print(f"Limited to {len(to_expand)} papers", flush=True)

    if not to_expand:
        print("No papers to expand", flush=True)
        return

    total_citations_added = 0
    total_references_added = 0
    expanded_count = 0

    for i, paper in enumerate(to_expand):
        paper_id = paper["paper_id"]
        title = paper["title"]
        depth = paper.get("depth", 0)

        # Get OpenAlex ID
        openalex_id = get_openalex_id_from_paper(paper)

        # If no OpenAlex ID, try to find it by title
        if not openalex_id:
            work = search_openalex_by_title(title)
            if work:
                openalex_id = work.get("id")
                state.papers[paper_id]["openalex_id"] = openalex_id
            time.sleep(args.rate_limit)

        if not openalex_id:
            print(f"[{i+1}/{len(to_expand)}] ⊘ No OpenAlex ID: {title[:40]}...", flush=True)
            continue

        try:
            # Fetch citations
            citations = get_citations_openalex(openalex_id, args.max_citations)
            time.sleep(args.rate_limit)

            # Fetch references
            references = get_references_openalex(openalex_id, args.max_references)
            time.sleep(args.rate_limit)

            citations_added = 0
            references_added = 0

            # Add citing papers
            for citing in citations:
                if not citing or not citing.get("openalex_id"):
                    continue

                # Use OpenAlex ID as paper_id
                citing_id = citing["openalex_id"].split("/")[-1]

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
                    depth=depth + 1,
                )
                if was_added:
                    state.papers[citing_id]["openalex_id"] = citing.get("openalex_id")
                    if citing.get("doi"):
                        state.papers[citing_id]["doi"] = citing.get("doi")
                    citations_added += 1

            # Add referenced papers
            for ref in references:
                if not ref or not ref.get("openalex_id"):
                    continue

                ref_id = ref["openalex_id"].split("/")[-1]

                was_added = state.add_paper(
                    paper_id=ref_id,
                    title=ref.get("title", "Unknown"),
                    source="reference",
                    source_paper_id=paper_id,
                    abstract=ref.get("abstract"),
                    year=ref.get("year"),
                    venue=ref.get("venue"),
                    authors=ref.get("authors", []),
                    url=ref.get("url"),
                    depth=depth + 1,
                )
                if was_added:
                    state.papers[ref_id]["openalex_id"] = ref.get("openalex_id")
                    if ref.get("doi"):
                        state.papers[ref_id]["doi"] = ref.get("doi")
                    references_added += 1

            # Mark as expanded
            state.set_expanded(paper_id)
            expanded_count += 1

            total_citations_added += citations_added
            total_references_added += references_added

            if (i + 1) % 5 == 0 or i == 0:
                print(f"[{i+1}/{len(to_expand)}] ✓ +{citations_added} cit, +{references_added} ref: {title[:35]}...", flush=True)

            # Save checkpoint
            if (i + 1) % 10 == 0:
                state.save()
                print(f"  Checkpoint saved", flush=True)

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
    print(f"  Papers expanded: {expanded_count}", flush=True)
    print(f"  Citations added: {total_citations_added}", flush=True)
    print(f"  References added: {total_references_added}", flush=True)

    stats = state.stats()
    print(f"\nCurrent state:", flush=True)
    print(f"  Total papers: {stats['total_papers']}", flush=True)
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}", flush=True)


if __name__ == "__main__":
    main()
