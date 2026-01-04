# Model Stealing Papers - Paper Filtering System

Clean, maintainable tool for filtering research papers by domain. Currently configured for model stealing/extraction research, but easily adaptable to other domains.

## Features

- **YAML Configuration**: Easy keyword management and domain switching
- **Modular Architecture**: Clean, extensible filter system
- **Multi-Stage Filtering**: Exclusion → Relevance → Topic filters
- **Domain-Agnostic**: Adapt to any research domain by editing config
- **Type-Safe**: Full type hints throughout
- **CLI Interface**: Simple command-line tools

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Basic Usage

```bash
# Filter papers (uses config.yaml)
python filter_papers_clean.py filter

# Show statistics
python filter_papers_clean.py stats

# Analyze false positives
python filter_papers_clean.py analyze
```

### Output Files

- `papers_filtered.json` - Relevant papers (keep these)
- `papers_filtered_excluded.json` - Excluded papers with reasons

## Configuration

The system uses YAML configuration files for easy customization.

### Default Configuration

Edit `config.yaml` to adjust keywords:

```yaml
domain:
  name: "model_stealing"
  description: "Research on stealing, extracting, or cloning ML models"

high_quality_keywords:
  - "model extraction attack"
  - "knockoff nets"

core_keywords:
  - "model extraction"
  - "model stealing"

# ... more configuration
```

### Switch to a Different Domain

```bash
# Create config for new domain
cp config.yaml config_privacy.yaml

# Edit config_privacy.yaml with domain-specific keywords
# Then use it:
python filter_papers_clean.py filter -c config_privacy.yaml
```

See [docs/configuration.md](docs/configuration.md) for detailed configuration guide.

## Project Structure

```
.
├── src/                          # Source code
│   ├── models/
│   │   └── paper.py             # Paper data model
│   ├── filters/
│   │   ├── base.py              # Filter interface
│   │   ├── exclusion_filter.py  # Remove false positives
│   │   └── relevance_filter.py  # Check relevance
│   ├── config.py                # Configuration loader
│   ├── pipeline.py              # Filtering pipeline
│   ├── utils.py                 # I/O utilities
│   └── cli.py                   # CLI interface
│
├── docs/                         # Documentation
│   ├── usage.md                 # How to use
│   ├── configuration.md         # Config guide
│   ├── architecture.md          # Architecture details
│   └── collection_strategy.md   # Collection approach
│
├── config.yaml                   # Main configuration
├── filter_papers_clean.py        # Entry point
├── requirements.txt              # Dependencies
└── papers.json                   # Input data
```

## Documentation

- **[Usage Guide](docs/usage.md)** - How to use the tool
- **[Configuration](docs/configuration.md)** - YAML configuration guide
- **[Architecture](docs/architecture.md)** - System design and extension
- **[Collection Strategy](docs/collection_strategy.md)** - Paper collection approach

## Commands

### filter

Filter papers to keep only relevant ones:

```bash
# Basic
python filter_papers_clean.py filter

# Custom input/output
python filter_papers_clean.py filter -i papers.json -o output.json

# Custom configuration
python filter_papers_clean.py filter -c config_privacy.yaml

# Show sample excluded papers
python filter_papers_clean.py filter --show-samples
```

### stats

Show collection statistics:

```bash
python filter_papers_clean.py stats

# Output:
# - Total papers
# - Papers by year
# - Papers by venue
# - With/without abstracts
```

### analyze

Analyze false positives:

```bash
python filter_papers_clean.py analyze

# Output:
# - Filtering statistics
# - Common exclusion reasons
# - Sample papers for each reason
```

## Adapting to Other Domains

The system is designed to work with any research domain:

1. **Copy the config template**:
   ```bash
   cp config.yaml config_my_domain.yaml
   ```

2. **Edit domain information**:
   ```yaml
   domain:
     name: "my_domain"
     description: "Research on X"
   ```

3. **Update keywords**:
   - High-quality keywords (strong signals)
   - Core keywords (general terms)
   - Problematic keywords (false positives)
   - Required abstract terms

4. **Define exclusions**:
   - Exclusion signals (wrong domain)
   - Other topics (different primary focus)

5. **Test and iterate**:
   ```bash
   python filter_papers_clean.py filter -c config_my_domain.yaml
   python filter_papers_clean.py analyze -c config_my_domain.yaml
   ```

See [docs/configuration.md](docs/configuration.md) for detailed instructions and examples.

## Examples

### Model Stealing (Default)

```bash
python filter_papers_clean.py filter
# Filters for model extraction/stealing papers
```

### Privacy Attacks

```bash
python filter_papers_clean.py filter -c config_privacy.yaml
# Filters for membership inference, attribute inference papers
```

### Custom Domain

```yaml
# config_my_domain.yaml
domain:
  name: "adversarial_examples"
  description: "Research on adversarial attacks and defenses"

high_quality_keywords:
  - "adversarial example"
  - "adversarial attack"
  # ...
```

```bash
python filter_papers_clean.py filter -c config_my_domain.yaml
```

## Development

### Adding a Custom Filter

```python
from src.filters.base import PaperFilter, FilterResult, Confidence
from src.models.paper import Paper

class MyCustomFilter(PaperFilter):
    """Custom filter for specific criteria."""

    def filter(self, paper: Paper) -> FilterResult:
        # Your logic here
        if condition:
            return FilterResult(
                is_relevant=False,
                reason="Why excluded",
                confidence=Confidence.HIGH
            )
        return FilterResult(
            is_relevant=True,
            reason="Why included",
            confidence=Confidence.HIGH
        )

# Use it
from src.pipeline import FilterPipeline

pipeline = FilterPipeline()
pipeline.add_filter("my_filter", MyCustomFilter())
```

### Programmatic Usage

```python
from src.config import Config, set_config
from src.pipeline import FilterPipeline
from src.utils import load_papers, save_papers

# Load custom config
config = Config("config_privacy.yaml")
set_config(config)

# Load and filter papers
papers, metadata = load_papers("papers.json")
pipeline = FilterPipeline()
results = pipeline.process_batch(papers)

# Get relevant papers
relevant = [r.paper for r in results if r.is_relevant]

# Save
save_papers(relevant, "filtered.json", metadata=metadata)
```

## Current Status

- **919 papers** in collection
- **~45% relevant** to model stealing (after filtering)
- **Main issues identified**: Electromagnetic papers, prompt stealing, watermarking papers
- **Solution**: Multi-stage filtering with YAML configuration

## Contributing

To improve the filtering:

1. **Add keywords** to `config.yaml`
2. **Report false positives** as problematic keywords
3. **Adjust thresholds** in filtering_rules
4. **Test changes** with `analyze` command

## License

See LICENSE file.

## Citation

If using this tool for research, please cite the original model stealing papers and any papers used from the collection.
