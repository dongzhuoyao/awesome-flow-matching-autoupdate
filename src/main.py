#!/usr/bin/env python3
"""Main orchestration script for awesome-flow-matching-autoupdate."""
from __future__ import annotations

import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sources.arxiv import search_arxiv, Paper
from sources.semantic_scholar import search_semantic_scholar, get_paper_details
from sources.openalex import search_openalex, get_citation_count_openalex
from dedup import load_existing_papers, load_local_readme, is_duplicate, normalize_title
from classifier import classify_paper
from formatter import generate_readme, validate_markdown


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def fetch_all_papers(config: dict) -> list[dict]:
    """
    Fetch papers from all sources.

    Returns list of paper dicts with normalized fields.
    """
    all_papers = {}  # Use dict to dedupe by arxiv_id

    search_terms = config["search_terms"]
    min_citations = config["min_citations"]

    print(f"Searching for papers with terms: {search_terms}")
    print(f"Minimum citations required: {min_citations}")

    # 1. Search OpenAlex directly (free, no rate limits, has citation counts)
    print("\n[1/3] Fetching from OpenAlex...")
    for term in search_terms:
        print(f"  Searching: '{term}'")
        oa_papers = search_openalex(
            term,
            limit=200,
            min_citation_count=min_citations,
            year_from=2020
        )
        print(f"    Found {len(oa_papers)} papers with {min_citations}+ citations")

        for paper in oa_papers:
            # Skip if no arXiv ID (we prefer arXiv links)
            if not paper.arxiv_id:
                continue

            clean_id = paper.arxiv_id.split("v")[0]

            # Skip if already have this paper
            if clean_id in all_papers:
                continue

            all_papers[clean_id] = {
                "arxiv_id": clean_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "published_date": None,
                "citation_count": paper.citation_count,
                "venue": paper.venue,
                "arxiv_url": f"https://arxiv.org/abs/{clean_id}"
            }

        time.sleep(0.5)  # Be polite

    # 2. Search arXiv for recent papers and check citations via OpenAlex
    print("\n[2/3] Fetching recent papers from arXiv...")
    arxiv_papers = search_arxiv(search_terms, max_results=200)
    print(f"  Found {len(arxiv_papers)} papers on arXiv")

    papers_to_check = []
    for paper in arxiv_papers:
        if not paper.arxiv_id:
            continue
        clean_id = paper.arxiv_id.split("v")[0]
        if clean_id not in all_papers:
            papers_to_check.append(paper)

    print(f"  Checking citations for {len(papers_to_check)} new papers...")
    for i, paper in enumerate(papers_to_check):
        clean_id = paper.arxiv_id.split("v")[0]

        # Get citation count from OpenAlex
        details = get_citation_count_openalex(clean_id)

        if details:
            citation_count = details.get("citation_count", 0)
            venue = details.get("venue", "")
        else:
            citation_count = 0
            venue = ""

        # Apply citation filter
        if citation_count >= min_citations:
            print(f"    [{i+1}/{len(papers_to_check)}] {paper.title[:40]}... ({citation_count} citations) ✓")
            all_papers[clean_id] = {
                "arxiv_id": clean_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "published_date": paper.published_date,
                "citation_count": citation_count,
                "venue": venue,
                "arxiv_url": f"https://arxiv.org/abs/{clean_id}"
            }

        time.sleep(0.2)  # Rate limiting

    # 3. Optionally try Semantic Scholar as backup
    print("\n[3/3] Checking Semantic Scholar for additional papers...")
    for term in search_terms:
        print(f"  Searching: '{term}'")
        try:
            ss_papers = search_semantic_scholar(
                term,
                limit=50,
                min_citation_count=min_citations,
                year_from=2020
            )
            print(f"    Found {len(ss_papers)} papers")

            for paper in ss_papers:
                if not paper.arxiv_id:
                    continue

                clean_id = paper.arxiv_id.split("v")[0]
                if clean_id in all_papers:
                    continue

                all_papers[clean_id] = {
                    "arxiv_id": clean_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "published_date": None,
                    "citation_count": paper.citation_count,
                    "venue": paper.venue,
                    "arxiv_url": f"https://arxiv.org/abs/{clean_id}"
                }
        except Exception as e:
            print(f"    Semantic Scholar error: {e}")

        time.sleep(2)  # Rate limiting

    return list(all_papers.values())


