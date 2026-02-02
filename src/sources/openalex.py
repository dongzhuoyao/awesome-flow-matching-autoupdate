"""OpenAlex API client - free alternative for citation counts."""
from __future__ import annotations

import urllib.request
import urllib.parse
import json
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class OpenAlexPaper:
    """Paper metadata from OpenAlex."""
    openalex_id: str
    title: str
    authors: list[str]
    abstract: str
    year: int
    citation_count: int
    venue: str
    arxiv_id: Optional[str]
    doi: Optional[str]


def search_openalex(
    query: str,
    limit: int = 100,
    min_citation_count: int = 0,
    year_from: Optional[int] = None
) -> list[OpenAlexPaper]:
    """
    Search OpenAlex for papers. Free API, no auth required.

    Args:
        query: Search query string
        limit: Maximum number of results
        min_citation_count: Minimum citation count filter
        year_from: Only include papers from this year onwards

    Returns:
        List of OpenAlexPaper objects
    """
    base_url = "https://api.openalex.org/works"

    # Build filter
    filters = [f'title_and_abstract.search:"{query}"']
    if min_citation_count > 0:
        filters.append(f"cited_by_count:>{min_citation_count - 1}")
    if year_from:
        filters.append(f"publication_year:>{year_from - 1}")

    params = {
        "filter": ",".join(filters),
        "per_page": min(limit, 200),
        "sort": "cited_by_count:desc",
        "mailto": "awesome-flow-matching@example.com"  # Polite pool
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    papers = []

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        for item in data.get("results", []):
            # Extract authors
            authors = []
            for authorship in item.get("authorships", []):
                author = authorship.get("author", {})
                name = author.get("display_name", "")
                if name:
                    authors.append(name)

            # Extract arXiv ID from locations
            arxiv_id = None
            for location in item.get("locations", []):
                source = location.get("source", {}) or {}
                if source.get("type") == "repository":
                    pdf_url = location.get("pdf_url", "") or ""
                    landing_url = location.get("landing_page_url", "") or ""
                    for url in [pdf_url, landing_url]:
                        if "arxiv.org" in url:
                            # Extract arXiv ID
                            import re
                            match = re.search(r'(\d{4}\.\d{4,5})', url)
                            if match:
                                arxiv_id = match.group(1)
                                break

            # Get venue
            venue = ""
            primary_location = item.get("primary_location", {}) or {}
            source = primary_location.get("source", {}) or {}
            venue = source.get("display_name", "") or ""

            # Get abstract
            abstract_inverted = item.get("abstract_inverted_index", {}) or {}
            abstract = reconstruct_abstract(abstract_inverted) if abstract_inverted else ""

            paper = OpenAlexPaper(
                openalex_id=item.get("id", ""),
                title=item.get("title", "") or "",
                authors=authors,
                abstract=abstract,
                year=item.get("publication_year", 0) or 0,
                citation_count=item.get("cited_by_count", 0) or 0,
                venue=venue,
                arxiv_id=arxiv_id,
                doi=item.get("doi", "")
            )
            papers.append(paper)

    except Exception as e:
        print(f"Error fetching from OpenAlex: {e}")

    return papers


def reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return ""

    # Find max position
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))

    # Reconstruct
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)


def get_citation_count_openalex(arxiv_id: str) -> Optional[dict]:
    """
    Get citation count from OpenAlex by arXiv ID.

    Args:
        arxiv_id: The arXiv ID

    Returns:
        Dict with citation_count and venue, or None
    """
    clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

    # OpenAlex uses DOI format for arXiv papers
    doi = f"https://doi.org/10.48550/arXiv.{clean_id}"
    encoded_doi = urllib.parse.quote(doi, safe="")
    url = f"https://api.openalex.org/works/{encoded_doi}?mailto=awesome-flow-matching@example.com"

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

        with urllib.request.urlopen(req, timeout=15) as response:
            item = json.loads(response.read().decode("utf-8"))

        venue = ""
        primary_location = item.get("primary_location", {}) or {}
        source = primary_location.get("source", {}) or {}
        venue = source.get("display_name", "") or ""

        return {
            "citation_count": item.get("cited_by_count", 0) or 0,
            "venue": venue
        }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try searching by title as fallback
            pass
        else:
            print(f"Error getting OpenAlex data: {e}")
    except Exception as e:
        print(f"Error getting OpenAlex data: {e}")

    return None


if __name__ == "__main__":
    # Test OpenAlex
    print("Testing OpenAlex search...")
    papers = search_openalex("flow matching generative", limit=5, min_citation_count=10, year_from=2020)
    print(f"Found {len(papers)} papers")
    for p in papers[:3]:
        print(f"  - {p.title[:50]}... (citations: {p.citation_count}, arXiv: {p.arxiv_id})")

    print("\nTesting citation lookup...")
    details = get_citation_count_openalex("2210.02747")
    if details:
        print(f"  Flow Matching paper: {details['citation_count']} citations, venue: {details['venue']}")
