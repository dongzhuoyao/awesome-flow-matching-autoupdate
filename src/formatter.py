"""Markdown formatter for paper entries."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def format_paper_entry(
    title: str,
    authors: list[str],
    arxiv_id: str,
    venue: Optional[str] = None,
    published_date: Optional[datetime] = None,
    citation_count: Optional[int] = None
) -> str:
    """
    Format a paper entry in the awesome-list markdown style.

    Format:
    **Paper Title**\
    *Author1, Author2, ...*\
    Venue Year. [[Paper](url)]\
    Date

    Args:
        title: Paper title
        authors: List of author names
        arxiv_id: arXiv ID (e.g., "2210.02747")
        venue: Publication venue (optional)
        published_date: Publication date (optional)
        citation_count: Number of citations (optional)

    Returns:
        Formatted markdown string
    """
    lines = []

    # Title
    lines.append(f"**{title}**\\")

    # Authors (limit to first 5 if many)
    if len(authors) > 5:
        author_str = ", ".join(authors[:5]) + ", et al."
    else:
        author_str = ", ".join(authors)
    lines.append(f"*{author_str}*\\")

    # Venue and link
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
    venue_str = venue if venue else "arXiv"

    year = ""
    if published_date:
        year = f" {published_date.year}"
    elif arxiv_id and len(arxiv_id) >= 4:
        # Extract year from arxiv ID (first 2 digits)
        yy = arxiv_id[:2]
        year = f" 20{yy}"

    citation_str = f" (cited: {citation_count})" if citation_count else ""
    lines.append(f"{venue_str}{year}.{citation_str} [[Paper]({arxiv_url})]\\")

    # Date
    if published_date:
        date_str = published_date.strftime("%d %b %Y")
        lines.append(date_str)
    elif arxiv_id and len(arxiv_id) >= 4:
        # Format from arxiv ID
        yy = arxiv_id[:2]
        mm = arxiv_id[2:4]
        month_names = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }
        month = month_names.get(mm, mm)
        lines.append(f"{month} 20{yy}")

    return "\n".join(lines)


def format_category_section(category: str, papers: list[dict]) -> str:
    """
    Format a section of papers for a category.

    Args:
        category: Category name
        papers: List of paper dicts

    Returns:
        Formatted markdown section
    """
    if not papers:
        return ""

    lines = [f"## {category}", ""]

    for paper in papers:
        entry = format_paper_entry(
            title=paper["title"],
            authors=paper["authors"],
            arxiv_id=paper["arxiv_id"],
            venue=paper.get("venue"),
            published_date=paper.get("published_date"),
            citation_count=paper.get("citation_count")
        )
        lines.append(entry)
        lines.append("")  # Blank line between entries

    return "\n".join(lines)


def generate_readme(
    papers_by_category: dict[str, list[dict]],
    last_updated: datetime
) -> str:
    """
    Generate the full README content.

    Args:
        papers_by_category: Dict mapping category name to list of papers
        last_updated: Timestamp of last update

    Returns:
        Full README markdown content
    """
    lines = [
        "# Awesome Flow Matching - Auto Updated",
        "",
        "[![Awesome](https://awesome.re/badge.svg)](https://awesome.re) [![GitHub stars](https://img.shields.io/github/stars/dongzhuoyao/awesome-flow-matching.svg?style=social&label=Star)](https://github.com/dongzhuoyao/awesome-flow-matching)",
        "",
        "Automatically curated list of flow matching papers with **10+ citations**.",
        "",
        f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "This repository automatically tracks new flow matching papers from arXiv and Semantic Scholar,",
        "filtering for quality (minimum 10 citations) and categorizing them using AI.",
        "",
        "Original curated list: [awesome-flow-matching](https://github.com/dongzhuoyao/awesome-flow-matching)",
        "",
        "---",
        "",
        "## Table of Contents",
        ""
    ]

    # Add TOC
    category_order = ["Foundational", "Theory", "Schrödinger Bridge", "Discrete Data", "Accelerating", "Applications"]
    for category in category_order:
        if category in papers_by_category and papers_by_category[category]:
            anchor = category.lower().replace(" ", "-").replace("ö", "o")
            count = len(papers_by_category[category])
            lines.append(f"- [{category}](#{anchor}) ({count} papers)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Add each category section
    for category in category_order:
        if category in papers_by_category and papers_by_category[category]:
            section = format_category_section(category, papers_by_category[category])
            lines.append(section)

    # Footer
    lines.extend([
        "---",
        "",
        "## About",
        "",
        "This list is automatically generated and updated daily.",
        "",
        "**Inclusion criteria:**",
        "- Paper must mention 'flow matching', 'rectified flow', 'stochastic interpolant', or 'continuous normalizing flow'",
        "- Minimum 10 citations required",
        "",
        "**Sources:** arXiv, Semantic Scholar",
        "",
        "**Classification:** OpenAI GPT-4o-mini",
        ""
    ])

    return "\n".join(lines)


def validate_markdown(content: str) -> list[str]:
    """
    Validate markdown content for common issues.

    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []

    lines = content.split('\n')

    # Check for basic structure
    if not content.startswith('# '):
        warnings.append("Missing main heading (should start with '# ')")

    # Check for unbalanced bold markers
    bold_count = content.count('**')
    if bold_count % 2 != 0:
        warnings.append(f"Unbalanced bold markers (**): found {bold_count}")

    # Check for unbalanced italic markers (single *)
    # Count single asterisks not part of **
    import re
    single_asterisks = len(re.findall(r'(?<!\*)\*(?!\*)', content))
    if single_asterisks % 2 != 0:
        warnings.append(f"Unbalanced italic markers (*): found {single_asterisks}")

    # Check for broken links
    links = re.findall(r'\[([^\]]*)\]\(([^)]*)\)', content)
    for text, url in links:
        if not url or url.isspace():
            warnings.append(f"Empty link URL for text: '{text}'")
        if not text:
            warnings.append(f"Empty link text for URL: '{url}'")

    # Check for duplicate arXiv IDs
    arxiv_ids = re.findall(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', content)
    seen_ids = set()
    for arxiv_id in arxiv_ids:
        clean_id = arxiv_id.split('v')[0]
        if clean_id in seen_ids:
            warnings.append(f"Duplicate arXiv ID: {clean_id}")
        seen_ids.add(clean_id)

    # Check for empty sections
    section_pattern = r'^## ([^\n]+)\n\n(?=## |---|$)'
    empty_sections = re.findall(section_pattern, content, re.MULTILINE)
    for section in empty_sections:
        warnings.append(f"Empty section: {section}")

    # Check TOC links match actual sections
    toc_links = re.findall(r'\[([^\]]+)\]\(#([^)]+)\)', content)
    section_headers = re.findall(r'^## ([^\n]+)$', content, re.MULTILINE)
    section_anchors = {h.lower().replace(' ', '-').replace('ö', 'o'): h for h in section_headers}

    for toc_text, toc_anchor in toc_links:
        if toc_anchor not in section_anchors and toc_anchor not in ['', 'awesome.re']:
            # Skip external links
            if not toc_anchor.startswith('http'):
                warnings.append(f"TOC link '#{toc_anchor}' has no matching section")

    return warnings


if __name__ == "__main__":
    # Test formatting
    test_paper = {
        "title": "Flow Matching for Generative Modeling",
        "authors": ["Yaron Lipman", "Ricky T. Q. Chen", "Heli Ben-Hamu"],
        "arxiv_id": "2210.02747",
        "venue": "ICLR",
        "citation_count": 500,
        "published_date": datetime(2022, 10, 10)
    }

    entry = format_paper_entry(**test_paper)
    print(entry)
