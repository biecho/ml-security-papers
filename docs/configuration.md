# Configuration Guide

The paper filtering system uses YAML configuration files for easy customization and domain switching.

## Configuration File Structure

### Basic Structure

```yaml
domain:
  name: "your_domain"
  description: "Description of the research area"

high_quality_keywords: [...]
core_keywords: [...]
defense_keywords: [...]
problematic_keywords: [...]
required_abstract_terms: [...]

exclusion_signals:
  category1: [terms...]
  category2: [terms...]

other_topics:
  topic1: [terms...]
  topic2: [terms...]

filtering_rules:
  min_term_mentions: 1
  watermark_dominance_threshold: 3
  topic_dominance_ratio: 2.0
  context_window: 50
  first_paragraph_length: 300
```

## Configuration Sections

### 1. Domain Information

```yaml
domain:
  name: "model_stealing"  # Internal identifier
  description: "Research on stealing, extracting, or cloning machine learning models"
```

**Purpose:** Identifies the research domain and is used in messages.

### 2. Keywords

#### High-Quality Keywords
Strong signals that a paper is highly relevant:
```yaml
high_quality_keywords:
  - "model extraction attack"
  - "knockoff nets"
```

**When to use:** Terms that almost always indicate a relevant paper.

#### Core Keywords
General terms that may indicate relevance:
```yaml
core_keywords:
  - "model extraction"
  - "model stealing"
```

**When to use:** Broader terms that need context verification.

#### Defense Keywords
Defense-related terms (still relevant to domain):
```yaml
defense_keywords:
  - "model extraction defense"
  - "prevent model stealing"
```

**When to use:** Papers about defending against the attack type.

#### Problematic Keywords
Terms that cause many false positives:
```yaml
problematic_keywords:
  - "electromagnetic analysis"
  - "side-channel attack"
```

**When to use:** Keywords to avoid or require extra verification.

### 3. Required Abstract Terms

Terms that MUST appear in the abstract:
```yaml
required_abstract_terms:
  - "model stealing"
  - "model extraction"
  - "clone model"
```

**Purpose:** Papers without these terms in the abstract are excluded.

### 4. Exclusion Signals

Patterns indicating the paper is about something else:
```yaml
exclusion_signals:
  prompt_stealing:
    - "prompt stealing"
    - "prompt template"
  link_stealing:
    - "link stealing"
    - "graph structure"
```

**Purpose:** Identify false positives (wrong type of "stealing").

### 5. Other Topics

Topics that may mention your domain but have a different primary focus:
```yaml
other_topics:
  watermarking:
    - "watermark"
    - "fingerprint"
  backdoor:
    - "backdoor attack"
    - "trojan attack"
```

**Purpose:** Papers primarily about these topics are filtered out.

### 6. Filtering Rules

Thresholds and parameters:
```yaml
filtering_rules:
  # Minimum mentions of domain terms for relevance
  min_term_mentions: 1

  # Threshold for topic dominance (e.g., watermarking)
  watermark_dominance_threshold: 3

  # Ratio for determining if another topic is dominant
  topic_dominance_ratio: 2.0

  # Character window for context matching
  context_window: 50

  # Characters from start of abstract to check for primary focus
  first_paragraph_length: 300
```

## Using Configurations

### Default Configuration

By default, the system uses `config.yaml`:
```bash
python filter_papers_clean.py filter
```

### Custom Configuration

Specify a different config file:
```bash
python filter_papers_clean.py filter -c config_privacy.yaml
```

### Domain-Specific Configurations

Create domain-specific configs with naming pattern `config_{domain}.yaml`:
- `config_model_stealing.yaml`
- `config_privacy_attacks.yaml`
- `config_adversarial_examples.yaml`

Load via code:
```python
from src.config import Config

config = Config.for_domain("privacy_attacks")
```

## Creating a New Domain Configuration

### Step 1: Copy Template

```bash
cp config.yaml config_my_domain.yaml
```

### Step 2: Update Domain Information

```yaml
domain:
  name: "my_domain"
  description: "Brief description of your research area"
```

### Step 3: Define Keywords

**High-quality keywords** (strongest signals):
- Specific attack names
- Well-known technique names
- Established terminology

**Core keywords** (general terms):
- Broader concepts
- Action verbs + target (e.g., "attack models")
- Common phrases in the field

**Problematic keywords** (known false positives):
- Terms with multiple meanings
- Overly broad terms
- Title-only matches

### Step 4: Define Exclusions

**Exclusion signals** (wrong domain):
- Similar attacks on different targets
- Related but distinct concepts

**Other topics** (different primary focus):
- Related research areas
- Defense mechanisms (if not your focus)
- Prerequisite technologies

### Step 5: Tune Filtering Rules

Adjust thresholds based on your domain:
- `min_term_mentions`: How many times terms should appear
- `topic_dominance_ratio`: When another topic overshadows yours
- `context_window`: How close terms need to be
- `first_paragraph_length`: How much of abstract to prioritize

### Step 6: Test and Iterate

```bash
# Filter with your config
python filter_papers_clean.py filter -c config_my_domain.yaml

# Analyze results
python filter_papers_clean.py analyze -c config_my_domain.yaml

# Check excluded papers for false negatives
cat papers_filtered_excluded.json | jq '.papers[].title'
```

## Example: Privacy Attacks Domain

See `config_example_privacy.yaml` for a complete example of adapting the system to a different domain.

Key differences from model stealing:
- Different keywords (membership inference vs model extraction)
- Different exclusion signals (model stealing becomes an exclusion)
- Same structure, easy to maintain

## Validation

The system validates your config file on load:
- Checks for required sections
- Ensures proper YAML syntax
- Reports missing or invalid sections

Error example:
```
Configuration file missing required sections: high_quality_keywords, core_keywords
```

## Best Practices

1. **Start broad, then narrow**
   - Begin with many keywords
   - Remove those causing false positives
   - Add to problematic_keywords list

2. **Test incrementally**
   - Add a few keywords at a time
   - Check what new papers are included
   - Adjust thresholds as needed

3. **Document your choices**
   - Add comments explaining non-obvious keywords
   - Note why certain terms are problematic
   - Track changes over time

4. **Review regularly**
   - New terminology emerges
   - Field boundaries shift
   - False positive patterns change

5. **Version control**
   - Keep configs in git
   - Track changes to keywords
   - Tag working configurations

## Programmatic Access

Access config in Python code:

```python
from src.config import get_config, Config

# Get global config
config = get_config()
print(config.domain_name)
print(config.high_quality_keywords)

# Load specific config
config = Config("config_privacy.yaml")

# Set as global
from src.config import set_config
set_config(config)
```

## Troubleshooting

**Problem:** Too many false positives
- Add problematic keywords
- Tighten exclusion signals
- Increase `topic_dominance_ratio`

**Problem:** Missing relevant papers
- Add more core keywords
- Check problematic_keywords list
- Lower `min_term_mentions`

**Problem:** Config not loading
- Check YAML syntax
- Ensure all required sections present
- Verify file path is correct

**Problem:** Domain name appears wrong in output
- Check `domain.name` in config
- Ensure proper YAML indentation
- Reload config after changes
