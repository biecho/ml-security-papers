# ML Security Papers - Design Document

*Goal: The best ML Security Research Website on the planet*

---

## Table of Contents

1. [Users & Needs](#users--needs)
2. [Data Architecture](#data-architecture)
3. [Pipeline Design](#pipeline-design)
4. [Classification System](#classification-system)
5. [Website Features](#website-features)
6. [LLM Prompt Design](#llm-prompt-design)
7. [API & Data Sources](#api--data-sources)
8. [Open Questions](#open-questions)

---

## Users & Needs

### Target Users

| User Type | Primary Questions |
|-----------|-------------------|
| **Security Researchers** | What attacks exist against LLMs? What defenses work? What's state of the art? |
| **ML Engineers** | Is my model vulnerable? How do I defend against X? What should I test? |
| **Red Teamers / Pentesters** | How do I attack this ML system? What tools exist? Show me PoC code |
| **Students / Newcomers** | Where do I start? What are seminal papers? What's hot right now? |
| **Policy / Compliance** | What risks exist? How do I map to OWASP? What should audits require? |

### User Needs

**Discovery:**
- What papers exist on topic X?
- What's new this month?
- What's trending / highly cited?
- What did this research group publish?
- Papers similar to this one?

**Understanding:**
- Explain this attack simply
- How does this defense work?
- What's the relationship between papers?
- What's the timeline of this research area?
- Who are the key researchers?

**Action:**
- Give me the PDF
- Show me the code
- How do I cite this?
- What should I read next?
- How do I reproduce this?

---

## Data Architecture

### Paper Data Model

```yaml
Paper:
  # === Identity (from S2) ===
  s2_paper_id: string           # Primary key, stable
  title: string

  # === Content ===
  tldr: string                  # S2 AI-generated summary
  abstract: string              # Full abstract
  eli5: string | null           # Optional: LLM-generated simple explanation

  # === Metadata (from S2) ===
  authors: [Author]
  year: int
  venue: string
  venue_type: conference | journal | preprint | workshop
  fields_of_study: [string]     # S2's categorization
  publication_types: [string]   # S2's paper type
  external_ids:                 # Cross-references
    DOI: string
    ArXiv: string
    DBLP: string
    PMID: string

  # === Metrics (from S2, updated periodically) ===
  citation_count: int
  influential_citation_count: int
  reference_count: int
  trending_score: float         # Calculated: recent citations / age
  metrics_updated_at: timestamp

  # === Resources ===
  pdf_url: string | null        # Open access PDF
  code_url: string | null       # GitHub, etc. (from PapersWithCode?)

  # === Our Classification (multi-label) ===
  owasp_labels: [string]        # [ML01, ML02, ...] - 1 to 3 labels
  paper_type: attack | defense | survey | benchmark | tool | theoretical
  domains: [string]             # [nlp, vision, audio, tabular, multimodal, ...]
  model_types: [string]         # [llm, cnn, transformer, diffusion, ...]
  assets_targeted: [string]     # [training-data, model-weights, api, embeddings, ...]
  tags: [string]                # Free-form tags

  classification_reasoning: string  # LLM's explanation
  classification_confidence: HIGH | LOW
  classified_at: timestamp

  # === Graph / Relationships ===
  depth: int                    # 0 = seed, 1 = cited by seed, etc.
  source: seed | citation | reference | discovery
  discovered_via: string | null # s2_paper_id of parent paper
  related_papers: [string]      # Computed or from S2

  # === Curation (manual) ===
  is_seminal: bool              # Foundational paper
  is_featured: bool             # Editor's pick
  collections: [string]         # "must-read", "best-2024", etc.

  # === Pipeline Status ===
  status: title_only | resolved | fetched | classified | expanded | discarded
```

### Tag Taxonomy (Controlled Vocabulary)

```yaml
domain:
  - nlp
  - vision
  - audio
  - tabular
  - multimodal
  - reinforcement-learning
  - federated-learning
  - generative

model_type:
  - llm
  - cnn
  - transformer
  - diffusion
  - gan
  - rnn
  - graph-neural-network

attack_vector:
  - adversarial-perturbation
  - backdoor
  - trojan
  - prompt-injection
  - jailbreak
  - data-extraction
  - membership-query
  - model-query

paper_type:
  - attack
  - defense
  - survey
  - benchmark
  - tool
  - theoretical

asset_targeted:
  - training-data
  - model-weights
  - model-api
  - predictions
  - embeddings
  - gradients
```

---

## Pipeline Design

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SEED SOURCE                                    │
│                  Awesome-ML-SP-Papers (~450 titles)                     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: RESOLVE                                                        │
│  ─────────────────                                                       │
│  Endpoint: S2 /paper/search/match                                       │
│  Input:    title string                                                 │
│  Output:   s2_paper_id                                                  │
│  Rate:     1/sec = 450 titles in ~8 minutes                            │
│                                                                          │
│  Status: title_only → resolved                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: FETCH                                                          │
│  ─────────────────                                                       │
│  Endpoint: S2 /paper/batch (up to 500 per request!)                     │
│  Input:    [s2_paper_id, ...]                                           │
│  Output:   Full metadata for all papers                                 │
│  Rate:     1 request for 500 papers                                     │
│                                                                          │
│  Fields: paperId, title, tldr, abstract, venue, year,                   │
│          fieldsOfStudy, s2FieldsOfStudy, publicationTypes,              │
│          citationCount, influentialCitationCount, referenceCount,       │
│          openAccessPdf, externalIds, authors                            │
│                                                                          │
│  Status: resolved → fetched                                             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: CLASSIFY                                                       │
│  ─────────────────                                                       │
│  Provider: Cerebras (or fallback: Groq, Google)                         │
│  Input:    Full paper context (title, tldr, abstract, venue, fields)    │
│  Output:   Multi-label classification + tags + reasoning                │
│  Rate:     Limited by LLM provider                                      │
│                                                                          │
│  Status: fetched → classified | discarded                               │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: EXPAND (depth-limited BFS)                                     │
│  ─────────────────                                                       │
│  Endpoints: S2 /paper/{id}/citations, /paper/{id}/references            │
│  Input:    Classified papers (ML01-ML10 only, not NONE)                 │
│  Output:   New s2_paper_ids → feed back to PHASE 2                      │
│  Rate:     1/sec per paper                                              │
│                                                                          │
│  Rules:                                                                  │
│    - Only expand papers classified as ML01-ML10                         │
│    - Max depth from seed (e.g., depth ≤ 2)                              │
│    - Skip papers already in system                                      │
│                                                                          │
│  Status: classified → expanded                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: EXPORT                                                         │
│  ─────────────────                                                       │
│  Output:   Website JSON files                                           │
│  Sorting:  By influentialCitationCount (quality ranking)                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Automated Jobs

```
┌─────────────────────────────────────────────────────────────────────────┐
│  JOB: UPDATE_METRICS (weekly)                                            │
│  ─────────────────────────────                                           │
│  Endpoint: S2 /paper/batch                                              │
│  Purpose:  Refresh citationCount, influentialCitationCount              │
│  Why:      Citation counts change over time                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  JOB: DISCOVER (daily)                                                   │
│  ─────────────────────                                                   │
│  Endpoint: S2 /paper/{id}/citations                                     │
│  Purpose:  Find NEW papers citing our classified papers                 │
│  Filter:   Only papers from last N days                                 │
│  Output:   New s2_paper_ids → PHASE 2 → PHASE 3                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Rate Limit Math

```
S2 API: 1 request/second with API key = 86,400 requests/day

SEEDS (~450 papers):
  Phase 1 (Resolve):  450 requests = ~8 minutes
  Phase 2 (Fetch):    1 batch request = ~1 second
  Phase 3 (Classify): 450 papers = depends on LLM rate limits
  Phase 4 (Expand):   450 papers × 2 (citations + refs) = ~15 minutes

DAILY DISCOVER:
  Check 500 papers for new citations = ~17 minutes

WEEKLY UPDATE:
  Refresh metrics for 2000 papers = 4 batch requests = ~4 seconds
```

---

## Classification System

### Multi-Label + Tags Approach

Papers can have:
1. **1-3 OWASP labels** (ML01-ML10) - formal taxonomy
2. **1 paper type** (attack/defense/survey/etc)
3. **Multiple domain tags** (nlp, vision, etc)
4. **Multiple model tags** (llm, cnn, etc)
5. **Multiple free-form tags**

### OWASP ML Top 10 Categories

```
ML01 - INPUT MANIPULATION ATTACK
  Adversarial examples that fool models at INFERENCE time.
  ✓ adversarial examples, evasion, perturbations, prompt injection, jailbreaking
  ✗ attacks on training data (ML02)

ML02 - DATA POISONING ATTACK
  Corrupting TRAINING DATA to make models learn wrong behavior.
  ✓ backdoor attacks, trojans, label flipping, clean-label attacks
  ✗ manipulating model weights directly (ML10)

ML03 - MODEL INVERSION ATTACK
  RECONSTRUCTING sensitive training data by querying the model.
  ✓ attribute inference, training data reconstruction, property inference
  ✗ just determining if data was in training set (ML04)

ML04 - MEMBERSHIP INFERENCE ATTACK
  Determining WHETHER a specific record was in the training set.
  ✓ membership inference, privacy auditing
  ✗ reconstructing the actual data (ML03)

ML05 - MODEL THEFT
  Stealing the MODEL ITSELF - parameters, architecture, functionality.
  ✓ model extraction, model stealing, knowledge distillation attacks
  ✗ stealing training data (ML03/ML04)

ML06 - AI SUPPLY CHAIN ATTACKS
  Attacking the ML ECOSYSTEM - packages, platforms, model hubs.
  ✓ malicious packages, compromised pre-trained models, MLOps attacks
  ✗ attacks on the model itself (other categories)

ML07 - TRANSFER LEARNING ATTACK
  Exploiting TRANSFER LEARNING to inject malicious behavior.
  ✓ backdoored foundation models, malicious fine-tuning
  ✗ general backdoors not via transfer learning (ML02)

ML08 - MODEL SKEWING
  Manipulating FEEDBACK LOOPS in continuously learning systems.
  ✓ feedback loop attacks, online learning manipulation
  ✗ one-time training data poisoning (ML02)

ML09 - OUTPUT INTEGRITY ATTACK
  Tampering with model OUTPUTS after prediction.
  ✓ prediction tampering, result manipulation, MITM on inference
  ✗ manipulating inputs (ML01)

ML10 - MODEL POISONING
  Directly manipulating MODEL PARAMETERS/WEIGHTS.
  ✓ weight manipulation, neural trojan insertion into weights
  ✗ poisoning via training data (ML02)

NONE - NOT ML SECURITY
  ✓ General ML, using AI FOR security, traditional security
```

### Example Classifications

```yaml
Paper: "BadNets: Identifying Vulnerabilities in ML Model Supply Chain"
owasp_labels: [ML02, ML06]
paper_type: attack
domains: [vision]
model_types: [cnn]
tags: [backdoor, trojan, pre-trained-models]
reasoning: "Backdoor attack (ML02) targeting the model supply chain (ML06)"

Paper: "Extracting Training Data from Large Language Models"
owasp_labels: [ML03]
paper_type: attack
domains: [nlp]
model_types: [llm]
tags: [memorization, privacy, gpt]
reasoning: "Model inversion attack extracting training data from LLMs"

Paper: "SoK: Machine Learning Security"
owasp_labels: [ML01, ML02, ML03, ML04, ML05]
paper_type: survey
domains: [vision, nlp]
model_types: [cnn, transformer]
tags: [systematization, taxonomy]
reasoning: "Comprehensive survey covering multiple attack categories"
```

---

## Website Features

### Navigation Structure

```
BY CATEGORY (OWASP ML Top 10):
├── ML01 Input Manipulation
├── ML02 Data Poisoning
├── ... (all 10 categories)
└── Cross-category view

BY TYPE:
├── Attacks
├── Defenses
├── Surveys & SoKs
├── Benchmarks
└── Tools

BY DOMAIN:
├── NLP / LLMs
├── Computer Vision
├── Audio / Speech
├── Multimodal
└── Federated Learning

BY TIME:
├── This week / month / year
├── Trending (recent + growing citations)
├── Classics (pre-2020, highly cited)
└── Timeline view
```

### Rich Filtering UI

```
┌────────────────────────────────────────────────────────────────┐
│ Search: [                                        ] [🔍]        │
├────────────────────────────────────────────────────────────────┤
│ Categories: [×ML01] [×ML02] [ML03] [ML04] ...    ← toggle     │
│ Type:       [×Attack] [Defense] [Survey] [Tool]               │
│ Domain:     [×NLP] [Vision] [Audio] [All]                     │
│ Model:      [×LLM] [Transformer] [CNN] [All]                  │
│ Year:       [2020]────●────[2026]                ← slider     │
│ Citations:  [0]────●────────[1000+]              ← slider     │
└────────────────────────────────────────────────────────────────┘
```

### Paper Card Design

```
┌─────────────────────────────────────────────────────────────────┐
│ Extracting Training Data from Large Language Models             │
│ Carlini, Tramèr, Wallace, et al.                               │
│ USENIX Security 2021                                            │
├─────────────────────────────────────────────────────────────────┤
│ 🔥 892 citations (127 influential)                              │
├─────────────────────────────────────────────────────────────────┤
│ [ML03 Model Inversion]                        ← OWASP labels   │
├─────────────────────────────────────────────────────────────────┤
│ #LLM #GPT-2 #memorization #privacy #attack   ← tags            │
├─────────────────────────────────────────────────────────────────┤
│ TLDR: We demonstrate that large language models memorize and   │
│ emit training data, including PII, code, and URLs...           │
├─────────────────────────────────────────────────────────────────┤
│ [📄 PDF] [💻 Code] [📚 Cite] [🔗 S2] [Similar Papers]          │
└─────────────────────────────────────────────────────────────────┘
```

### Category Landing Pages

```
╔═════════════════════════════════════════════════════════════════╗
║  ML03: MODEL INVERSION ATTACK                                   ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  WHAT IS IT?                                                    ║
║  Attackers reconstruct sensitive training data by querying      ║
║  the model. They reverse-engineer private information.          ║
║                                                                  ║
║  REAL-WORLD IMPACT:                                             ║
║  • Facial recognition models leak faces                         ║
║  • Medical models leak patient data                             ║
║  • LLMs leak training text, PII, code                          ║
║                                                                  ║
║  SEMINAL PAPERS:              TOP DEFENSES:                     ║
║  • Fredrikson 2015            • Differential Privacy            ║
║  • Carlini 2021 (LLMs)        • Output perturbation            ║
║                                                                  ║
║  [View all 89 papers →]                                         ║
║                                                                  ║
║  RELATED: [ML04 Membership Inference] [ML05 Model Theft]        ║
╚═════════════════════════════════════════════════════════════════╝
```

### Visualizations

**Attack Landscape Graph:**
- Nodes = categories (size = paper count)
- Edges = papers with multiple labels

**Timeline View:**
- Papers plotted by year
- Highlight seminal papers
- Show research trends

**Trends Charts:**
- Papers per category per year
- Attack vs Defense ratio over time
- Domain distribution evolution
- Citation growth over time

### Learning Paths

```
🎓 NEW TO ML SECURITY?

Start Here:
1. "SoK: Machine Learning Security" (overview)
2. "Explaining and Harnessing Adversarial Examples" (foundational)
3. "Towards Evaluating the Robustness of Neural Networks" (attacks)

Then explore by interest:
├── Want to attack LLMs? → [LLM Attack Path]
├── Want to defend models? → [Defense Path]
├── Interested in privacy? → [Privacy Path]
└── Building secure ML? → [MLSecOps Path]
```

### Curated Collections

- "Must-read papers for ML security"
- "Best papers of 2024"
- "Papers with code"
- "Industry-relevant attacks"
- "Beginner-friendly explanations"
- Community-submitted collections

### Insights Dashboard

- "X% of papers are attacks, Y% are defenses"
- "LLM security grew 400% in 2023"
- "Most under-researched area: ML08 Model Skewing"
- "Top venues: USENIX, S&P, NeurIPS"
- Auto-generated monthly digest

---

## LLM Prompt Design

### Prompt Template Location

```
configs/
├── prompts/
│   └── classification.md     # Full prompt template
├── categories.yaml           # OWASP category definitions
└── tags.yaml                 # Controlled vocabulary
```

### Classification Prompt

See `configs/prompts/classification.md` for full prompt.

**Input to LLM:**
```
TITLE: {title}
TLDR: {tldr}
ABSTRACT: {abstract}
VENUE: {venue}
YEAR: {year}
FIELDS OF STUDY: {fields_of_study}
PUBLICATION TYPE: {publication_types}
```

**Expected Output:**
```json
{
  "owasp_labels": ["ML02", "ML07"],
  "paper_type": "attack",
  "domains": ["nlp"],
  "model_types": ["llm", "transformer"],
  "tags": ["backdoor", "transfer-learning", "fine-tuning"],
  "confidence": "HIGH",
  "reasoning": "Paper presents backdoor attack (ML02) that exploits transfer learning pipeline (ML07), targeting transformer-based LLMs."
}
```

---

## API & Data Sources

### Semantic Scholar API

**Base URL:** `https://api.semanticscholar.org/graph/v1`

**Key Endpoints:**
| Endpoint | Purpose | Rate |
|----------|---------|------|
| `/paper/search/match` | Find paper by title | 1/sec |
| `/paper/batch` | Get up to 500 papers | 1/sec |
| `/paper/{id}` | Get single paper | 1/sec |
| `/paper/{id}/citations` | Papers citing this | 1/sec |
| `/paper/{id}/references` | Papers this cites | 1/sec |

**Available Fields:**
- paperId, corpusId, externalIds
- title, abstract, tldr
- venue, year, publicationDate
- authors, fieldsOfStudy, publicationTypes
- citationCount, influentialCitationCount, referenceCount
- openAccessPdf, url

### LLM Providers

| Provider | Model | Rate Limit | Cost |
|----------|-------|------------|------|
| Cerebras | llama-3.3-70b | Free tier limited | Free |
| Groq | llama-3.3-70b | 30 req/min? | Free |
| Google | gemini-2.0-flash | Daily quota | Free |

---

## Open Questions

### Classification
- [ ] Min/max OWASP labels per paper? (suggest: 1-3)
- [ ] Controlled vocab for tags, or free-form + normalize?
- [ ] Re-classify if paper gets influential citations later?
- [ ] Human review for low-confidence classifications?

### Website
- [ ] How to count papers per category with multi-label?
- [ ] Show "primary" label or treat all equally?
- [ ] User accounts for saving papers / collections?
- [ ] API for programmatic access?

### Data
- [ ] Include preprints or only peer-reviewed?
- [ ] Minimum citation threshold for expansion?
- [ ] How far to expand graph? (depth limit)
- [ ] Include non-English papers?

### Operations
- [ ] How often to re-classify with improved prompts?
- [ ] Backup / versioning strategy for data?
- [ ] Monitoring for API failures?

---

## File Structure

```
ml-security-papers/
├── configs/
│   ├── prompts/
│   │   └── classification.md
│   ├── categories.yaml
│   └── tags.yaml
├── scripts/
│   └── pipeline/
│       ├── resolve.py      # title → s2_paper_id
│       ├── fetch.py        # s2_paper_id → full metadata
│       ├── classify.py     # metadata → labels + tags
│       ├── expand.py       # get citations/references
│       ├── discover.py     # find new papers daily
│       ├── update.py       # refresh citation counts
│       ├── export.py       # generate website JSON
│       └── state.py        # paper state management
├── data/
│   ├── paper_state.json    # all papers + status
│   ├── seeds.json          # original seed titles
│   ├── manifest.json       # website metadata
│   └── papers/
│       ├── ml01.json
│       └── ...
├── web/
│   ├── index.html
│   ├── css/
│   └── js/
├── docs/
│   ├── DESIGN.md           # this file
│   └── ARCHITECTURE.md
└── .github/
    └── workflows/
        └── update-papers.yml
```

---

## What Makes It "Best"

1. **COMPREHENSIVE** - Every ML security paper, not just famous ones
2. **ORGANIZED** - OWASP taxonomy + rich multi-label tags
3. **DISCOVERABLE** - Search, filter, visualize, explore
4. **ACTIONABLE** - PDFs, code, citations ready
5. **CURRENT** - Daily updates, trending papers
6. **EDUCATIONAL** - Learning paths, explanations, curated collections
7. **QUALITY-RANKED** - Influential citations, not just counts
8. **BEAUTIFUL** - Clean, fast, delightful UX
