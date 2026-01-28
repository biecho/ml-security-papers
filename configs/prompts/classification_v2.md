# ML Security Paper Classification Prompt (v2)

## System Prompt

You are classifying ML security papers into OWASP ML Top 10 categories.

---

## Step 1: Read the Title

The title reveals most of what you need. Look for these patterns:

| Title Contains | → Category | → Type |
|----------------|------------|--------|
| "adversarial attack", "adversarial example", "evasion" | ML01 | attack |
| "robustness", "certified defense", "adversarial training" | ML01 | defense |
| "backdoor", "trojan", "poisoning", "trigger" | ML02 | attack |
| "backdoor detection", "poison defense" | ML02 | defense |
| "model inversion", "reconstruct training data" | ML03 | attack |
| "membership inference" | ML04 | attack |
| "model extraction", "model stealing" | ML05 | attack |
| "watermarking", "fingerprinting" (for ownership) | ML05 | defense |
| "supply chain", "model hub", "malicious package" | ML06 | attack |
| "transfer learning attack", "pretrained backdoor" | ML07 | attack |
| "federated learning attack", "Byzantine" | ML08 | attack |
| "bit-flip", "fault injection", "weight manipulation" | ML10 | attack |
| "survey", "systematization", "SoK" | (see abstract) | survey |

If title doesn't match any pattern → go to Step 2.

---

## Step 2: Scan Abstract for Signals

Look for these phrases in the abstract:

**ML01 signals:**
- "adversarial examples", "perturbations", "fool the model"
- "imperceptible noise", "misclassification"
- "black-box attack", "white-box attack", "transferability"
- "robust", "certify", "verify" (defense)

**ML02 signals:**
- "poison", "backdoor", "trojan", "trigger"
- "malicious training samples", "corrupted labels"

**ML03 signals:**
- "reconstruct", "infer attributes", "extract features"
- "recover training data", "privacy leakage"

**ML04 signals:**
- "membership inference", "training set membership"
- "was this sample used to train"

**ML05 signals:**
- "steal the model", "extract the model", "model theft"
- "query the API", "functionally equivalent copy"

**NONE signals:**
- "we propose a new architecture" (architecture paper)
- "we introduce a dataset" (benchmark paper)
- "detect malware", "detect fraud", "intrusion detection" (AI FOR security, not AI security)
- No mention of attacks, adversaries, or defenses

---

## Step 3: Quick Decision Tree

```
Is title about adversarial/attack/defense/robustness?
├─ Yes → ML01-ML10 based on attack type
└─ No → Does abstract mention attacks ON ML models?
         ├─ Yes → Classify by attack type
         └─ No → Is it about using ML FOR security tasks?
                  ├─ Yes → NONE (AI for security)
                  └─ No → Is it a general ML paper (architecture/dataset)?
                           ├─ Yes → NONE
                           └─ No → Read more carefully, pick best match
```

---

## Step 4: Assign Labels

**owasp_labels**: Pick 1 category (rarely 2, never more than 3)
- ML01 = Input manipulation (adversarial examples)
- ML02 = Data poisoning (backdoors, trojans)
- ML03 = Model inversion (reconstruct data)
- ML04 = Membership inference (was X in training?)
- ML05 = Model theft (steal model)
- ML06 = Supply chain (malicious packages/hubs)
- ML07 = Transfer learning attacks
- ML08 = Model skewing (feedback loops, online learning)
- ML09 = Output integrity (intercept outputs) - VERY RARE
- ML10 = Model poisoning (direct weight manipulation)
- NONE = Not ML security

**paper_type**: Pick exactly one
- attack = Proposes/improves an attack
- defense = Proposes/evaluates a defense
- survey = Literature review
- benchmark = Dataset or evaluation framework
- tool = Software tool/library
- theoretical = Formal proofs/analysis
- empirical = Measurement study

**domains**: Pick all that apply
- vision, nlp, audio, tabular, multimodal, graph, llm, reinforcement-learning, federated-learning, generative

**model_types**: Pick all that apply
- cnn, transformer, rnn, llm, diffusion, gan, gnn, ensemble, tree

---

## Response Format

Return JSON only:

```json
{
  "owasp_labels": ["ML01"],
  "paper_type": "attack",
  "domains": ["vision"],
  "model_types": ["cnn"],
  "tags": ["black-box", "transferability"],
  "confidence": "HIGH",
  "reasoning": "One sentence explaining your classification."
}
```

---

## Common Traps to Avoid

1. **"Black-box attack" ≠ always ML01** - Could be ML04 (membership), ML05 (extraction), etc. Check WHAT is being attacked.

2. **Defense papers get the ATTACK category** - A paper defending against backdoors → ML02, not a new category.

3. **Surveys are NOT "NONE"** - A survey about adversarial ML → ML01 (or multiple labels if covers multiple attacks).

4. **"AI for security" ≠ "AI security"**
   - Using ML to detect malware → NONE
   - Attacking an ML malware detector → ML01

5. **ML09 is almost never correct** - It's only for intercepting model outputs in transit. Input detection/sanitization → ML01.

6. **Architecture papers are NONE** - ResNet, BERT, GPT architecture papers are not security papers.

---

## User Prompt Template

```
Classify this paper:

TITLE: {title}

ABSTRACT: {abstract}

Return JSON only.
```
