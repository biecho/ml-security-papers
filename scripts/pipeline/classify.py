#!/usr/bin/env python3
"""
Classify papers using LLM (Groq, Google AI, or Cerebras).

Takes papers with status="fetched" and classifies them into OWASP categories
with rich metadata:
- owasp_labels: ML01-ML10 (multi-label) or NONE
- paper_type: attack, defense, survey, etc.
- domains: vision, nlp, llm, audio, etc.
- model_types: cnn, transformer, llm, etc.

Papers with abstracts get HIGH confidence classification.
Papers without abstracts get LOW confidence (title-only).
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from state import PaperState

# API configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GOOGLE_MODEL = "gemini-2.0-flash"

CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")
CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama-3.3-70b"

# Load rich prompt from config file
def load_system_prompt() -> str:
    """Load the classification system prompt from config file."""
    prompt_path = Path(__file__).parent.parent.parent / "configs/prompts/classification.md"
    if prompt_path.exists():
        with open(prompt_path) as f:
            content = f.read()
        # Extract system prompt section (everything before "## User Prompt Template")
        if "## User Prompt Template" in content:
            content = content.split("## User Prompt Template")[0]
        # Remove the markdown header
        if content.startswith("# Classification Prompt Template"):
            content = content.replace("# Classification Prompt Template", "", 1)
        if "## System Prompt" in content:
            content = content.split("## System Prompt", 1)[1]
        return content.strip()
    else:
        raise FileNotFoundError(f"Classification prompt not found at {prompt_path}")

# Load system prompt at module level
SYSTEM_PROMPT = load_system_prompt()


VALID_CATEGORIES = ["ML01", "ML02", "ML03", "ML04", "ML05", "ML06", "ML07", "ML08", "ML09", "ML10", "NONE"]
VALID_PAPER_TYPES = ["attack", "defense", "survey", "benchmark", "tool", "theoretical", "empirical"]
VALID_DOMAINS = ["nlp", "vision", "audio", "tabular", "multimodal", "reinforcement-learning", "federated-learning", "generative", "graph", "llm", "timeseries"]
VALID_MODEL_TYPES = ["llm", "transformer", "cnn", "rnn", "diffusion", "gan", "gnn", "graph-neural-network", "ensemble", "tree", "decision-tree", "mlp", "svm", "dnn"]


def validate_category(category: str) -> str:
    """Validate and extract category from LLM response."""
    category = category.strip().upper()
    if category in VALID_CATEGORIES:
        return category
    # Try to extract valid category
    for v in VALID_CATEGORIES:
        if v in category:
            return v
    return "NONE"


def parse_classification_response(response: str, has_abstract: bool = True) -> dict:
    """
    Parse LLM JSON response into classification result.

    Returns a dict with:
    - owasp_labels: list of validated categories
    - paper_type: validated paper type
    - domains: list of domains
    - model_types: list of model types
    - tags: list of tags
    - confidence: HIGH or LOW
    - reasoning: explanation
    """
    # Default fallback result
    fallback = {
        "owasp_labels": ["NONE"],
        "paper_type": "unknown",
        "domains": [],
        "model_types": [],
        "tags": [],
        "confidence": "HIGH" if has_abstract else "LOW",
        "reasoning": ""
    }

    try:
        # Try to extract JSON from response (may have markdown code blocks)
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if not json_match:
            # Try multiline JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

        if json_match:
            result = json.loads(json_match.group())
        else:
            # No JSON found, try to parse as plain category
            cat = validate_category(response)
            fallback["owasp_labels"] = [cat]
            fallback["reasoning"] = "Parsed from plain text response"
            return fallback

        # Validate and normalize owasp_labels
        labels = result.get("owasp_labels", [])
        if isinstance(labels, str):
            labels = [labels]
        validated_labels = [validate_category(l) for l in labels if l]
        validated_labels = [l for l in validated_labels if l in VALID_CATEGORIES]
        if not validated_labels:
            validated_labels = ["NONE"]
        # Cap at 5 labels max
        if len(validated_labels) > 5:
            validated_labels = validated_labels[:5]

        # Validate paper_type
        paper_type = result.get("paper_type", "unknown")
        if paper_type not in VALID_PAPER_TYPES:
            paper_type = "unknown"

        # Validate domains
        domains = result.get("domains", [])
        if isinstance(domains, str):
            domains = [domains]
        domains = [d.lower() for d in domains if d]

        # Validate model_types
        model_types = result.get("model_types", [])
        if isinstance(model_types, str):
            model_types = [model_types]
        model_types = [m.lower() for m in model_types if m]

        # Get tags (free-form, just clean up)
        tags = result.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tags = [t.lower().strip() for t in tags if t]

        # Confidence
        confidence = result.get("confidence", "HIGH" if has_abstract else "LOW")
        if confidence not in ["HIGH", "LOW"]:
            confidence = "HIGH" if has_abstract else "LOW"

        return {
            "owasp_labels": validated_labels,
            "paper_type": paper_type,
            "domains": domains,
            "model_types": model_types,
            "tags": tags,
            "confidence": confidence,
            "reasoning": result.get("reasoning", "")
        }

    except json.JSONDecodeError as e:
        fallback["reasoning"] = f"JSON parse error: {e}. Response: {response[:200]}"
        return fallback
    except Exception as e:
        fallback["reasoning"] = f"Parse error: {e}. Response: {response[:200]}"
        return fallback


def build_user_message(title: str, abstract: str = None, venue: str = None, year: int = None) -> str:
    """Build the user message for classification."""
    parts = [f"Title: {title}"]

    if abstract:
        parts.append(f"\nAbstract: {abstract[:2500]}")
    else:
        parts.append("\n(No abstract available - classify based on title only)")

    if venue:
        parts.append(f"\nVenue: {venue}")
    if year:
        parts.append(f"\nYear: {year}")

    parts.append("\n\nRespond with a JSON object containing: owasp_labels, paper_type, domains, model_types, tags, confidence, and reasoning.")

    return "".join(parts)


def classify_with_groq(title: str, abstract: str = None, venue: str = None, year: int = None) -> dict:
    """Classify using Groq API. Returns parsed classification result."""
    has_abstract = abstract is not None
    user_message = build_user_message(title, abstract, venue, year)

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "ml-security-papers/1.0",
    }

    req = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode())
        content = data["choices"][0]["message"]["content"]
        return parse_classification_response(content, has_abstract)


def classify_with_google(title: str, abstract: str = None, venue: str = None, year: int = None) -> dict:
    """Classify using Google AI (Gemini) API. Returns parsed classification result."""
    has_abstract = abstract is not None
    user_message = build_user_message(title, abstract, venue, year)

    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"

    url = f"{GOOGLE_API_URL}/{GOOGLE_MODEL}:generateContent?key={GOOGLE_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 500,
        }
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ml-security-papers/1.0",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode())
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_classification_response(content, has_abstract)


def classify_with_cerebras(title: str, abstract: str = None, venue: str = None, year: int = None) -> dict:
    """Classify using Cerebras API (OpenAI-compatible). Returns parsed classification result."""
    has_abstract = abstract is not None
    user_message = build_user_message(title, abstract, venue, year)

    payload = {
        "model": CEREBRAS_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "ml-security-papers/1.0",
    }

    req = urllib.request.Request(
        CEREBRAS_API_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode())
        content = data["choices"][0]["message"]["content"]
        return parse_classification_response(content, has_abstract)


def classify_with_llm(title: str, abstract: str = None, venue: str = None, year: int = None, provider: str = "cerebras") -> dict:
    """
    Classify a paper using LLM.

    Returns a dict with:
    - owasp_labels: list of categories
    - paper_type: attack, defense, survey, etc.
    - domains: list of domains
    - model_types: list of model types
    - tags: list of tags
    - confidence: HIGH or LOW
    - reasoning: explanation
    """
    if provider == "google":
        return classify_with_google(title, abstract, venue, year)
    elif provider == "cerebras":
        return classify_with_cerebras(title, abstract, venue, year)
    else:
        return classify_with_groq(title, abstract, venue, year)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Classify papers with LLM (rich classification)")
    parser.add_argument("--state-file", type=Path, default=Path("data/paper_state.json"))
    parser.add_argument("--limit", type=int, default=0, help="Limit papers to classify (0=all)")
    parser.add_argument("--rate-limit", type=float, default=1.5, help="Seconds between requests")
    parser.add_argument("--include-pending", action="store_true", help="Also classify pending papers (title-only)")
    parser.add_argument("--provider", type=str, default="cerebras", choices=["groq", "google", "cerebras"], help="LLM provider")
    parser.add_argument("--reclassify", action="store_true", help="Re-classify already classified papers")
    parser.add_argument("--dry-run", action="store_true", help="Print classification results without saving")
    args = parser.parse_args()

    if args.provider == "groq" and not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable not set", flush=True)
        return
    if args.provider == "google" and not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY environment variable not set", flush=True)
        return
    if args.provider == "cerebras" and not CEREBRAS_API_KEY:
        print("Error: CEREBRAS_API_KEY environment variable not set", flush=True)
        print("Get a free API key at: https://cloud.cerebras.ai/", flush=True)
        return

    print(f"Using provider: {args.provider}", flush=True)
    print(f"Using rich classification (paper_type, domains, model_types)", flush=True)

    state = PaperState(args.state_file)

    # Get papers to classify
    if args.reclassify:
        # Re-classify already classified papers
        to_classify = state.get_classified_papers()
        print(f"Re-classifying {len(to_classify)} already classified papers", flush=True)
    else:
        to_classify = state.get_papers_to_classify()  # status="fetched"

    if args.include_pending:
        # Also include pending papers for title-only classification
        to_classify.extend(state.get_pending_papers())

    print(f"Papers to classify: {len(to_classify)}", flush=True)

    if args.limit > 0:
        to_classify = to_classify[:args.limit]
        print(f"Limited to {len(to_classify)} papers", flush=True)

    if not to_classify:
        print("No papers to classify", flush=True)
        return

    classified = 0
    discarded = 0
    errors = 0
    paper_types = {}

    for i, paper in enumerate(to_classify):
        paper_id = paper["paper_id"]
        title = paper["title"]
        abstract = paper.get("abstract")
        venue = paper.get("venue")
        year = paper.get("year")

        try:
            result = classify_with_llm(title, abstract, venue, year, args.provider)

            primary_category = result["owasp_labels"][0] if result["owasp_labels"] else "NONE"

            if args.dry_run:
                print(f"\n[{i+1}] {title[:60]}...", flush=True)
                print(f"    Labels: {result['owasp_labels']}", flush=True)
                print(f"    Type: {result['paper_type']}", flush=True)
                print(f"    Domains: {result['domains']}", flush=True)
                print(f"    Models: {result['model_types']}", flush=True)
                print(f"    Confidence: {result['confidence']}", flush=True)
            else:
                state.set_classified(paper_id, classification_result=result)

            if primary_category == "NONE":
                discarded += 1
            else:
                classified += 1

            # Track paper types
            pt = result.get("paper_type", "unknown")
            paper_types[pt] = paper_types.get(pt, 0) + 1

            if (i + 1) % 10 == 0 or i == 0:
                status = "✓" if primary_category != "NONE" else "✗"
                labels_str = ",".join(result["owasp_labels"][:2])
                print(f"[{i+1}/{len(to_classify)}] {status} {labels_str} ({result['paper_type']}): {title[:35]}...", flush=True)

            # Save checkpoint
            if not args.dry_run and (i + 1) % 25 == 0:
                state.save()
                print(f"  Checkpoint saved", flush=True)

            time.sleep(args.rate_limit)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited, waiting 60s...", flush=True)
                time.sleep(60)
                continue
            else:
                print(f"Error: {e}", flush=True)
                errors += 1

        except Exception as e:
            print(f"Error classifying {title[:40]}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            errors += 1

    # Final save
    if not args.dry_run:
        state.save()

    print(f"\nDone!", flush=True)
    print(f"  Classified (ML01-ML10): {classified}", flush=True)
    print(f"  Discarded (NONE): {discarded}", flush=True)
    print(f"  Errors: {errors}", flush=True)

    print(f"\nBy paper type:", flush=True)
    for pt, count in sorted(paper_types.items(), key=lambda x: -x[1]):
        print(f"  {pt}: {count}", flush=True)

    if not args.dry_run:
        stats = state.stats()
        print(f"\nBy category:", flush=True)
        for cat, count in sorted(stats['by_category'].items()):
            print(f"  {cat}: {count}", flush=True)


if __name__ == "__main__":
    main()
