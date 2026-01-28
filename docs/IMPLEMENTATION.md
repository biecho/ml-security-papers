# Implementation Plan

## Overview

This document details the technical implementation to transform the current paper collection into a research intelligence platform.

---

## Phase 1: Pipeline Upgrade

### Goal
Store rich classification data (paper_type, domains, model_types) for all papers.

### Current State

```
classify.py (now):
├── Uses inline SYSTEM_PROMPT
├── Prompt says: "Respond with ONLY the category code"
├── max_tokens: 10
├── Returns: "ML01"
└── Stores: classification="ML01", classification_confidence="HIGH"
```

### Target State

```
classify.py (after):
├── Loads configs/prompts/classification.md
├── Prompt returns full JSON
├── max_tokens: 500
├── Returns: {"owasp_labels": [...], "paper_type": "attack", ...}
└── Stores: owasp_labels, paper_type, domains, model_types, tags, reasoning
```

### Files to Modify

#### 1. `scripts/pipeline/state.py`

Update `set_classified` to accept and store all fields:

```python
def set_classified(self, paper_id: str, classification_result: dict):
    """
    Store rich classification result.

    classification_result = {
        "owasp_labels": ["ML01", "ML02"],
        "paper_type": "attack",
        "domains": ["vision", "nlp"],
        "model_types": ["cnn", "transformer"],
        "tags": ["backdoor", "physical-attack"],
        "confidence": "HIGH",
        "reasoning": "This paper..."
    }
    """
    paper = self.papers[paper_id]

    # Store all classification fields
    paper["owasp_labels"] = classification_result["owasp_labels"]
    paper["paper_type"] = classification_result["paper_type"]
    paper["domains"] = classification_result.get("domains", [])
    paper["model_types"] = classification_result.get("model_types", [])
    paper["tags"] = classification_result.get("tags", [])
    paper["classification_confidence"] = classification_result["confidence"]
    paper["classification_reasoning"] = classification_result.get("reasoning", "")

    # Legacy field for backward compat
    paper["classification"] = classification_result["owasp_labels"][0] if classification_result["owasp_labels"] else "NONE"

    # Update status
    paper["status"] = "classified" if paper["owasp_labels"][0] != "NONE" else "discarded"
    paper["classified_at"] = datetime.now().isoformat()
```

#### 2. `scripts/pipeline/classify.py`

Major changes:

```python
# Load rich prompt from file
def load_prompt():
    prompt_path = Path(__file__).parent.parent.parent / "configs/prompts/classification.md"
    with open(prompt_path) as f:
        content = f.read()
    # Extract system prompt section
    # ... parse markdown to get system prompt and user template
    return system_prompt, user_template

# Update classify function
def classify_with_llm(title: str, abstract: str = None, provider: str = "cerebras") -> dict:
    """
    Returns full classification dict, not just category string.
    """
    system_prompt, user_template = load_prompt()

    user_message = user_template.format(
        title=title,
        abstract=abstract or "(No abstract available)",
        # ... other fields
    )

    # Call LLM with higher max_tokens
    response = call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=500,  # Was 10
        provider=provider
    )

    # Parse JSON response
    result = parse_classification_response(response)
    return result

def parse_classification_response(response: str) -> dict:
    """Parse LLM JSON response, handle edge cases."""
    # Try to extract JSON from response
    # Handle markdown code blocks, extra text, etc.
    try:
        # Find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass

    # Fallback: return minimal valid result
    return {
        "owasp_labels": ["NONE"],
        "paper_type": "unknown",
        "domains": [],
        "model_types": [],
        "tags": [],
        "confidence": "LOW",
        "reasoning": f"Failed to parse: {response[:100]}"
    }
```

#### 3. `scripts/pipeline/export.py`

Update to export all fields:

```python
def export_paper(paper: dict) -> dict:
    """Export paper with full classification data."""
    return {
        "paper_id": paper["paper_id"],
        "title": paper["title"],
        "abstract": paper.get("abstract", ""),
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "authors": paper.get("authors", []),
        "url": paper.get("url"),
        "pdf_url": paper.get("pdf_url"),
        "cited_by_count": paper.get("cited_by_count", 0),

        # Rich classification (NEW)
        "owasp_labels": paper.get("owasp_labels", []),
        "paper_type": paper.get("paper_type", "unknown"),
        "domains": paper.get("domains", []),
        "model_types": paper.get("model_types", []),
        "tags": paper.get("tags", []),
        "classification_confidence": paper.get("classification_confidence", "LOW"),
    }
```

---

## Phase 2: Analytics Pipeline

### New Script: `scripts/pipeline/analyze.py`

Computes all analytics from classified papers.

