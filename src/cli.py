"""Command-line interface for paper filtering."""

import argparse
import sys
from pathlib import Path

from src.pipeline import FilterPipeline, FilterStats
from src.utils import load_papers, print_sample_papers, save_papers, save_results


def filter_command(args: argparse.Namespace) -> None:
    """Filter papers to keep only relevant ones."""
    # Load config if specified
    if hasattr(args, 'config') and args.config:
        from src.config import set_config, Config
        config = Config(args.config)
        set_config(config)
        print(f"Using configuration: {config.domain_name}")

    print(f"Loading papers from {args.input}...")
    papers, metadata = load_papers(args.input)
    print(f"Loaded {len(papers)} papers\n")

    # Create and run pipeline
    pipeline = FilterPipeline()
    print("Running filtering pipeline...")

    def progress(current: int, total: int) -> None:
        if current % 100 == 0 or current == total:
            print(f"  Processed {current}/{total} papers...", end="\r")

    results = pipeline.process_batch(papers, progress_callback=progress)
    print()  # New line after progress

    # Calculate statistics
    stats = FilterStats(results)
    stats.print_summary()

    # Separate relevant and excluded papers
    relevant_results = [r for r in results if r.is_relevant]
    excluded_results = [r for r in results if not r.is_relevant]

    # Save results
    output_dir = Path(args.output).parent if args.output else Path(".")
    output_base = Path(args.output).stem if args.output else "papers_filtered"

    # Save relevant papers
    relevant_papers = [r.paper for r in relevant_results]
    filtered_path = output_dir / f"{output_base}.json"
    save_papers(
        relevant_papers,
        filtered_path,
        metadata={"keywords": metadata.get("keywords"), "seed_papers": metadata.get("seed_papers")},
        note="Filtered to include only papers primarily about model stealing/extraction",
    )
    print(f"\n✓ Saved {len(relevant_papers)} relevant papers to: {filtered_path}")

    # Save excluded papers
    excluded_path = output_dir / f"{output_base}_excluded.json"
    save_results(excluded_results, excluded_path)
    print(f"✓ Saved {len(excluded_results)} excluded papers to: {excluded_path}")

    # Save papers needing manual review (low confidence relevant)
    review_results = [r for r in results if r.is_relevant and r.reason.startswith("No abstract")]
    if review_results:
        review_path = output_dir / f"{output_base}_needs_review.json"
        save_results(review_results, review_path)
        print(f"✓ Saved {len(review_results)} papers needing review to: {review_path}")

    # Show samples
    if args.show_samples:
        print_sample_papers(
            [r.paper for r in excluded_results[:10]],
            "SAMPLE EXCLUDED PAPERS",
            max_papers=10,
        )


def stats_command(args: argparse.Namespace) -> None:
    """Show statistics about the paper collection."""
    papers, metadata = load_papers(args.input)

    print("=" * 80)
    print("COLLECTION STATISTICS")
    print("=" * 80)
    print(f"\nTotal papers: {len(papers)}")
    print(f"Last updated: {metadata.get('updated', 'Unknown')}")

    # Papers by year
    by_year = {}
    for paper in papers:
        if paper.year:
            by_year[paper.year] = by_year.get(paper.year, 0) + 1

    print("\nPapers by year:")
    for year in sorted(by_year.keys(), reverse=True)[:10]:
        print(f"  {year}: {by_year[year]}")

    # Papers with/without abstracts
    with_abstract = sum(1 for p in papers if p.has_abstract)
    print(f"\nWith abstract: {with_abstract} ({with_abstract/len(papers)*100:.1f}%)")
    print(f"Without abstract: {len(papers)-with_abstract} ({(len(papers)-with_abstract)/len(papers)*100:.1f}%)")

    # Top venues
    by_venue = {}
    for paper in papers:
        if paper.venue:
            by_venue[paper.venue] = by_venue.get(paper.venue, 0) + 1

    print("\nTop 10 venues:")
    for venue, count in sorted(by_venue.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {count:4d} - {venue}")


def analyze_command(args: argparse.Namespace) -> None:
    """Analyze papers to identify false positives."""
    papers, _ = load_papers(args.input)
    print(f"Analyzing {len(papers)} papers...\n")

    pipeline = FilterPipeline()
    results = pipeline.process_batch(papers)

    stats = FilterStats(results)
    stats.print_summary()

    # Show most common exclusion reasons in detail
    print("\n" + "=" * 80)
    print("DETAILED EXCLUSION ANALYSIS")
    print("=" * 80)

    excluded = [r for r in results if not r.is_relevant]
    by_reason = {}
    for result in excluded:
        reason = result.reason
        if reason not in by_reason:
            by_reason[reason] = []
        by_reason[reason].append(result.paper)

    for reason, papers_list in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"\n{reason} ({len(papers_list)} papers):")
        print("-" * 80)
        for i, paper in enumerate(papers_list[:3], 1):
            print(f"{i}. {paper.title} ({paper.year})")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter and analyze model stealing papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter papers to keep only relevant ones")
    filter_parser.add_argument(
        "-i", "--input", default="papers.json", help="Input JSON file (default: papers.json)"
    )
    filter_parser.add_argument(
        "-o",
        "--output",
        default="papers_filtered.json",
        help="Output file base name (default: papers_filtered.json)",
    )
    filter_parser.add_argument(
        "-c", "--config", help="Configuration YAML file (default: config.yaml)"
    )
    filter_parser.add_argument(
        "--show-samples", action="store_true", help="Show sample excluded papers"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics about paper collection")
    stats_parser.add_argument(
        "-i", "--input", default="papers.json", help="Input JSON file (default: papers.json)"
    )

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze papers to identify false positives")
    analyze_parser.add_argument(
        "-i", "--input", default="papers.json", help="Input JSON file (default: papers.json)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "filter":
            filter_command(args)
        elif args.command == "stats":
            stats_command(args)
        elif args.command == "analyze":
            analyze_command(args)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
