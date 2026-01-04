# Code Structure

Clean, maintainable architecture for filtering model stealing papers.

## Directory Layout

```
.
├── src/                          # Source code
│   ├── models/                   # Data models
│   │   └── paper.py             # Paper dataclass
│   ├── filters/                  # Filter implementations
│   │   ├── base.py              # Base filter interface
│   │   ├── exclusion_filter.py  # Remove false positives
│   │   ├── relevance_filter.py  # Check for model stealing terms
│   │   └── topic_filter.py      # (included in exclusion_filter.py)
│   ├── config.py                # Keywords and configuration
│   ├── pipeline.py              # Filtering pipeline orchestration
│   ├── utils.py                 # I/O utilities
│   └── cli.py                   # Command-line interface
├── filter_papers_clean.py        # Main entry point
└── papers.json                   # Input data
```

## Architecture Overview

### Core Components

#### 1. Data Model (`src/models/paper.py`)
- **`Paper`**: Dataclass representing a research paper
- Provides convenient properties like `has_abstract`, `abstract_lower`
- Handles serialization to/from dictionaries

#### 2. Filter System (`src/filters/`)
- **`PaperFilter`**: Abstract base class for all filters
- **`FilterResult`**: Result object with `is_relevant`, `reason`, `confidence`
- **`Confidence`**: Enum for HIGH, MEDIUM, LOW confidence levels

**Filter Implementations:**
- **`ExclusionFilter`**: Removes obvious false positives
  - Electromagnetic/side-channel papers without model stealing context
  - Wrong type of stealing (prompts, links, data)
  - Citation-only mentions

- **`RelevanceFilter`**: Checks for model stealing terminology
  - Requires abstract with relevant terms
  - Looks for strong indicators (e.g., "model extraction attack")
  - Verifies terms appear in meaningful context

- **`TopicFilter`**: Ensures model stealing is primary focus
  - Counts mentions of model stealing vs other topics
  - Excludes papers primarily about watermarking, backdoors, etc.

#### 3. Pipeline (`src/pipeline.py`)
- **`FilterPipeline`**: Orchestrates filters in sequence
- **`FilterStats`**: Computes statistics about filtering results
- **`PipelineResult`**: Final result with paper + filtering metadata

**Pipeline Flow:**
```
Paper → ExclusionFilter → RelevanceFilter → TopicFilter → Result
         ↓ Exclude          ↓ Exclude        ↓ Exclude     ↓ Keep
```

#### 4. Configuration (`src/config.py`)
- Centralized keyword definitions
- High-quality vs core keywords
- Problematic keywords to avoid
- Exclusion signals for false positives

#### 5. CLI (`src/cli.py`)
- **`filter`**: Filter papers to keep only relevant ones
- **`stats`**: Show statistics about collection
- **`analyze`**: Analyze to identify false positives

## Design Principles

### 1. Single Responsibility
Each filter has one job:
- `ExclusionFilter`: Remove false positives
- `RelevanceFilter`: Check for model stealing terms
- `TopicFilter`: Verify primary focus

### 2. Open/Closed Principle
- Filters implement `PaperFilter` interface
- Easy to add new filters without changing pipeline
- Custom filters can be added via `pipeline.add_filter()`

### 3. Dependency Inversion
- Pipeline depends on `PaperFilter` interface, not concrete implementations
- Filters can be swapped or reordered

### 4. Clean Code
- Type hints throughout
- Docstrings for all public methods
- Self-documenting variable names
- No magic numbers (constants in config.py)

### 5. Testability
- Each component is independently testable
- Filters are pure functions (Paper → FilterResult)
- No global state

## Usage

### Basic Usage
```bash
# Filter papers (default: papers.json → papers_filtered.json)
python filter_papers_clean.py filter

# Show statistics
python filter_papers_clean.py stats

# Analyze false positives
python filter_papers_clean.py analyze
```

### Advanced Usage
```bash
# Custom input/output
python filter_papers_clean.py filter -i papers.json -o output.json

# Show sample excluded papers
python filter_papers_clean.py filter --show-samples

# Stats from different file
python filter_papers_clean.py stats -i papers_filtered.json
```

### Programmatic Usage
```python
from src.models.paper import Paper
from src.pipeline import FilterPipeline
from src.utils import load_papers, save_papers

# Load papers
papers, metadata = load_papers("papers.json")

# Create and run pipeline
pipeline = FilterPipeline()
results = pipeline.process_batch(papers)

# Get relevant papers
relevant = [r.paper for r in results if r.is_relevant]

# Save
save_papers(relevant, "filtered.json", metadata=metadata)
```

## Extending the System

### Adding a New Filter

```python
from src.filters.base import PaperFilter, FilterResult, Confidence
from src.models.paper import Paper

class MyCustomFilter(PaperFilter):
    """Description of what this filter does."""

    def filter(self, paper: Paper) -> FilterResult:
        # Your logic here
        if some_condition:
            return FilterResult(
                is_relevant=False,
                reason="Why it was excluded",
                confidence=Confidence.HIGH
            )
        return FilterResult(
            is_relevant=True,
            reason="Why it passed",
            confidence=Confidence.HIGH
        )

# Use it
from src.pipeline import FilterPipeline

pipeline = FilterPipeline()
pipeline.add_filter("my_filter", MyCustomFilter())
```

### Adding New Keywords

Edit `src/config.py`:
```python
# Add to HIGH_QUALITY_KEYWORDS for strong signals
HIGH_QUALITY_KEYWORDS = [
    "model extraction attack",
    "your new keyword here",
]

# Or to PROBLEMATIC_KEYWORDS for exclusions
PROBLEMATIC_KEYWORDS = [
    "electromagnetic analysis",
    "false positive keyword",
]
```

## Maintenance

### Monthly Tasks
1. Run filter on new papers
2. Review `papers_filtered_excluded.json` for false positives
3. Update keywords in `config.py` if needed

### Adding New Papers
```python
from src.utils import load_papers, save_papers
from src.models.paper import Paper

# Load existing
papers, metadata = load_papers("papers.json")

# Add new paper
new_paper = Paper(
    paper_id="...",
    title="...",
    # ... other fields
)
papers.append(new_paper)

# Save
save_papers(papers, "papers.json", metadata=metadata)
```

## Benefits of This Architecture

1. **Maintainable**: Each component has a clear purpose
2. **Extensible**: Easy to add new filters or modify existing ones
3. **Testable**: Components can be tested independently
4. **Self-documenting**: Code explains itself through names and types
5. **Configurable**: Keywords centralized in config.py
6. **Reusable**: Components can be used in other contexts

## Migration from Old Scripts

Old files you can now remove:
- `analyze_papers.py` → Use `filter_papers_clean.py analyze`
- `analyze_keywords.py` → Functionality in `FilterStats`
- `filter_papers.py` → Use `filter_papers_clean.py filter`

The new system consolidates all functionality into a clean, modular architecture.