```python
#!/usr/bin/env python3
"""
Compute analytics from classified papers.

Generates:
- attack_defense_balance.json
- domain_category_matrix.json
- temporal_trends.json
- gaps.json
"""

def compute_attack_defense_balance(papers: list) -> dict:
    """Count attacks vs defenses per category."""
    balance = {f"ML{i:02d}": {"attack": 0, "defense": 0, "other": 0}
               for i in range(1, 11)}

    for paper in papers:
        for label in paper.get("owasp_labels", []):
            if label in balance:
                paper_type = paper.get("paper_type", "other")
                if paper_type in ["attack", "defense"]:
                    balance[label][paper_type] += 1
                else:
                    balance[label]["other"] += 1

    # Compute ratios
    for cat, counts in balance.items():
        attacks = counts["attack"]
        defenses = counts["defense"]
        counts["ratio"] = attacks / defenses if defenses > 0 else None
        counts["total"] = attacks + defenses + counts["other"]

    return balance

def compute_domain_matrix(papers: list) -> dict:
    """Build domain × category matrix."""
    categories = [f"ML{i:02d}" for i in range(1, 11)]
    domains = ["vision", "nlp", "llm", "audio", "tabular",
               "multimodal", "graph", "reinforcement-learning",
               "federated-learning", "generative"]

    matrix = {cat: {dom: 0 for dom in domains} for cat in categories}

    for paper in papers:
        for label in paper.get("owasp_labels", []):
            if label in matrix:
                for domain in paper.get("domains", []):
                    if domain in matrix[label]:
                        matrix[label][domain] += 1

    return {"matrix": matrix, "categories": categories, "domains": domains}

def compute_gaps(papers: list, balance: dict, matrix: dict) -> list:
    """Identify and score research gaps."""
    gaps = []

    # Empty categories
    for cat, counts in balance.items():
        if counts["total"] == 0:
            gaps.append({
                "id": f"empty-{cat}",
                "type": "empty_category",
                "title": f"{cat}: Entire Category Unexplored",
                "category": cat,
                "score": 95,
                "description": "Zero papers exist in this OWASP category.",
                "recommendation": "First-mover advantage in officially recognized threat."
            })

    # Defense deficits
    for cat, counts in balance.items():
        if counts["attack"] > 0 and counts["ratio"] and counts["ratio"] > 2:
            score = min(95, 70 + counts["ratio"] * 3)
            gaps.append({
                "id": f"defense-{cat}",
                "type": "defense_deficit",
                "title": f"{cat}: Defense Gap",
                "category": cat,
                "score": int(score),
                "attack_count": counts["attack"],
                "defense_count": counts["defense"],
                "ratio": round(counts["ratio"], 1),
                "description": f"{counts['attack']} attack papers vs {counts['defense']} defense papers.",
                "recommendation": "High-impact area for defense research."
            })

    # Domain gaps
    domain_totals = {}
    for cat_data in matrix["matrix"].values():
        for dom, count in cat_data.items():
            domain_totals[dom] = domain_totals.get(dom, 0) + count

    max_domain = max(domain_totals.values()) if domain_totals else 1
    for dom, total in domain_totals.items():
        if total < max_domain * 0.1:  # Less than 10% of max
            score = int(85 * (1 - total / max_domain))
            gaps.append({
                "id": f"domain-{dom}",
                "type": "domain_gap",
                "title": f"Domain Gap: {dom.replace('-', ' ').title()}",
                "domain": dom,
                "score": score,
                "paper_count": total,
                "max_domain_count": max_domain,
                "description": f"Only {total} papers vs {max_domain} in most-studied domain.",
                "recommendation": f"Security of {dom} models is underexplored."
            })

    # Sort by score
    gaps.sort(key=lambda g: g["score"], reverse=True)
    return gaps

def main():
    # Load papers
    state = PaperState(Path("data/paper_state.json"))
    papers = [p for p in state.papers.values()
              if p.get("status") == "classified"]

    # Compute analytics
    balance = compute_attack_defense_balance(papers)
    matrix = compute_domain_matrix(papers)
    gaps = compute_gaps(papers, balance, matrix)

    # Write output files
    output_dir = Path("data")

    with open(output_dir / "attack_defense_balance.json", "w") as f:
        json.dump(balance, f, indent=2)

    with open(output_dir / "domain_category_matrix.json", "w") as f:
        json.dump(matrix, f, indent=2)

    with open(output_dir / "gaps.json", "w") as f:
        json.dump({"gaps": gaps, "generated_at": datetime.now().isoformat()}, f, indent=2)

    print(f"Generated analytics for {len(papers)} papers")
    print(f"Found {len(gaps)} research gaps")
```

---

## Phase 3: Website

### Structure

```
web/
├── index.html          # Dashboard with OWASP grid + top gaps
├── gaps.html           # Gap explorer with filters
├── category/
│   └── [id].html       # Category detail pages (or dynamic)
├── css/
│   └── style.css       # Tailwind or custom
├── js/
│   ├── app.js          # Main application logic
│   ├── dashboard.js    # Homepage components
│   ├── gaps.js         # Gap explorer logic
│   └── charts.js       # D3/Plotly visualizations
└── data/               # Symlink or copy from /data
    ├── papers.json
    ├── gaps.json
    └── ...
```

### Key Components

