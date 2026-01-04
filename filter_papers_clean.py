#!/usr/bin/env python3
"""
Clean, maintainable paper filtering tool.

Usage:
    python filter_papers_clean.py filter [options]  # Filter papers
    python filter_papers_clean.py stats [options]   # Show statistics
    python filter_papers_clean.py analyze [options] # Analyze false positives

Examples:
    # Filter papers from papers.json
    python filter_papers_clean.py filter

    # Filter with custom input/output
    python filter_papers_clean.py filter -i papers.json -o filtered.json

    # Show statistics about the collection
    python filter_papers_clean.py stats

    # Analyze to identify false positives
    python filter_papers_clean.py analyze
"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
