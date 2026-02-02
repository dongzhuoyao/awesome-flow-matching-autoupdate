#!/usr/bin/env python3
"""Sync new papers to the original awesome-flow-matching repo."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def get_existing_arxiv_ids(readme_path: str) -> set[str]:
    """Extract arXiv IDs from a README file."""
    with open(readme_path, 'r') as f:
        content = f.read()
    return set(re.findall(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', content))


def extract_papers_by_section(readme_path: str) -> dict[str, list[str]]:
    """Extract papers grouped by section from auto-update README."""
    with open(readme_path, 'r') as f:
        content = f.read()

    sections = {}
    current_section = None
    current_papers = []
    valid_sections = ['Foundational', 'Theory', 'Schrödinger Bridge', 'Discrete Data', 'Accelerating', 'Applications']

    for line in content.split('\n'):
        if line.startswith('## ') and line[3:].strip() in valid_sections:
            if current_section and current_papers:
                sections[current_section] = current_papers
            current_section = line[3:].strip()
            current_papers = []
        elif current_section and line.startswith('**'):
            current_papers.append(line)
        elif current_section and current_papers and line.strip():
            current_papers[-1] += '\n' + line

    if current_section and current_papers:
        sections[current_section] = current_papers

    return sections


def main():
    auto_update_readme = Path(__file__).parent.parent / "README.md"
    original_repo_dir = Path("/tmp/awesome-flow-matching")
    original_readme = original_repo_dir / "README.md"

    # Clone original repo
    print("Cloning original repo...")
    subprocess.run(["rm", "-rf", str(original_repo_dir)], check=True)
    subprocess.run([
        "git", "clone",
        "https://github.com/dongzhuoyao/awesome-flow-matching.git",
        str(original_repo_dir)
    ], check=True)

    # Get existing papers
    existing_ids = get_existing_arxiv_ids(str(original_readme))
    print(f"Existing papers in original repo: {len(existing_ids)}")

    # Extract papers from auto-update
    sections = extract_papers_by_section(str(auto_update_readme))

    # Filter to only new papers
    new_papers_by_section = {}
    total_new = 0

    for section, papers in sections.items():
        new_papers = []
        for paper in papers:
            match = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', paper)
            if match and match.group(1) not in existing_ids:
                new_papers.append(paper)
        if new_papers:
            new_papers_by_section[section] = new_papers
            total_new += len(new_papers)

    if total_new == 0:
        print("No new papers to add.")
        return 0

    print(f"New papers to add: {total_new}")
    for section, papers in new_papers_by_section.items():
        print(f"  {section}: {len(papers)}")

    # Read original README
    with open(original_readme, 'r') as f:
        orig_content = f.read()

    # Check if "# More Papers" section exists
    if "# More Papers" in orig_content:
        # Append to existing section
        insert_point = orig_content.find("# More Papers")
        # Find the end of the "# More Papers" line
        insert_point = orig_content.find('\n', insert_point) + 1

        new_section = "\n"
        for section, papers in new_papers_by_section.items():
            new_section += f"\n## {section}\n\n"
            for paper in papers:
                new_section += paper + "\n\n"

        # Insert after the header
        updated_content = orig_content[:insert_point] + new_section + orig_content[insert_point:]
    else:
        # Create new section
        new_section = "\n\n---\n\n# More Papers\n\n"
        for section, papers in new_papers_by_section.items():
            new_section += f"\n## {section}\n\n"
            for paper in papers:
                new_section += paper + "\n\n"

        updated_content = orig_content.rstrip() + new_section

    # Write updated README
    with open(original_readme, 'w') as f:
        f.write(updated_content)

    # Create branch, commit, and push
    branch_name = "auto-update-papers"

    subprocess.run(["git", "-C", str(original_repo_dir), "checkout", "-B", branch_name], check=True)
    subprocess.run(["git", "-C", str(original_repo_dir), "add", "README.md"], check=True)

    result = subprocess.run(
        ["git", "-C", str(original_repo_dir), "diff", "--cached", "--quiet"],
        capture_output=True
    )

    if result.returncode == 0:
        print("No changes to commit.")
        return 0

    subprocess.run([
        "git", "-C", str(original_repo_dir),
        "commit", "-m", f"Add {total_new} new papers"
    ], check=True)

    subprocess.run([
        "git", "-C", str(original_repo_dir),
        "push", "-f", "origin", branch_name
    ], check=True)

    # Create and merge PR
    print("Creating PR...")
    result = subprocess.run([
        "gh", "pr", "create",
        "--repo", "dongzhuoyao/awesome-flow-matching",
        "--head", branch_name,
        "--title", f"Add {total_new} new papers",
        "--body", f"Automatically adding {total_new} new papers with 10+ citations."
    ], capture_output=True, text=True)

    if "already exists" in result.stderr:
        print("PR already exists, updating...")
    elif result.returncode != 0:
        print(f"PR creation output: {result.stdout}")
        print(f"PR creation error: {result.stderr}")

    print("Merging PR...")
    subprocess.run([
        "gh", "pr", "merge", branch_name,
        "--repo", "dongzhuoyao/awesome-flow-matching",
        "--merge", "--delete-branch"
    ], check=False)

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
