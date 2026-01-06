# OWASP ML Security Top 10 - Academic Paper Collection

A curated collection of academic papers covering the [OWASP Machine Learning Security Top 10](https://owasp.org/www-project-machine-learning-security-top-10/) categories. Papers are automatically fetched from Semantic Scholar and filtered using configurable keyword-based rules.

## Live Website

Browse the papers: **[https://biecho.github.io/model-stealing-papers/web/](https://biecho.github.io/model-stealing-papers/web/)**

## Categories

| ID | Category | Papers | Description |
|----|----------|--------|-------------|
| ML01 | Input Manipulation Attack | 596 | Adversarial examples, evasion attacks |
| ML02 | Data Poisoning Attack | 156 | Training data manipulation |
| ML03 | Model Inversion Attack | 230 | Extracting training data from models |
| ML04 | Membership Inference Attack | 199 | Determining if data was used in training |
| ML05 | Model Theft | 403 | Model extraction and stealing |
| ML06 | AI Supply Chain Attacks | 29 | Attacks on ML pipelines and dependencies |
| ML07 | Transfer Learning Attack | 580 | Exploiting pre-trained models |
| ML08 | Model Skewing | 578 | Manipulating model behavior over time |
| ML09 | Output Integrity Attack | 627 | Manipulating model outputs |
| ML10 | Model Poisoning | 730 | Backdoors and trojans in models |

### Subcategories

- **ML01a**: Prompt Injection (543 papers) - LLM-specific input manipulation

## Installation

```bash
# Clone the repository
git clone https://github.com/biecho/model-stealing-papers.git
cd model-stealing-papers

# Create virtual environment and install
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Usage

### View Statistics

```bash
python scripts/run_all.py --stats
```

### List Available Categories

```bash
python scripts/run_all.py --list
```

### Filter Papers for All Categories

```bash
python scripts/run_all.py
```

### Filter a Specific Category

```bash
python scripts/run_all.py --category ML05
```

### Fetch Fresh Papers from Semantic Scholar

```bash
# Requires S2_API_KEY environment variable
export S2_API_KEY=your_api_key

# Fetch main dataset
python scripts/fetch_papers.py

# Fetch for a specific config
python scripts/fetch_papers.py -c configs/ml01a_prompt_injection.yaml -o data/ml01a_raw.json
```

## Project Structure

```
.
├── configs/                    # YAML configurations per category
│   ├── ml01_input_manipulation.yaml
│   ├── ml01a_prompt_injection.yaml  # Subcategory
│   ├── ml02_data_poisoning.yaml
│   └── ...
├── data/                       # Generated data
│   ├── papers.json             # Raw fetched papers
│   ├── ml01_papers.json        # Filtered papers per category
│   ├── ml01a_papers.json       # Subcategory papers
│   └── manifest.json           # Category metadata
├── ml_security/                # Python package
│   ├── filters/                # Filtering logic
│   ├── models/                 # Data models
│   ├── config.py               # Configuration loader
│   ├── pipeline.py             # Filter pipeline
│   └── utils.py                # Utilities
├── scripts/                    # CLI scripts
│   ├── fetch_papers.py         # Fetch from Semantic Scholar
│   ├── filter_papers_clean.py  # Filter single category
│   └── run_all.py              # Filter all categories
├── web/                        # Website
│   ├── index.html
│   ├── css/
│   └── js/
└── pyproject.toml              # Package configuration
```

## Configuration

Each category has a YAML configuration file in `configs/`. Example:

```yaml
domain:
  name: "model_stealing"
  owasp_id: "ML05"
  description: "Techniques to steal or extract ML models"
  short_description: "Model extraction and stealing"

high_quality_keywords:
  - "model stealing"
  - "model extraction attack"

core_keywords:
  - "steal model"
  - "extract model"

exclusion_signals:
  - "electromagnetic"
  - "power analysis"
```

### Adding a Subcategory

1. Create a new config file (e.g., `configs/ml05a_example.yaml`)
2. Add `parent_id` to link to the parent category:

```yaml
domain:
  name: "example_subcategory"
  owasp_id: "ML05a"
  parent_id: "ML05"  # Links to parent
  description: "Specific subcategory of model theft"
```

3. Update `web/js/categories.js` to include the subcategory
4. Run the pipeline to generate filtered papers

## Automation

Papers are automatically updated every 12 hours via GitHub Actions. The workflow:

1. Fetches new papers from Semantic Scholar
2. Filters papers for all categories
3. Commits and pushes updated data

## Development

### Entry Points

After installation, these commands are available:

```bash
fetch-papers    # Fetch papers from Semantic Scholar
filter-papers   # Filter papers for a single category
run-all         # Filter all categories
```

### Programmatic Usage

```python
from ml_security.config import Config, set_config
from ml_security.pipeline import FilterPipeline
from ml_security.utils import load_papers, save_papers

# Load configuration
config = Config("configs/ml05_model_stealing.yaml")
set_config(config)

# Load and filter papers
papers, metadata = load_papers("data/papers.json")
pipeline = FilterPipeline()
results = pipeline.process_batch(papers)

# Get relevant papers
relevant = [r.paper for r in results if r.is_relevant]
print(f"Found {len(relevant)} relevant papers")
```

## Data Sources

- Papers fetched from [Semantic Scholar API](https://www.semanticscholar.org/)
- Categories based on [OWASP ML Security Top 10](https://owasp.org/www-project-machine-learning-security-top-10/)

## License

MIT

## Contributing

1. Fork the repository
2. Add or improve category configurations
3. Submit a pull request

To improve filtering accuracy:
- Add keywords to category configs
- Report false positives as exclusion signals
- Suggest new subcategories
