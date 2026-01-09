#!/usr/bin/env python3
"""
Fetch metadata for papers that are in "pending" status.

Sources (in order of preference):
1. OpenAlex API (free, generous limits)
2. arXiv API (if URL contains arxiv.org)
3. Semantic Scholar API (fallback, rate-limited)

Updates paper status to "fetched" when successful.
"""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from state import PaperState

# OpenAlex API (free, generous limits with polite pool)
OPENALEX_API = "https://api.openalex.org"
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "ml-security-papers@example.com")

# Semantic Scholar API (fallback)
S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
S2_API_KEY = os.environ.get("S2_API_KEY")
S2_FIELDS = "paperId,title,abstract,year,venue,authors,citationCount,url,externalIds"

# arXiv API
ARXIV_API = "http://export.arxiv.org/api/query"


def reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words.keys()))


def search_openalex(title: str) -> dict | None:
    """Search for a paper by title in OpenAlex."""
    query = urllib.parse.quote(title)
    url = f"{OPENALEX_API}/works?search={query}&per_page=1&mailto={OPENALEX_EMAIL}"

    headers = {"User-Agent": f"ml-security-papers/1.0 (mailto:{OPENALEX_EMAIL})"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            if data.get("results"):
                work = data["results"][0]
                # Get PDF URL from open access or primary location
                pdf_url = None
                if work.get("open_access", {}).get("oa_url"):
                    pdf_url = work["open_access"]["oa_url"]
                elif work.get("primary_location", {}).get("pdf_url"):
                    pdf_url = work["primary_location"]["pdf_url"]

                return {
                    "openalex_id": work.get("id"),
                    "title": work.get("title"),
                    "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
                    "year": work.get("publication_year"),
                    "venue": (work.get("primary_location") or {}).get("source", {}).get("display_name") if (work.get("primary_location") or {}).get("source") else None,
                    "authors": [a.get("author", {}).get("display_name") for a in work.get("authorships", [])],
                    "cited_by_count": work.get("cited_by_count"),
                    "doi": work.get("doi"),
                    "url": work.get("id"),  # OpenAlex URL
                    "pdf_url": pdf_url,
                }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise
        print(f"  OpenAlex HTTP Error {e.code}", flush=True)
    except Exception as e:
        print(f"  OpenAlex Error: {e}", flush=True)

    return None


def extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv ID from URL."""
    if not url:
        return None
    patterns = [
        r'arxiv.org/(?:abs|pdf)/(\d+\.\d+)',
        r'arxiv.org/(?:abs|pdf)/([a-z-]+/\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_arxiv(arxiv_id: str) -> dict | None:
    """Fetch metadata from arXiv API."""
    url = f"{ARXIV_API}?id_list={arxiv_id}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ml-security-papers/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read().decode()

        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        entry = root.find('atom:entry', ns)
        if entry is None:
            return None

        title_el = entry.find('atom:title', ns)
        if title_el is not None and 'Error' in (title_el.text or ''):
            return None

        return {
            'arxiv_id': arxiv_id,
            'title': title_el.text.strip().replace('\n', ' ') if title_el is not None else None,
            'abstract': entry.find('atom:summary', ns).text.strip().replace('\n', ' ') if entry.find('atom:summary', ns) is not None else None,
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'published': entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else None,
            'url': f"https://arxiv.org/abs/{arxiv_id}",
        }
    except Exception as e:
        print(f"  arXiv Error: {e}", flush=True)
        return None


def search_semantic_scholar(title: str) -> dict | None:
    """Search for a paper by title in Semantic Scholar (fallback)."""
    query = urllib.parse.quote(title)
    url = f"{S2_API_BASE}/paper/search?query={query}&fields={S2_FIELDS}&limit=1"

    headers = {"User-Agent": "ml-security-papers/1.0"}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            if data.get("data"):
                result = data["data"][0]
                return {
                    "s2_paper_id": result.get("paperId"),
                    "title": result.get("title"),
                    "abstract": result.get("abstract"),
                    "year": result.get("year"),
                    "venue": result.get("venue"),
                    "authors": [a.get("name") for a in result.get("authors", [])],
                    "cited_by_count": result.get("citationCount"),
                    "url": result.get("url"),
                    "external_ids": result.get("externalIds", {}),
                }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise
        print(f"  S2 HTTP Error {e.code}", flush=True)
    except Exception as e:
        print(f"  S2 Error: {e}", flush=True)

    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch metadata for pending papers")
    parser.add_argument("--state-file", type=Path, default=Path("data/paper_state.json"))
    parser.add_argument("--limit", type=int, default=0, help="Limit papers to fetch (0=all)")
    parser.add_argument("--rate-limit", type=float, default=0.2, help="Seconds between requests (OpenAlex is fast)")
    parser.add_argument("--source", type=str, default="openalex", choices=["openalex", "s2", "arxiv"],
                       help="Primary source for metadata")
    args = parser.parse_args()

    state = PaperState(args.state_file)

    # Get pending papers
    pending = state.get_pending_papers()
    print(f"Papers pending metadata: {len(pending)}", flush=True)
    print(f"Using source: {args.source}", flush=True)

    if args.limit > 0:
        pending = pending[:args.limit]
        print(f"Limited to {len(pending)} papers", flush=True)

    if not pending:
        print("No papers to fetch", flush=True)
        return

    fetched = 0
    failed = 0

    for i, paper in enumerate(pending):
        paper_id = paper["paper_id"]
        title = paper["title"]

        try:
            result = None

            # Try arXiv first if URL contains arxiv
            arxiv_id = extract_arxiv_id(paper.get("url"))
            if arxiv_id:
                result = fetch_arxiv(arxiv_id)
                if result and result.get("abstract"):
                    state.set_fetched(
                        paper_id,
                        abstract=result.get("abstract"),
                        authors=result.get("authors"),
                        year=int(result["published"][:4]) if result.get("published") else paper.get("year"),
                        url=result.get("url"),
                    )
                    state.papers[paper_id]["arxiv_id"] = arxiv_id

            # Try OpenAlex (primary source)
            if not result or not result.get("abstract"):
                result = search_openalex(title)
                if result and result.get("abstract"):
                    state.set_fetched(
                        paper_id,
                        abstract=result.get("abstract"),
                        authors=result.get("authors"),
                        year=result.get("year"),
                        venue=result.get("venue"),
                        url=result.get("url"),
                        cited_by_count=result.get("cited_by_count"),
                        pdf_url=result.get("pdf_url"),
                    )
                    state.papers[paper_id]["openalex_id"] = result.get("openalex_id")
                    if result.get("doi"):
                        state.papers[paper_id]["doi"] = result.get("doi")

            # Fall back to Semantic Scholar if still no abstract
            if (not result or not result.get("abstract")) and args.source != "openalex":
                result = search_semantic_scholar(title)
                if result and result.get("abstract"):
                    state.set_fetched(
                        paper_id,
                        abstract=result.get("abstract"),
                        authors=result.get("authors"),
                        year=result.get("year"),
                        venue=result.get("venue"),
                        url=result.get("url"),
                    )
                    state.papers[paper_id]["s2_paper_id"] = result.get("s2_paper_id")
                    state.papers[paper_id]["external_ids"] = result.get("external_ids", {})

            if result and result.get("abstract"):
                fetched += 1
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"[{i+1}/{len(pending)}] ✓ {title[:50]}...", flush=True)
            else:
                failed += 1
                if (i + 1) % 20 == 0:
                    print(f"[{i+1}/{len(pending)}] ✗ No abstract: {title[:40]}...", flush=True)

            # Save checkpoint
            if (i + 1) % 50 == 0:
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
                failed += 1

    # Final save
    state.save()

    print(f"\nDone!", flush=True)
    print(f"  Fetched with abstract: {fetched}", flush=True)
    print(f"  Failed/no abstract: {failed}", flush=True)

    stats = state.stats()
    print(f"\nCurrent state:", flush=True)
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}", flush=True)


if __name__ == "__main__":
    main()
