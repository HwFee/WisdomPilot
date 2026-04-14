"""
LibreOJ (LOJ) Problem Crawler

This script crawls problems from LibreOJ (https://loj.ac)

LOJ uses a GraphQL API for data retrieval.
Reference: https://github.com/hydro-dev/loj-download

Usage:
    # Crawl a single problem
    python -m app.scripts.crawl_loj --problem 1

    # Crawl multiple problems
    python -m app.scripts.crawl_loj --problems 1 2 3 4 5

    # Crawl a range of problems
    python -m app.scripts.crawl_loj --range 1 100

    # Import crawled problems to database
    python -m app.scripts.crawl_loj --problems 1 2 3 --import
"""

import asyncio
import json
import re
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise


# LOJ GraphQL API endpoint
LOJ_GRAPHQL_URL = "https://loj.ac/api/graphql"

# LOJ problem URL pattern
LOJ_PROBLEM_URL = "https://loj.ac/problem/{pid}"


async def fetch_graphql(
    session: aiohttp.ClientSession,
    query: str,
    variables: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Fetch data from LOJ GraphQL API

    Args:
        session: aiohttp session
        query: GraphQL query string
        variables: Query variables

    Returns:
        Response data
    """
    payload = {
        "query": query,
        "variables": variables or {}
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with session.post(
        LOJ_GRAPHQL_URL,
        json=payload,
        headers=headers
    ) as response:
        response.raise_for_status()
        data = await response.json()

        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")

        return data.get("data", {})


async def get_problem_list(
    session: aiohttp.ClientSession,
    page: int = 1,
    per_page: int = 50
) -> List[Dict[str, Any]]:
    """
    Get list of problems from LOJ

    Args:
        session: aiohttp session
        page: Page number
        per_page: Problems per page

    Returns:
        List of problem summaries
    """
    query = """
    query($page: Int!, $perPage: Int!) {
        problemList(page: $page, perPage: $perPage) {
            count
            problems {
                pid
                title
                difficulty
                tags
                accepted
                submitted
            }
        }
    }
    """

    data = await fetch_graphql(session, query, {
        "page": page,
        "perPage": per_page
    })

    return data.get("problemList", {}).get("problems", [])


async def get_problem_detail(
    session: aiohttp.ClientSession,
    pid: int
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a problem

    Args:
        session: aiohttp session
        pid: Problem ID

    Returns:
        Problem details or None if not found
    """
    query = """
    query($pid: Int!) {
        problem(pid: $pid) {
            pid
            title
            difficulty
            tags
            content
            samples {
                input
                output
            }
            testDataInfo {
            }
            timeLimit
            memoryLimit
            accepted
            submitted
        }
    }
    """

    try:
        data = await fetch_graphql(session, query, {"pid": pid})
        return data.get("problem")
    except Exception as e:
        print(f"Error fetching problem {pid}: {e}")
        return None


async def fetch_problem_page(
    session: aiohttp.ClientSession,
    pid: int
) -> Optional[str]:
    """
    Fetch problem page HTML for parsing

    Args:
        session: aiohttp session
        pid: Problem ID

    Returns:
        HTML content or None
    """
    url = LOJ_PROBLEM_URL.format(pid=pid)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"Error fetching page for problem {pid}: {e}")
        return None


def parse_problem_html(html: str) -> Dict[str, Any]:
    """
    Parse problem data from HTML page

    Args:
        html: HTML content

    Returns:
        Parsed problem data
    """
    soup = BeautifulSoup(html, 'html.parser')

    problem = {}

    # Try to extract from embedded JSON
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'window.__INITIAL_STATE__' in str(script.string):
            try:
                # Extract JSON from script
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string)
                if match:
                    state = json.loads(match.group(1))
                    if 'problem' in state:
                        return state['problem']
            except (json.JSONDecodeError, AttributeError):
                pass

    # Fallback to HTML parsing
    title_elem = soup.find('h1') or soup.find(class_='problem-title')
    if title_elem:
        problem['title'] = title_elem.get_text(strip=True)

    return problem


def convert_loj_to_exercise(
    problem: Dict[str, Any],
    course_id: Optional[int] = None
) -> Exercise:
    """
    Convert LOJ problem to Exercise model

    Args:
        problem: LOJ problem data
        course_id: Optional course assignment

    Returns:
        Exercise instance
    """
    # Map LOJ difficulty to our scale (LOJ uses 1-8, we use 1-5)
    loj_difficulty = problem.get('difficulty', 0)
    difficulty = min(5, max(1, round(loj_difficulty / 2)))

    # Build content
    content = {
        "title": problem.get('title', 'Untitled'),
        "description": problem.get('content', ''),
        "time_limit": problem.get('timeLimit', 1000) / 1000,  # Convert ms to seconds
        "memory_limit": problem.get('memoryLimit', 256),  # MB
        "source": f"LibreOJ #{problem.get('pid')}",
    }

    # Add samples
    samples = problem.get('samples', [])
    if samples:
        content['sample_input'] = samples[0].get('input', '') if samples else ''
        content['sample_output'] = samples[0].get('output', '') if samples else ''

    # Build test cases from samples
    test_cases = []
    for i, sample in enumerate(samples):
        test_cases.append({
            "input": sample.get('input', ''),
            "output": sample.get('output', ''),
            "name": f"sample{i+1}"
        })

    # Extract knowledge points from tags
    knowledge_points = problem.get('tags', [])

    # Create exercise
    exercise = Exercise(
        source="loj",
        source_id=str(problem.get('pid')),
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=knowledge_points,
        content=content,
        test_cases=test_cases if test_cases else None,
        is_verified=True,
    )

    return exercise


