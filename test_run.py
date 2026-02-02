#!/usr/bin/env python3
"""Test script that runs a limited version of the full pipeline."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sources.arxiv import search_arxiv
from sources.openalex import search_openalex, get_citation_count_openalex
from dedup import load_existing_papers, is_duplicate
from formatter import format_paper_entry
from datetime import datetime


def main():
    print("=" * 70)
    print("AWESOME FLOW MATCHING AUTO-UPDATE - TEST RUN")
    print("=" * 70)

    # Config
    search_terms = ["flow matching", "rectified flow", "stochastic interpolant", "continuous normalizing flow"]
    min_citations = 10

    # 1. Load existing papers
    print("\n[Step 1] Loading existing papers from original repo...")
    url = "https://raw.githubusercontent.com/dongzhuoyao/awesome-flow-matching/main/README.md"
    existing_ids, existing_titles = load_existing_papers(url)

    # 2. Search OpenAlex (free, no rate limits)
    print(f"\n[Step 2] Searching OpenAlex for papers with {min_citations}+ citations...")
    all_papers = []

    for term in search_terms:
        print(f"  Searching: '{term}'")
        papers = search_openalex(term, limit=100, min_citation_count=min_citations, year_from=2020)
        print(f"    Found {len(papers)} papers")

        for p in papers:
            if p.arxiv_id:
                all_papers.append({
                    "arxiv_id": p.arxiv_id.split("v")[0],
                    "title": p.title,
                    "authors": p.authors,
                    "abstract": p.abstract,
                    "citation_count": p.citation_count,
                    "venue": p.venue
                })
        time.sleep(0.5)  # Be polite

    # Dedupe
    seen = set()
    unique_papers = []
    for p in all_papers:
        if p["arxiv_id"] not in seen:
            seen.add(p["arxiv_id"])
            unique_papers.append(p)

    print(f"\n  Total unique papers with {min_citations}+ citations: {len(unique_papers)}")

    # 3. Filter duplicates
    print("\n[Step 3] Filtering papers already in original repo...")
    new_papers = []
    for p in unique_papers:
        if not is_duplicate(p["arxiv_id"], p["title"], existing_ids, existing_titles):
            new_papers.append(p)
        else:
            print(f"  [SKIP] {p['title'][:50]}... (already in repo)")

    print(f"\n  New papers not in original repo: {len(new_papers)}")

    # 4. Show results
    print("\n" + "=" * 70)
    print("NEW PAPERS FOUND")
    print("=" * 70)

    # Sort by citation count
    new_papers.sort(key=lambda x: x["citation_count"], reverse=True)

    for i, p in enumerate(new_papers[:15]):
        print(f"\n{i+1}. {p['title']}")
        print(f"   Citations: {p['citation_count']}, Venue: {p['venue'] or 'arXiv'}")
        print(f"   arXiv: https://arxiv.org/abs/{p['arxiv_id']}")

    # 5. Show formatted output sample
    if new_papers:
        print("\n" + "=" * 70)
        print("SAMPLE FORMATTED OUTPUT")
        print("=" * 70)
        sample = new_papers[0]
        formatted = format_paper_entry(
            title=sample["title"],
            authors=sample["authors"],
            arxiv_id=sample["arxiv_id"],
            venue=sample["venue"],
            citation_count=sample["citation_count"]
        )
        print(formatted)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return new_papers


if __name__ == "__main__":
    main()
