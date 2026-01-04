# Model Stealing Paper Collection Strategy

## Current Problems

### 1. False Positive Keywords (Remove These)

**High False Positive Rate (>10x off-topic vs relevant):**
- ❌ `electromagnetic analysis` - 81 false positives, 0 relevant
- ❌ `electromagnetic neural network` - About EM analysis, NOT model stealing
- ❌ `power analysis neural network` - About power consumption analysis
- ❌ `DNN weights leakage` - Too vague, matches unrelated papers
- ❌ `side-channel attack` (when standalone) - Too broad
- ❌ `imitation attack` - 13:1 false positive ratio
- ❌ `(via citation)` - Only mentions in references, not actual content

**Title-only matches are problematic:**
- `model stealing (title)` - Matches "prompt stealing", "link stealing", "data stealing"
- These need abstract verification

### 2. Ambiguous Keywords (Need Context)

These match both relevant and off-topic papers:
- ⚠️ `model theft` - 1.54x more off-topic (often in watermarking papers)
- ⚠️ `side-channel model extraction` - Only relevant if PRIMARY focus
- ⚠️ `reverse engineer neural network` - Often about understanding, not attacking

### 3. Best Keywords (Keep These)

**High precision keywords:**
- ✅ `model extraction attack` - 2.7:1 relevant ratio (best)
- ✅ `clone model` - Strong signal
- ✅ `cloning attack` - Strong signal
- ✅ `model stealing attack` - Good precision
- ✅ `model extraction` - Good general term
- ✅ `model stealing` - Good general term
- ✅ `knockoff nets` - Very specific to the field
- ✅ `copycat CNN` / `copycat model` - Specific terminology
- ✅ `functionality stealing` - Good signal

**Defensive keywords (also relevant):**
- ✅ `model stealing defense`
- ✅ `model extraction defense`
- ✅ `prevent model stealing`

## Recommended Filtering Strategy

### Phase 1: Keyword Refinement

**Remove from keyword list:**
```
- electromagnetic analysis (all variants)
- electromagnetic neural network
- power analysis neural network
- cache attack DNN
- timing attack neural network
- DNN weights leakage
- imitation attack
- side-channel neural network (too broad)
```

**Keep core keywords:**
```
- model stealing attack
- model extraction attack
- model stealing
- model extraction
- steal ML model
- extract model
- clone model
- cloning attack
- knockoff nets
- copycat CNN
- copycat model
- functionality stealing
- black-box model stealing
- query-based model stealing
- API model extraction
- prediction API stealing
```

### Phase 2: Multi-Stage Filtering

**Stage 1: Initial keyword match** (Semantic Scholar/ArXiv search)
- Use refined keyword list above
- Search in: title, abstract, keywords

**Stage 2: Abstract verification** (Automatic)
Required criteria:
1. Abstract must exist
2. Abstract must contain at least one core term:
   - "model stealing" OR "model extraction" OR "steal" + "model"
   - "clone" + "model" OR "knockoff" OR "copycat"
3. Abstract should NOT primarily focus on:
   - "watermark" (unless explicitly about model stealing)
   - "membership inference" (different attack)
   - "data privacy" without model discussion
   - "prompt" stealing (not model stealing)
   - "link" stealing (graph attacks, not model)

**Stage 3: Context analysis** (Automatic or semi-automatic)
Check abstract for PRIMARY focus indicators:

**Positive signals (likely relevant):**
- "extract the model", "steal the model", "clone the model"
- "query the victim model", "replicate functionality"
- "black-box access", "API queries" + extraction/stealing
- "surrogate model", "substitute model" in stealing context
- "teacher-student" in adversarial context
- "model fidelity", "model agreement" in attack context

**Negative signals (likely off-topic):**
- "watermark" + "protect" (unless evaluating against stealing)
- "adversarial example" without model extraction
- "backdoor" without model extraction
- "membership inference" as primary topic
- "differential privacy" as primary topic
- "federated learning" unless explicitly about model extraction
- "prompt stealing" / "prompt template"
- "link stealing" / "graph stealing"

### Phase 3: Manual Curation

**Review queue priorities:**
1. Papers with only title matches (no abstract match)
2. Papers from 2024+ (recent, high impact)
3. Papers with high citation counts
4. Papers from top venues

**Quick manual filters:**
- Does the abstract's first sentence mention model stealing/extraction?
- Is the main contribution about stealing/extracting/cloning models?
- Is it a defense whose evaluation includes model stealing attacks?

## Implementation Recommendations

### Option 1: Strict Filtering (Higher Precision)
```python
def is_relevant_strict(paper):
    abstract = paper.get('abstract', '').lower()

    # Must have abstract
    if not abstract:
        return False

    # Must mention core concepts
    core_terms = ['model stealing', 'model extraction', 'steal model',
                  'extract model', 'clone model', 'knockoff']
    if not any(term in abstract for term in core_terms):
        return False

    # Exclude primary focus on other topics
    exclude_primary = {
        'watermark': abstract.count('watermark') > 3,
        'membership inference': 'membership inference' in abstract,
        'prompt stealing': 'prompt' in abstract and 'steal' in abstract,
        'link stealing': 'link stealing' in abstract,
    }

    if any(exclude_primary.values()):
        return False

    return True
```

### Option 2: Semantic Filtering (Use LLM)
For each paper, ask an LLM:
```
Title: {title}
Abstract: {abstract}

Is this paper primarily about:
A) Stealing/extracting/cloning machine learning models
B) Defending against model stealing/extraction attacks
C) Other topic (specify)

Answer: (A/B/C)
```

### Option 3: Hybrid Approach (Recommended)
1. Use keyword search with refined list
2. Apply automatic filters (remove no-abstract, obvious false positives)
3. Use LLM to classify remaining papers
4. Manual spot-check of uncertain cases

## Validation Strategy

Test your filtering on known papers:

**Should INCLUDE:**
- "Stealing Machine Learning Models via Prediction APIs" (Tramèr 2016)
- "Knockoff Nets: Stealing Functionality of Black-Box Models" (2018)
- "Thieves on Sesame Street!" (2019)
- "CloudLeak: Large-Scale Deep Learning Models Stealing" (2020)
- "ActiveThief: Model Extraction Using Active Learning" (2020)

**Should EXCLUDE:**
- Pure watermarking papers (unless they evaluate against stealing)
- Prompt stealing papers
- Link/graph stealing papers
- Membership inference papers
- Pure adversarial example papers
- Federated learning papers (unless about model extraction)

## Metrics to Track

- **Precision**: % of collected papers that are truly about model stealing
- **Recall**: % of known model stealing papers that are collected
- **Category breakdown**: Attack vs Defense vs Survey
- **Venue quality**: Conference tier, journal impact factor

Target: >80% precision, >90% recall on seed papers