#### OWASP Grid (Homepage)

```javascript
function renderOWASPGrid(manifest) {
    const categories = [
        {id: "ML01", name: "Input Manipulation", color: "#ef4444"},
        {id: "ML02", name: "Data Poisoning", color: "#f97316"},
        // ...
    ];

    return categories.map(cat => `
        <a href="/category/${cat.id}" class="category-card"
           style="--cat-color: ${cat.color}">
            <div class="category-id">${cat.id}</div>
            <div class="category-count">${manifest.category_counts[cat.id] || 0}</div>
            <div class="category-name">${cat.name}</div>
            <div class="category-bar" style="width: ${getBarWidth(cat)}%"></div>
        </a>
    `).join('');
}
```

#### Gap Cards

```javascript
function renderGapCard(gap) {
    const typeIcons = {
        empty_category: "🔴",
        defense_deficit: "🛡️",
        domain_gap: "🌐",
        model_gap: "🤖"
    };

    return `
        <div class="gap-card" data-score="${gap.score}">
            <div class="gap-header">
                <span class="gap-icon">${typeIcons[gap.type]}</span>
                <span class="gap-score">${gap.score}</span>
            </div>
            <h3 class="gap-title">${gap.title}</h3>
            <p class="gap-description">${gap.description}</p>
            <p class="gap-recommendation">${gap.recommendation}</p>
            <a href="/papers?gap=${gap.id}" class="gap-link">Explore →</a>
        </div>
    `;
}
```

#### Domain × Category Heatmap

```javascript
function renderHeatmap(matrix) {
    // Use D3.js or Plotly
    const data = [{
        z: matrix.categories.map(cat =>
            matrix.domains.map(dom => matrix.matrix[cat][dom])
        ),
        x: matrix.domains,
        y: matrix.categories,
        type: 'heatmap',
        colorscale: 'Blues',
        showscale: true
    }];

    Plotly.newPlot('heatmap', data, {
        title: 'Domain × Category Coverage',
        annotations: generateAnnotations(matrix)  // Show counts in cells
    });
}
```

---

## Testing Strategy

### Unit Tests

```python
# test_classify.py
def test_parse_valid_json():
    response = '{"owasp_labels": ["ML01"], "paper_type": "attack", ...}'
    result = parse_classification_response(response)
    assert result["owasp_labels"] == ["ML01"]
    assert result["paper_type"] == "attack"

def test_parse_with_markdown():
    response = '```json\n{"owasp_labels": ["ML02"]}\n```'
    result = parse_classification_response(response)
    assert result["owasp_labels"] == ["ML02"]

def test_parse_invalid_fallback():
    response = "I think this is ML01 because..."
    result = parse_classification_response(response)
    assert result["owasp_labels"] == ["NONE"]
    assert result["confidence"] == "LOW"
```

### Integration Tests

```bash
# Test full pipeline on 5 papers
python scripts/pipeline/classify.py --limit 5 --provider cerebras

# Verify state file has new fields
python -c "
import json
with open('data/paper_state.json') as f:
    d = json.load(f)
for pid, p in list(d['papers'].items())[:5]:
    if p.get('status') == 'classified':
        assert 'owasp_labels' in p, f'{pid} missing owasp_labels'
        assert 'paper_type' in p, f'{pid} missing paper_type'
        print(f'{pid}: {p[\"paper_type\"]} - {p[\"owasp_labels\"]}')"
```

### Quality Checks

After re-classification, verify distributions make sense:

```python
# Expected rough distribution
# paper_type: ~60% attack, ~25% defense, ~15% other
# domains: vision > nlp > llm > others
# Most papers should have HIGH confidence
```

---

## Rollout Plan

### Step 1: Implement & Test (Day 1-2)
- [ ] Update state.py
- [ ] Update classify.py
- [ ] Test on 10 papers
- [ ] Fix edge cases

### Step 2: Re-classify (Day 3)
- [ ] Backup current paper_state.json
- [ ] Reset classified papers to "fetched" status
- [ ] Run classifier on all papers
- [ ] Verify output quality

### Step 3: Analytics (Day 4)
- [ ] Implement analyze.py
- [ ] Generate all analytics JSON
- [ ] Validate numbers

### Step 4: Export (Day 5)
- [ ] Update export.py
- [ ] Generate papers.json with all fields
- [ ] Verify format

### Step 5: Website (Day 6-10)
- [ ] Build dashboard
- [ ] Build gap explorer
- [ ] Deploy to GitHub Pages

---

## Cost Estimate

| Item | Cost |
|------|------|
| Re-classify 309 papers | ~$3 (Cerebras/Groq free tier may cover) |
| Hosting | $0 (GitHub Pages) |
| Domain (optional) | ~$12/year |
| **Total** | **~$3-15** |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM returns invalid JSON | Robust parsing with fallbacks |
| Classification quality varies | Sample verification, iterate on prompt |
| Rate limiting | Exponential backoff, checkpointing |
| Scope creep | Phase 1 is MVP, ship before adding |
