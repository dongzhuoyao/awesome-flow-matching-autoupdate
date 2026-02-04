"""Deduplication module - parses original repo README to find existing papers."""
from __future__ import annotations

import re
import urllib.request


def fetch_original_readme(url: str) -> str:
    """Fetch the README from the original repository."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "awesome-flow-matching-autoupdate/1.0")

        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching original README: {e}")
        return ""


def extract_arxiv_ids(readme_content: str) -> set[str]:
    """
    Extract all arXiv IDs from the README content.

    Looks for patterns like:
    - https://arxiv.org/abs/2210.02747
    - https://arxiv.org/pdf/2210.02747
    - arXiv:2210.02747

    Returns:
        Set of arXiv IDs (without version suffix)
    """
    arxiv_ids = set()

    # Pattern for arxiv.org URLs
    url_pattern = r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})'
    for match in re.finditer(url_pattern, readme_content):
        arxiv_id = match.group(1)
        # Remove version suffix if present
        arxiv_id = arxiv_id.split("v")[0]
        arxiv_ids.add(arxiv_id)

    # Pattern for arXiv:XXXX.XXXXX format
    arxiv_pattern = r'arXiv[:\s]+(\d{4}\.\d{4,5})'
    for match in re.finditer(arxiv_pattern, readme_content, re.IGNORECASE):
        arxiv_id = match.group(1)
        arxiv_id = arxiv_id.split("v")[0]
        arxiv_ids.add(arxiv_id)

    return arxiv_ids


def extract_paper_titles(readme_content: str) -> set[str]:
    """
    Extract paper titles from the README content.

    Looks for bold titles in the format: **Paper Title**

    Returns:
        Set of normalized paper titles (lowercase, stripped)
    """
    titles = set()

    # Pattern for bold titles
    title_pattern = r'\*\*([^*]+)\*\*'
    for match in re.finditer(title_pattern, readme_content):
        title = match.group(1).strip()
        # Normalize: lowercase and remove extra whitespace
        normalized = " ".join(title.lower().split())
        titles.add(normalized)

    return titles


def normalize_title(title: str) -> str:
    """Normalize a title for comparison."""
    return " ".join(title.lower().split())


def is_duplicate(
    arxiv_id: str,
    title: str,
    existing_arxiv_ids: set[str],
    existing_titles: set[str]
) -> bool:
    """
    Check if a paper is a duplicate.

    Args:
        arxiv_id: The paper's arXiv ID
        title: The paper's title
        existing_arxiv_ids: Set of arXiv IDs from original repo
        existing_titles: Set of normalized titles from original repo

    Returns:
        True if the paper is a duplicate
    """
    # Clean arXiv ID
    clean_id = arxiv_id.split("v")[0] if arxiv_id else ""

    # Check arXiv ID match
    if clean_id and clean_id in existing_arxiv_ids:
        return True

    # Check title match
    normalized_title = normalize_title(title)
    if normalized_title in existing_titles:
        return True

    return False


def load_existing_papers(readme_url: str) -> tuple[set[str], set[str]]:
    """
    Load existing papers from the original repository.

    Args:
        readme_url: URL to the raw README file

    Returns:
        Tuple of (arxiv_ids, titles)
    """
    content = fetch_original_readme(readme_url)
    arxiv_ids = extract_arxiv_ids(content)
    titles = extract_paper_titles(content)

    print(f"Found {len(arxiv_ids)} arXiv IDs and {len(titles)} titles in original repo")

    return arxiv_ids, titles


def load_local_readme(readme_path: str) -> tuple[set[str], set[str]]:
    """
    Load existing papers from a local README file.

    Args:
        readme_path: Path to the local README file

    Returns:
        Tuple of (arxiv_ids, titles)
    """
    try:
        with open(readme_path, "r") as f:
            content = f.read()
        arxiv_ids = extract_arxiv_ids(content)
        titles = extract_paper_titles(content)
        print(f"Found {len(arxiv_ids)} arXiv IDs and {len(titles)} titles in local README")
        return arxiv_ids, titles
    except FileNotFoundError:
        print("Local README not found, starting fresh")
        return set(), set()


if __name__ == "__main__":
    # Test deduplication
    url = "https://raw.githubusercontent.com/dongzhuoyao/awesome-flow-matching/main/README.md"
    arxiv_ids, titles = load_existing_papers(url)

    print(f"\nSample arXiv IDs: {list(arxiv_ids)[:5]}")
    print(f"\nSample titles: {list(titles)[:3]}")
