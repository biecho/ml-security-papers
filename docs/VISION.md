# ML Security Papers: Research Intelligence Platform

> **See the shape of the field. Find the gaps. Start your research 6 months faster.**

---

## What We're Building

The world's best tool for understanding the ML security research landscape and finding research gaps.

Not a paper database. A **research intelligence platform** that answers:

> "Where should I focus my research to have the most impact?"

---

## The Problem

The ML security field is invisible to newcomers:

- **2,000+ papers** scattered across venues
- **No map** of what's been done vs. what's missing
- **Researchers waste months** discovering the landscape

A PhD student today:
```
Month 1-3: Read random papers, build mental model
Month 4-5: Think they found a gap, discover it's covered
Month 6:   Finally find actual gap by accident
```

With our platform:
```
Hour 1: See the landscape (categories, coverage, trends)
Hour 2: Explore gaps (defense deficits, empty domains)
Hour 3: Deep-dive papers in chosen gap
Hour 4: Start writing
```

**We compress 6 months of literature review into hours.**

---

## Target User

**The Researcher** starting or pivoting into ML security.

Their core question: *"Where are the gaps in the literature?"*

---

## The Three Views

### 1. The Landscape (Homepage)

**Question:** "What does ML security research look like?"

Shows the OWASP ML Top 10 at a glance:

```
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│ML01 │ │ML02 │ │ML03 │ │ML04 │ │ML05 │
│ 117 │ │  69 │ │  45 │ │  43 │ │  22 │
│████ │ │███  │ │██   │ │██   │ │█    │
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│ML06 │ │ML07 │ │ML08 │ │ML09 │ │ML10 │
│   2 │ │   3 │ │   0 │ │   2 │ │   6 │
│░    │ │░    │ │     │ │░    │ │░    │
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘

████ Crowded    ░░░░ Sparse    [empty] Open
```

User learns in 5 seconds:
- ML01 (adversarial examples) is crowded
- ML08 (model skewing) is completely empty
- Categories 6-10 are underexplored

### 2. The Gaps (Gap Explorer)

**Question:** "Where are the research opportunities?"

Ranked list of gaps with scores:

| Rank | Gap | Score | Why |
|------|-----|-------|-----|
| 1 | ML08: Model Skewing | 94 | 0 papers. Entire category unexplored. |
| 2 | Model Theft Defenses | 87 | 18 attacks vs 4 defenses (4.5:1) |
| 3 | Audio Domain | 82 | 12 papers vs 156 in vision |
| 4 | Diffusion Models | 78 | 3 papers. Adoption +340% YoY. |

Gap types:
- **Empty categories** - 0 papers in OWASP category
- **Defense deficits** - many attacks, few defenses
- **Domain gaps** - underexplored application areas (audio, RL, graphs)
- **Model gaps** - new architectures without security research

### 3. The Matrix (Deep Analysis)

**Question:** "What combinations haven't been studied?"

Interactive heatmap: Domain × Category

```
              │Vision│ NLP │ LLM │Audio│  RL │Graph│
──────────────┼──────┼─────┼─────┼─────┼─────┼─────┤
ML01 Input    │ ████ │ ███ │ ██  │ █   │     │     │
ML02 Poison   │ ███  │ ██  │ █   │     │     │     │
ML03 Inversion│ ██   │ █   │ █   │     │     │     │
ML04 Member   │ ██   │ █   │ █   │     │     │     │
ML05 Theft    │ █    │ █   │ █   │     │     │     │
...
```

Click empty cell → "No papers exist. Research opportunity!"

---

## Data Model

Each paper needs:

```yaml
# Identity
paper_id: "openalex:W123..."
title: "Adversarial Examples for..."
authors: ["Alice", "Bob"]
year: 2024
venue: "IEEE S&P"

# Content
abstract: "We present..."

# Metrics
cited_by_count: 542

# Classification (the key enrichment)
owasp_labels: ["ML01", "ML02"]     # Multi-label categories
paper_type: "attack"               # attack | defense | survey | benchmark | tool
domains: ["vision", "nlp"]         # What application domains
model_types: ["cnn", "transformer"] # What model architectures
```

From this we compute:
- Attack/defense balance per category
- Domain × category coverage matrix
- Temporal trends
- Gap scores

---

