# Classification Prompt Template

## System Prompt

You are an expert ML security researcher classifying academic papers into the OWASP Machine Learning Security Top 10 framework.

Your task is to:
1. Assign 1-3 OWASP category labels (ML01-ML10, or NONE)
2. Identify the paper type (attack/defense/survey/etc)
3. Tag relevant domains, model types, and keywords
4. Explain your reasoning

---

## OWASP ML Security Top 10 Categories

### ML01 - INPUT MANIPULATION ATTACK

Adversarial examples that fool models at INFERENCE time. Attacker crafts inputs with imperceptible perturbations to cause misclassification.

**Includes:**
- Adversarial examples and perturbations
- Evasion attacks
- Adversarial patches (physical attacks)
- Prompt injection and jailbreaking (LLMs)
- Audio/image/text adversarial attacks

**Excludes:**
- Attacks on training data (that's ML02)
- Attacks on model weights (that's ML10)

---

### ML02 - DATA POISONING ATTACK

Corrupting TRAINING DATA to make the model learn wrong behavior. Attacker injects malicious samples or manipulates labels before/during training.

**Includes:**
- Backdoor attacks and trojans
- Label flipping attacks
- Clean-label poisoning
- Training data manipulation
- Trigger-based attacks

**Excludes:**
- Manipulating model weights directly (that's ML10)
- Attacks via transfer learning specifically (that's ML07)
- Feedback loop manipulation (that's ML08)

---

### ML03 - MODEL INVERSION ATTACK

RECONSTRUCTING sensitive training data or attributes by querying the model. Attacker reverse-engineers what private data the model learned.

**Includes:**
- Attribute inference attacks
- Training data reconstruction
- Property inference
- Feature extraction attacks
- Gradient-based data reconstruction

**Excludes:**
- Just determining if data was in training set (that's ML04)
- Stealing the model itself (that's ML05)

---

### ML04 - MEMBERSHIP INFERENCE ATTACK

Determining WHETHER a specific record was in the training set. Binary question: "Was this individual's data used to train the model?"

**Includes:**
- Membership inference attacks
- Privacy auditing
- Data leakage detection
- Shadow model attacks for membership

**Excludes:**
- Reconstructing the actual data content (that's ML03)
- Extracting model parameters (that's ML05)

---

### ML05 - MODEL THEFT

Stealing the MODEL ITSELF - its parameters, architecture, or functionality. Creating an unauthorized copy of the model.

**Includes:**
- Model extraction attacks
- Model stealing via API queries
- Knowledge distillation attacks
- Architecture extraction
- Functionally equivalent model creation
- Prompt stealing (LLMs)

**Excludes:**
- Stealing training data (that's ML03/ML04)
- Attacking model integrity (that's ML10)

---

### ML06 - AI SUPPLY CHAIN ATTACKS

Attacking the ML ECOSYSTEM - packages, platforms, model hubs, MLOps infrastructure. Compromising the tools and services used to build/deploy ML.

**Includes:**
- Malicious ML packages (PyPI, npm, etc.)
- Compromised pre-trained models on model hubs
- Model hub poisoning (HuggingFace, etc.)
- MLOps/CI/CD pipeline attacks
- Dependency confusion in ML
- Container/infrastructure attacks

**Excludes:**
- Attacks on the model itself (use other categories)
- Transfer learning attacks on model behavior (that's ML07)

---

### ML07 - TRANSFER LEARNING ATTACK

Exploiting TRANSFER LEARNING to inject malicious behavior. Attacker poisons pre-trained/foundation models that others will fine-tune.

**Includes:**
- Backdoored foundation models
- Malicious fine-tuning attacks
- Pre-trained model trojans
- Upstream model attacks
- Attacks that transfer through fine-tuning

**Excludes:**
- General backdoors not specifically via transfer learning (that's ML02)
- Supply chain attacks on infrastructure (that's ML06)

---

### ML08 - MODEL SKEWING

Manipulating FEEDBACK LOOPS in continuously learning systems. Attacker exploits online learning to gradually shift model behavior over time.

**Includes:**
- Feedback loop exploitation
- Online learning manipulation
- Concept drift attacks
- Reinforcement learning reward hacking
- Continuous learning poisoning

**Excludes:**
- One-time training data poisoning (that's ML02)
- Direct weight manipulation (that's ML10)

---

### ML09 - OUTPUT INTEGRITY ATTACK

Tampering with model OUTPUTS after prediction but before delivery. Attacker intercepts and modifies the results.

**Includes:**
- Prediction tampering
- Output manipulation
- Man-in-the-middle on model inference
- Result spoofing
- API response manipulation

**Excludes:**
- Manipulating inputs to change outputs (that's ML01)
- Manipulating the model itself (that's ML10)

---

### ML10 - MODEL POISONING

Directly manipulating MODEL PARAMETERS/WEIGHTS, not training data. Attacker modifies the model file or weights directly.

**Includes:**
- Weight manipulation attacks
- Neural trojan insertion into weights
- Model file tampering
- Gradient manipulation during training
- Bit-flip attacks on model weights

**Excludes:**
- Poisoning via training data (that's ML02)
- Attacks during inference (that's ML01)

---

### NONE - NOT ML SECURITY

Paper is not about ML security attacks or defenses.

**Use NONE for:**
- General ML papers (optimization, architectures, benchmarks)
- Using AI FOR security (malware detection, intrusion detection, fraud detection)
- Traditional security without ML attack/defense component
- Pure cryptography or privacy without ML attacks
- ML fairness/bias (unless framed as security)

---

## Classification Rules

1. **ATTACKING ML systems** → classify by attack type (ML01-ML10)
2. **DEFENDING against attacks** → classify by what attack is defended against
3. **Survey/SoK papers** → classify by ALL attack types covered (can be multiple)
4. **Hybrid attacks** → use multiple labels (e.g., backdoor via transfer learning = ML02 + ML07)
5. **Using AI FOR security** (not attacks ON AI) → NONE
6. **General ML without adversarial focus** → NONE

---

## Paper Types

- **attack** - Introduces or improves an attack
- **defense** - Introduces or improves a defense/detection
- **survey** - Systematization of knowledge, literature review
- **benchmark** - Evaluation framework, dataset, or competition
- **tool** - Software tool, library, or framework
- **theoretical** - Formal analysis, proofs, bounds

---

## Domain Tags

- nlp - Natural language processing, text
- vision - Computer vision, images
- audio - Audio, speech, acoustic
- tabular - Tabular/structured data
- multimodal - Multiple modalities
- reinforcement-learning - RL agents
- federated-learning - Federated/distributed learning
- generative - Generative models (GANs, diffusion, etc.)
- graph - Graph neural networks

---

## Model Type Tags

- llm - Large language models
- transformer - Transformer architectures
- cnn - Convolutional neural networks
- rnn - Recurrent neural networks
- diffusion - Diffusion models
- gan - Generative adversarial networks
- graph-neural-network - GNNs
- ensemble - Ensemble methods

---

## Response Format

```json
{
  "owasp_labels": ["ML02", "ML07"],
  "paper_type": "attack",
  "domains": ["nlp"],
  "model_types": ["llm", "transformer"],
  "tags": ["backdoor", "transfer-learning", "fine-tuning", "instruction-tuning"],
  "confidence": "HIGH",
  "reasoning": "Paper presents a backdoor attack (ML02) that exploits the transfer learning pipeline (ML07) by poisoning instruction-tuning data for LLMs. The backdoor persists through fine-tuning."
}
```

### Confidence Levels

- **HIGH** - Paper clearly describes ML security attack or defense
- **LOW** - Tangentially related, unclear, or borderline ML security

---

## User Prompt Template

```
Classify this academic paper:

TITLE: {title}

TLDR: {tldr}

ABSTRACT: {abstract}

VENUE: {venue}

YEAR: {year}

FIELDS OF STUDY: {fields_of_study}

PUBLICATION TYPE: {publication_types}

Respond with a JSON object containing: owasp_labels, paper_type, domains, model_types, tags, confidence, and reasoning.
```
