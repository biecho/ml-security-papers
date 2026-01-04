# Usage Guide

Quick guide for using the paper filtering tool.

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Filter Papers
Remove false positives and keep only papers about model stealing:
```bash
python filter_papers_clean.py filter
```

Output:
- `papers_filtered.json` - Relevant papers (keep these)
- `papers_filtered_excluded.json` - Excluded papers with reasons

### Using Custom Configuration
Filter with a different domain configuration:
```bash
python filter_papers_clean.py filter -c config_privacy.yaml
```

### Show Statistics
View statistics about your paper collection:
```bash
python filter_papers_clean.py stats
```

### Analyze False Positives
Identify common false positive patterns:
```bash
python filter_papers_clean.py analyze
```

## Commands

### `filter` - Filter Papers

Basic usage:
```bash
python filter_papers_clean.py filter
```

With options:
```bash
# Custom input/output files
python filter_papers_clean.py filter -i papers.json -o output.json

# Show sample excluded papers
python filter_papers_clean.py filter --show-samples
```

**Output files:**
- `{output}.json` - Filtered papers (relevant only)
- `{output}_excluded.json` - Excluded papers with reasons

### `stats` - Collection Statistics

```bash
python filter_papers_clean.py stats
```

Shows:
- Total papers
- Papers by year
- Papers with/without abstracts
- Top venues

### `analyze` - Analyze False Positives

```bash
python filter_papers_clean.py analyze
```

Shows:
- Filtering statistics
- Common exclusion reasons
- Sample papers for each reason

## Programmatic Usage

```python
from src.models.paper import Paper
from src.pipeline import FilterPipeline, FilterStats
from src.utils import load_papers, save_papers

# Load papers
papers, metadata = load_papers("papers.json")

# Create pipeline
pipeline = FilterPipeline()

# Process papers
results = pipeline.process_batch(papers)

# Get statistics
stats = FilterStats(results)
stats.print_summary()

# Get relevant papers
relevant_papers = [r.paper for r in results if r.is_relevant]

# Save
save_papers(relevant_papers, "filtered.json", metadata=metadata)
```

## Configuration

The system uses YAML configuration files. See [configuration.md](configuration.md) for detailed documentation.

### Quick Configuration Changes

Edit `config.yaml` to adjust keywords:
```yaml
# Add new keywords
high_quality_keywords:
  - "model extraction attack"
  - "your new keyword here"

# Add problematic keywords to exclude
problematic_keywords:
  - "false positive term"
```

### Switch Domains

Create a new config file for a different domain:
```bash
cp config.yaml config_privacy.yaml
# Edit config_privacy.yaml with domain-specific keywords
python filter_papers_clean.py filter -c config_privacy.yaml
```

## Customization

### Add Custom Filter

```python
from src.filters.base import PaperFilter, FilterResult, Confidence
from src.models.paper import Paper

class VenueFilter(PaperFilter):
    """Filter papers by venue."""

    def __init__(self, allowed_venues):
        self.allowed_venues = allowed_venues

    def filter(self, paper: Paper) -> FilterResult:
        if paper.venue not in self.allowed_venues:
            return FilterResult(
                is_relevant=False,
                reason=f"Venue not in allowed list",
                confidence=Confidence.HIGH
            )
        return FilterResult(
            is_relevant=True,
            reason="Venue is allowed",
            confidence=Confidence.HIGH
        )

# Use it
from src.pipeline import FilterPipeline

pipeline = FilterPipeline()
pipeline.add_filter("venue", VenueFilter(["USENIX Security", "S&P"]))
results = pipeline.process_batch(papers)
```

### Modify Keywords

Edit `config.yaml`:

```yaml
# Add keywords
high_quality_keywords:
  - "model extraction attack"
  - "your new keyword"  # Add here

# Remove problematic keywords by commenting out
problematic_keywords:
  - "electromagnetic analysis"
  # - "removed keyword"  # Comment out to remove
```

Changes take effect immediately on next run.

## Understanding Results

### Confidence Levels

- **HIGH**: Very confident in the decision
- **MEDIUM**: Moderately confident
- **LOW**: Uncertain, may need manual review

### Common Exclusion Reasons

1. **"No model stealing terminology in abstract"**
   - Paper matched keywords but doesn't discuss model stealing

2. **"Prompt stealing, not model stealing"**
   - About stealing prompts for text-to-image models

3. **"Link stealing, not model stealing"**
   - About inferring graph structure, not stealing models

4. **"Primarily about watermarking"**
   - Defense paper that only mentions model stealing as motivation

5. **"Only mentioned in citations"**
   - Model stealing appears only in references

## Tips

### For Best Results

1. **Ensure papers have abstracts** - Papers without abstracts are excluded
2. **Review excluded papers** - Check `papers_filtered_excluded.json` for false negatives
3. **Update keywords regularly** - Add new terminology as field evolves
4. **Spot-check results** - Manually review a sample of filtered papers

### Handling Edge Cases

**Papers about defenses:**
- Kept if they evaluate model stealing attacks
- Excluded if only about watermarking without attack evaluation

**Survey papers:**
- Kept if primarily about model stealing
- Excluded if model stealing is just one of many topics

**Side-channel papers:**
- Kept if they extract the model
- Excluded if only about analysis without extraction

## See Also

- [configuration.md](configuration.md) - Configuration guide
- [architecture.md](architecture.md) - Architecture details
- [collection_strategy.md](collection_strategy.md) - Paper collection strategy
