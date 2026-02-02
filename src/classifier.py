"""Paper classifier using OpenAI API."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional


CATEGORIES = [
    ("Foundational", "Core flow matching methodology, frameworks, and general techniques"),
    ("Theory", "Theoretical analysis, convergence proofs, mathematical foundations, optimal transport theory"),
    ("Schrödinger Bridge", "Schrödinger bridge methods, entropy-regularized optimal transport"),
    ("Discrete Data", "Flow matching for discrete data, text, graphs, categorical variables"),
    ("Accelerating", "Faster sampling, distillation, few-step generation, efficiency improvements"),
    ("Applications", "Domain applications: images, video, audio, 3D, molecules, proteins, biology, etc.")
]


def classify_paper(title: str, abstract: str, api_key: Optional[str] = None) -> str:
    """
    Classify a paper into one of the predefined categories using OpenAI.

    Args:
        title: Paper title
        abstract: Paper abstract
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

    Returns:
        Category name
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("Warning: No OpenAI API key, defaulting to 'Applications'")
        return "Applications"

    categories_text = "\n".join([f"- {name}: {desc}" for name, desc in CATEGORIES])

    prompt = f"""Classify this machine learning paper into exactly one category.

Categories:
{categories_text}

Paper Title: {title}

Abstract: {abstract[:1500]}

Respond with ONLY the category name (e.g., "Foundational" or "Theory"), nothing else."""

    try:
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a paper classifier. Respond with only the category name."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 20
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            category = result["choices"][0]["message"]["content"].strip()

            # Validate category
            valid_categories = [c[0] for c in CATEGORIES]
            if category in valid_categories:
                return category
            else:
                # Try to match partial
                for valid in valid_categories:
                    if valid.lower() in category.lower():
                        return valid
                return "Applications"  # Default fallback

    except Exception as e:
        print(f"Error classifying paper: {e}")
        return "Applications"


def classify_papers_batch(papers: list[dict], api_key: Optional[str] = None) -> dict[str, str]:
    """
    Classify multiple papers.

    Args:
        papers: List of dicts with 'arxiv_id', 'title', 'abstract'
        api_key: OpenAI API key

    Returns:
        Dict mapping arxiv_id to category
    """
    results = {}
    for paper in papers:
        category = classify_paper(
            paper["title"],
            paper.get("abstract", ""),
            api_key
        )
        results[paper["arxiv_id"]] = category
        print(f"  Classified '{paper['title'][:50]}...' as {category}")

    return results


if __name__ == "__main__":
    # Test classification (requires OPENAI_API_KEY)
    test_title = "Flow Matching for Generative Modeling"
    test_abstract = """
    We introduce a new paradigm for generative modeling based on regressing vector fields
    that generate probability paths. We show that this framework generalizes previous methods
    based on diffusion models and continuous normalizing flows.
    """

    category = classify_paper(test_title, test_abstract)
    print(f"Category: {category}")
