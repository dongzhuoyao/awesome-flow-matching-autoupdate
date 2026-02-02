"""arXiv API client for fetching flow matching papers."""
from __future__ import annotations

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import time


@dataclass
class Paper:
    """Represents a paper with metadata."""
    title: str
    authors: list[str]
    abstract: str
    arxiv_id: str
    arxiv_url: str
    pdf_url: str
    published_date: datetime
    updated_date: datetime
    categories: list[str]
    citation_count: Optional[int] = None
    venue: Optional[str] = None


def search_arxiv(
    search_terms: list[str],
    max_results: int = 500,
    days_back: Optional[int] = None
) -> list[Paper]:
    """
    Search arXiv for papers matching the given search terms.

    Args:
        search_terms: List of terms to search for (OR'd together)
        max_results: Maximum number of results to return
        days_back: Only return papers from the last N days (None for all time)

    Returns:
        List of Paper objects
    """
    # Build search query - search in title and abstract
    query_parts = []
    for term in search_terms:
        # Search in title OR abstract
        escaped_term = term.replace('"', '')
        query_parts.append(f'(ti:"{escaped_term}" OR abs:"{escaped_term}")')

    query = " OR ".join(query_parts)

    # Add category filter for relevant categories
    categories = ["cs.LG", "cs.CV", "cs.AI", "stat.ML", "cs.CL"]
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    query = f"({query}) AND ({cat_query})"

    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    papers = []

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read().decode("utf-8")

        # Parse XML
        root = ET.fromstring(data)

        # Define namespace
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        cutoff_date = None
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)

        for entry in root.findall("atom:entry", ns):
            # Extract paper info
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Get abstract
            abstract_elem = entry.find("atom:summary", ns)
            abstract = abstract_elem.text.strip().replace("\n", " ") if abstract_elem is not None else ""

            # Get arxiv ID from id URL
            id_elem = entry.find("atom:id", ns)
            arxiv_url = id_elem.text.strip() if id_elem is not None else ""
            arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""

            # Get PDF URL
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")
                    break

            # Get dates
            published_elem = entry.find("atom:published", ns)
            published_str = published_elem.text if published_elem is not None else ""
            published_date = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else datetime.now()

            updated_elem = entry.find("atom:updated", ns)
            updated_str = updated_elem.text if updated_elem is not None else ""
            updated_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00")) if updated_str else datetime.now()

            # Get categories
            categories = []
            for cat in entry.findall("atom:category", ns):
                term = cat.get("term", "")
                if term:
                    categories.append(term)

            # Apply date filter
            if cutoff_date and published_date.replace(tzinfo=None) < cutoff_date:
                continue

            paper = Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                arxiv_id=arxiv_id,
                arxiv_url=arxiv_url,
                pdf_url=pdf_url,
                published_date=published_date,
                updated_date=updated_date,
                categories=categories
            )
            papers.append(paper)

    except Exception as e:
        print(f"Error fetching from arXiv: {e}")

    return papers


if __name__ == "__main__":
    # Test the arXiv search
    terms = ["flow matching", "rectified flow"]
    papers = search_arxiv(terms, max_results=10)
    print(f"Found {len(papers)} papers")
    for p in papers[:3]:
        print(f"- {p.title} ({p.arxiv_id})")