def filter_duplicates(
    papers: list[dict],
    existing_arxiv_ids: set[str],
    existing_titles: set[str]
) -> list[dict]:
    """Filter out papers that already exist in the original repo."""
    new_papers = []

    for paper in papers:
        if is_duplicate(
            paper["arxiv_id"],
            paper["title"],
            existing_arxiv_ids,
            existing_titles
        ):
            print(f"  Skipping duplicate: {paper['title'][:50]}...")
            continue
        new_papers.append(paper)

    return new_papers


def classify_papers(papers: list[dict]) -> dict[str, list[dict]]:
    """Classify papers into categories."""
    papers_by_category = {
        "Foundational": [],
        "Theory": [],
        "Schrödinger Bridge": [],
        "Discrete Data": [],
        "Accelerating": [],
        "Applications": []
    }

    print(f"\nClassifying {len(papers)} papers...")

    for paper in papers:
        category = classify_paper(paper["title"], paper["abstract"])
        paper["category"] = category
        papers_by_category[category].append(paper)
        print(f"  [{category}] {paper['title'][:60]}...")

    return papers_by_category


def main():
    """Main entry point."""
    print("=" * 60)
    print("Awesome Flow Matching Auto-Update")
    print("=" * 60)

    # Load config
    config = load_config()
    readme_path = Path(__file__).parent.parent / "README.md"

    # Step 1: Load existing papers from original repo (dongzhuoyao/awesome-flow-matching)
    print("\n[Step 1] Loading existing papers from original repository...")
    print(f"  Source: {config['original_readme_url']}")
    orig_arxiv_ids, orig_titles = load_existing_papers(
        config["original_readme_url"]
    )

    # Step 2: Load existing papers from our local README (to avoid self-duplicates)
    print("\n[Step 2] Loading existing papers from local README...")
    local_arxiv_ids, local_titles = load_local_readme(str(readme_path))

    # Merge both sets for comprehensive deduplication
    existing_arxiv_ids = orig_arxiv_ids | local_arxiv_ids
    existing_titles = orig_titles | local_titles
    print(f"\nTotal unique papers to exclude: {len(existing_arxiv_ids)} arXiv IDs, {len(existing_titles)} titles")

    # Step 3: Fetch papers from all sources
    print("\n[Step 3] Fetching papers from sources...")
    all_papers = fetch_all_papers(config)
    print(f"\nTotal papers found with {config['min_citations']}+ citations: {len(all_papers)}")

    # Step 4: Filter duplicates (incremental update - only new papers)
    print("\n[Step 4] Filtering duplicates (incremental update)...")
    new_papers = filter_duplicates(all_papers, existing_arxiv_ids, existing_titles)
    print(f"New papers after deduplication: {len(new_papers)}")

    if not new_papers:
        print("\nNo new papers to add!")
        return

    # Step 5: Classify papers
    print("\n[Step 5] Classifying papers...")
    papers_by_category = classify_papers(new_papers)

    # Print summary
    print("\n" + "=" * 60)
    print("Summary by category:")
    for category, papers in papers_by_category.items():
        if papers:
            print(f"  {category}: {len(papers)} papers")

    # Step 6: Generate README
    print("\n[Step 6] Generating README.md...")
    readme_content = generate_readme(papers_by_category, datetime.utcnow())

    # Step 7: Sanity check - validate markdown format
    print("\n[Step 7] Validating markdown format...")
    warnings = validate_markdown(readme_content)
    if warnings:
        print("  Warnings found:")
        for warning in warnings:
            print(f"    ⚠ {warning}")
    else:
        print("  ✓ Markdown validation passed")

    # Write README
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print(f"\nREADME written to {readme_path}")
    print("\nDone!")


if __name__ == "__main__":
    main()
