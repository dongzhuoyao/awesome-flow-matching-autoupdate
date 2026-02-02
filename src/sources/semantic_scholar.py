"""Semantic Scholar API client for fetching citation counts and paper metadata."""
from __future__ import annotations

import urllib.request
import urllib.parse
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SemanticScholarPaper:
    """Paper metadata from Semantic Scholar."""
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    year: int
    citation_count: int
    venue: str
    arxiv_id: Optional[str]
    url: str
    publication_date: Optional[str]


def search_semantic_scholar(
    query: str,
    limit: int = 100,
    min_citation_count: int = 0,
    year_from: Optional[int] = None,
    max_retries: int = 3
) -> list[SemanticScholarPaper]:
    """
    Search Semantic Scholar for papers.

    Args:
        query: Search query string
        limit: Maximum number of results
        min_citation_count: Minimum citation count filter
        year_from: Only include papers from this year onwards
        max_retries: Maximum number of retries on rate limit

    Returns:
        List of SemanticScholarPaper objects
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    fields = "paperId,title,authors,abstract,year,citationCount,venue,externalIds,url,publicationDate"

    params = {
        "query": query,
        "limit": min(limit, 100),  # API max is 100 per request
        "fields": fields
    }

    if year_from:
        params["year"] = f"{year_from}-"

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    papers = []

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            for item in data.get("data", []):
                citation_count = item.get("citationCount", 0) or 0

                # Apply citation filter
                if citation_count < min_citation_count:
                    continue

                # Extract authors
                authors = []
                for author in item.get("authors", []):
                    name = author.get("name", "")
                    if name:
                        authors.append(name)

                # Extract arXiv ID if available
                external_ids = item.get("externalIds", {}) or {}
                arxiv_id = external_ids.get("ArXiv")

                paper = SemanticScholarPaper(
                    paper_id=item.get("paperId", ""),
                    title=item.get("title", ""),
                    authors=authors,
                    abstract=item.get("abstract", "") or "",
                    year=item.get("year", 0) or 0,
                    citation_count=citation_count,
                    venue=item.get("venue", "") or "",
                    arxiv_id=arxiv_id,
                    url=item.get("url", ""),
                    publication_date=item.get("publicationDate")
                )
                papers.append(paper)

            return papers  # Success, return results

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = 2 ** attempt * 30  # Exponential backoff: 30, 60, 120 seconds
                print(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"HTTP error from Semantic Scholar: {e}")
                return papers
        except Exception as e:
            print(f"Error fetching from Semantic Scholar: {e}")
            return papers

    return papers


def get_citation_count(arxiv_id: str) -> Optional[int]:
    """
    Get citation count for a paper by its arXiv ID.

    Args:
        arxiv_id: The arXiv ID (e.g., "2210.02747")

    Returns:
        Citation count or None if not found
    """
    # Clean up arxiv ID (remove version suffix if present)
    clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}?fields=citationCount,venue"

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("citationCount", 0)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        elif e.code == 429:
            print("Rate limited, waiting...")
            time.sleep(5)
            return None
        else:
            print(f"HTTP error: {e}")
            return None
    except Exception as e:
        print(f"Error getting citation count: {e}")
        return None


def get_paper_details(arxiv_id: str, max_retries: int = 3) -> Optional[dict]:
    """
    Get detailed paper info from Semantic Scholar by arXiv ID.

    Args:
        arxiv_id: The arXiv ID
        max_retries: Maximum number of retries on rate limit

    Returns:
        Dict with citationCount and venue, or None if not found
    """
    clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}?fields=citationCount,venue,publicationVenue"

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
                return {
                    "citation_count": data.get("citationCount", 0) or 0,
                    "venue": data.get("venue", "") or "",
                    "publication_venue": data.get("publicationVenue", {})
                }

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = 2 ** attempt * 5  # Exponential backoff: 5, 10, 20 seconds
                print(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            elif e.code == 404:
                return None
            else:
                return None
        except Exception:
            return None

    return None


if __name__ == "__main__":
    # Test search
    papers = search_semantic_scholar("flow matching generative", limit=5, min_citation_count=10)
    print(f"Found {len(papers)} papers with 10+ citations")
    for p in papers:
        print(f"- {p.title} (citations: {p.citation_count}, venue: {p.venue})")