## Gap Scoring Algorithm

```python
def score_gap(gap):
    if gap.type == "empty_category":
        return 95  # Entire OWASP category open

    if gap.type == "defense_deficit":
        ratio = gap.attacks / max(gap.defenses, 1)
        return min(95, 70 + ratio * 5)  # 70-95

    if gap.type == "domain_gap":
        coverage = gap.papers / max_domain_papers
        return int(90 * (1 - coverage))  # 0-90

    if gap.type == "model_gap":
        return min(90, 30 / max(gap.papers, 1) + gap.trend * 0.5)
```

---

## Technical Architecture

### Static-First

- **Hosting:** GitHub Pages (free, fast)
- **Data:** Pre-computed JSON files
- **Frontend:** Vanilla JS + Tailwind (or lightweight React)
- **Charts:** D3.js or Plotly

All analytics computed offline by pipeline. Website is pure visualization.

### Pipeline Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Fetch   │ ──▶ │Classify │ ──▶ │ Analyze │ ──▶ │ Export  │
│ (S2 API)│     │  (LLM)  │     │ (Python)│     │ (JSON)  │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                     │
                     ▼
              ┌─────────────┐
              │ Rich JSON:  │
              │ paper_type  │
              │ domains[]   │
              │ model_types│
              └─────────────┘
```

### Pre-computed Analytics Files

```
data/
├── papers.json                  # All papers with full classification
├── manifest.json                # Summary stats
├── attack_defense_balance.json  # Per-category attack/defense counts
├── domain_category_matrix.json  # Coverage heatmap data
├── temporal_trends.json         # Papers by year by category
└── gaps.json                    # Ranked research opportunities
```

---

## Current State

| Component | Status |
|-----------|--------|
| Paper collection | ✅ 309 classified, 2,349 tracked |
| OWASP taxonomy | ✅ ML01-ML10 defined |
| Classification prompt | ✅ Rich prompt exists in `configs/prompts/classification.md` |
| Pipeline storage | ❌ Only stores single category, drops rich data |
| Analytics | ❌ Not built |
| Gap detection | ❌ Not built |
| Website | ❌ Basic, no gap visualization |

### The Bottleneck

`classify.py` uses a simple prompt returning only "ML01".

The rich prompt (paper_type, domains, model_types) exists but **isn't connected**.

---

## Implementation Roadmap

### Phase 1: Fix the Pipeline (Week 1)

1. **Upgrade classify.py** - use rich prompt, parse JSON response
2. **Update state.py** - store all classification fields
3. **Re-classify papers** - run on all 309 with rich prompt
4. **Update export.py** - output all fields

**Deliverable:** `papers.json` with paper_type, domains, model_types for all papers.

### Phase 2: Build Analytics (Week 2)

1. **Create analyze.py** - compute matrices and gap scores
2. **Generate analytics JSON** - balance, matrix, trends, gaps
3. **Validate output** - sanity check numbers

**Deliverable:** Pre-computed analytics files ready for visualization.

### Phase 3: Build UI (Week 3-4)

1. **Dashboard homepage** - OWASP grid, top gaps, stats
2. **Gap explorer page** - ranked gaps with filters
3. **Category pages** - deep-dive per category
4. **Interactive matrix** - domain × category heatmap

**Deliverable:** Working website showing research landscape and gaps.

### Phase 4: Polish (Week 5+)

1. **Temporal trends** - sparklines, YoY growth
2. **Citation analysis** - network visualization
3. **Export features** - BibTeX, reading lists
4. **Mobile optimization**

---

## Success Criteria

We've succeeded when:

1. A PhD student finds their thesis direction in one afternoon
2. Papers cite our analysis: "According to [ML Security Papers], this area is underexplored..."
3. Course syllabi link to us for research direction
4. We predict a gap, papers emerge there within 12 months

---

## What We're NOT Building

- **Paper recommendations** - not a recommender system
- **Full-text search** - Google Scholar does this
- **Social features** - no accounts, comments, ratings
- **PDF hosting** - link to originals
- **Writing assistance** - not an AI tool

We do ONE thing: **reveal the structure of the field**.

---

## Next Step

**Upgrade `classify.py`** to use the rich prompt and store all fields.

See: [Implementation Details](./IMPLEMENTATION.md)
