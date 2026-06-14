#!/usr/bin/env python3
"""
Minimal GitHub star scraper — fetches star counts from GitHub repo pages
without hitting the API rate limit.

Usage:
    python get_github_stars.py owner/repo [owner/repo2 ...]
    python get_github_stars.py facebook/react vuejs/core angular/angular
"""

import sys
import urllib.request
import re


def get_stars(repo: str) -> str:
    """Scrape star count from a GitHub repo page."""
    url = f"https://github.com/{repo}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")

        # Match the star counter span
        m = re.search(
            r'<span id="repo-stars-counter-star"[^>]*>([0-9.kK,]+)</span>',
            html,
        )
        if m:
            return m.group(1)

        # Fallback: aria-label pattern
        m = re.search(
            r'aria-label="([0-9,]+) users? starred this repository"',
            html,
        )
        if m:
            return m.group(1)

        return "?"
    except Exception as e:
        return f"error: {e}"


def main():
    repos = sys.argv[1:]
    if not repos:
        print("Usage: python get_github_stars.py owner/repo [...]")
        sys.exit(1)

    print(f"{'Repository':<30} {'Stars':>10}")
    print("-" * 42)
    for repo in repos:
        stars = get_stars(repo)
        print(f"{repo:<30} {stars:>10}")


if __name__ == "__main__":
    main()
