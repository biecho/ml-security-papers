# Claude Paper Classification Prompt

You are classifying ML security papers from top security conferences (S&P, CCS, USENIX Security, NDSS).

---

## Your Task

For each paper (title + abstract), output:

```
| # | Title | OWASP | Type | Domains | Models | Tags |
```

---

## OWASP ML Top 10 Categories

| Code | Name | Key Signals |
|------|------|-------------|
| **ML01** | Input Manipulation | adversarial examples, evasion, perturbations, jailbreak, prompt injection |
| **ML02** | Data Poisoning | backdoor, trojan, poisoning, trigger, training data attack |
| **ML03** | Model Inversion | reconstruct training data, attribute inference, data extraction |
| **ML04** | Membership Inference | "was X in training set?", membership attack, privacy auditing |
| **ML05** | Model Theft | model extraction, model stealing, watermarking, fingerprinting |
| **ML06** | Supply Chain | malicious packages, model hub attacks, MLOps pipeline |
| **ML07** | Transfer Learning Attack | backdoor in pretrained model, fine-tuning attacks |
| **ML08** | Model Skewing | feedback loops, online learning manipulation, federated attacks |
| **ML09** | Output Integrity | intercept model outputs in transit (VERY RARE) |
| **ML10** | Model Poisoning | direct weight manipulation, bit-flip, fault injection |
| **NONE** | Not ML Security | general ML, AI FOR security (not attacks ON AI) |

---

## Paper Types (pick one)

| Type | When to Use |
|------|-------------|
| `attack` | Proposes/improves an attack method |
| `defense` | Proposes/evaluates a defense or detection |
| `survey` | Literature review, SoK, systematization |
| `benchmark` | Dataset, evaluation framework, competition |
| `tool` | Software library, framework |
| `theoretical` | Proofs, formal analysis, bounds |
| `empirical` | Measurement study, analysis of existing methods |

---

## Domains (pick all that apply)

`vision` `nlp` `audio` `tabular` `multimodal` `graph` `llm` `federated-learning` `reinforcement-learning` `generative`

---

## Model Types (pick all that apply)

`cnn` `transformer` `rnn` `llm` `diffusion` `gan` `gnn` `ensemble` `tree`

---

## Tags (free-form, pick 2-4)

Specific descriptors like:
- Attack style: `black-box` `white-box` `query-efficient` `decision-based` `transfer-attack` `physical`
- Defense style: `certified` `detection` `preprocessing` `adversarial-training`
- Application: `autonomous-driving` `face-recognition` `malware-detection` `object-detection`
- Technique: `gradient-based` `optimization` `GAN-based` `spectral`

---

## Decision Process

1. **Read title** → Usually tells you attack vs defense and category
2. **Scan abstract** → Confirm category, identify domain/models
3. **Assign labels:**
   - OWASP: Usually 1, rarely 2, never 3+
   - Type: Exactly 1
   - Domains: 1-2 typical
   - Models: 1-2 typical
   - Tags: 2-4 specific descriptors

---

## Common Patterns

| Title Contains | → OWASP | → Type |
|----------------|---------|--------|
| "adversarial attack/example" | ML01 | attack |
| "robust defense", "certified" | ML01 | defense |
| "backdoor", "trojan" | ML02 | attack |
| "membership inference" | ML04 | attack |
| "model extraction/stealing" | ML05 | attack |
| "watermark" (for ownership) | ML05 | defense |
| "survey", "SoK" | (by topic) | survey |

---

## Output Format

Provide a markdown table:

```
| # | Title (short) | OWASP | Type | Domains | Models | Tags |
|---|---------------|-------|------|---------|--------|------|
| 1 | Paper Name | ML01 | attack | vision | cnn | `tag1` `tag2` |
```

Then summarize:
- Count by OWASP category
- Count by paper type
- Any notable patterns or edge cases

---

## Rules

1. **Defense papers get the ATTACK's category** - defending against backdoors = ML02
2. **Be conservative with multi-labels** - most papers are 1 category
3. **ML09 is almost never correct** - it's only for intercepting outputs in transit
4. **"AI for security" ≠ "AI security"** - using ML to detect malware = NONE
5. **Surveys get classified by topic** - survey on adversarial ML = ML01