async def crawl_problem(
    session: aiohttp.ClientSession,
    pid: int
) -> Optional[Dict[str, Any]]:
    """
    Crawl a single problem from LOJ

    Args:
        session: aiohttp session
        pid: Problem ID

    Returns:
        Problem data or None
    """
    print(f"Crawling problem #{pid}...")

    # Try GraphQL API first
    problem = await get_problem_detail(session, pid)

    if problem:
        print(f"  Found via API: {problem.get('title', 'Unknown')}")
        return problem

    # Fallback to HTML parsing
    print(f"  API failed, trying HTML...")
    html = await fetch_problem_page(session, pid)

    if html:
        problem = parse_problem_html(html)
        if problem:
            problem['pid'] = pid
            print(f"  Found via HTML: {problem.get('title', 'Unknown')}")
            return problem

    print(f"  Problem #{pid} not found or inaccessible")
    return None


async def crawl_problems(
    pids: List[int],
    import_to_db: bool = False
) -> List[Dict[str, Any]]:
    """
    Crawl multiple problems

    Args:
        pids: List of problem IDs
        import_to_db: Whether to import to database

    Returns:
        List of crawled problems
    """
    problems = []

    async with aiohttp.ClientSession() as session:
        for pid in pids:
            problem = await crawl_problem(session, pid)
            if problem:
                problems.append(problem)

            # Be nice to the server
            await asyncio.sleep(0.5)

    if import_to_db and problems:
        await import_problems(problems)

    return problems


async def import_problems(
    problems: List[Dict[str, Any]],
    course_code: Optional[str] = None
) -> Dict[str, int]:
    """
    Import crawled problems to database

    Args:
        problems: List of problem data
        course_code: Optional course assignment

    Returns:
        Statistics
    """
    stats = {
        "total": len(problems),
        "imported": 0,
        "errors": 0
    }

    async with AsyncSessionLocal() as session:
        from app.models.course import Course
        from sqlalchemy import select

        # Get course ID if specified
        course_id = None
        if course_code:
            result = await session.execute(
                select(Course).where(Course.code == course_code)
            )
            course = result.scalar_one_or_none()
            if course:
                course_id = course.id

        for problem in problems:
            try:
                exercise = convert_loj_to_exercise(problem, course_id)
                session.add(exercise)
                stats["imported"] += 1
            except Exception as e:
                print(f"Error importing problem {problem.get('pid')}: {e}")
                stats["errors"] += 1

        await session.commit()

    return stats


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Crawl problems from LibreOJ"
    )
    parser.add_argument(
        "--problem", "-p",
        type=int,
        help="Single problem ID to crawl"
    )
    parser.add_argument(
        "--problems",
        type=int,
        nargs="+",
        help="Multiple problem IDs to crawl"
    )
    parser.add_argument(
        "--range",
        type=int,
        nargs=2,
        help="Range of problem IDs (start end)"
    )
    parser.add_argument(
        "--import",
        dest="import_to_db",
        action="store_true",
        help="Import crawled problems to database"
    )
    parser.add_argument(
        "--course",
        type=str,
        choices=["C", "CPP", "Python", "Java", "Rust", "DSA", "ADA", "DiscreteMath"],
        help="Assign problems to this course"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON file for crawled data"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List recent problems"
    )

    args = parser.parse_args()

    # Determine problem IDs to crawl
    pids = []
    if args.problem:
        pids.append(args.problem)
    if args.problems:
        pids.extend(args.problems)
    if args.range:
        pids.extend(range(args.range[0], args.range[1] + 1))

    if args.list:
        # List recent problems
        async with aiohttp.ClientSession() as session:
            problems = await get_problem_list(session, page=1, per_page=20)
            print("\nRecent LOJ Problems:")
            print("-" * 60)
            for p in problems:
                print(f"  #{p.get('pid'):5d} | {p.get('title', 'Unknown')[:40]}")
                print(f"         | Difficulty: {p.get('difficulty', 'N/A')} | Tags: {', '.join(p.get('tags', []))}")
        return

    if not pids:
        parser.print_help()
        print("\nError: Please specify problems to crawl")
        return

    print(f"Will crawl {len(pids)} problems from LibreOJ")
    print("=" * 50)

    problems = await crawl_problems(pids, args.import_to_db)

    print("\n" + "=" * 50)
    print(f"Crawled {len(problems)}/{len(pids)} problems successfully")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)
        print(f"Saved to: {args.output}")

    if args.import_to_db:
        stats = await import_problems(problems, args.course)
        print(f"\nImport Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Imported: {stats['imported']}")
        print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    asyncio.run(main())
