"""
Codeforces Problem Crawler

This script fetches problems from Codeforces using the official API.
API Documentation: https://codeforces.com/apiHelp

Usage:
    # Get all problems
    python -m app.scripts.crawl_codeforces --all

    # Get problems by tags
    python -m app.scripts.crawl_codeforces --tags implementation math

    # Get problems from specific contest
    python -m app.scripts.crawl_codeforces --contest 1900

    # Import to database
    python -m app.scripts.crawl_codeforces --all --import
"""

import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise


# Codeforces API base URL
CF_API_URL = "https://codeforces.com/api"

# Rate limit: 1 request per 2 seconds
CF_RATE_LIMIT = 2.0


async def fetch_api(
    session: aiohttp.ClientSession,
    method: str,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Fetch data from Codeforces API

    Args:
        session: aiohttp session
        method: API method name
        params: Query parameters

    Returns:
        API response data
    """
    url = f"{CF_API_URL}/{method}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with session.get(url, params=params, headers=headers) as response:
        response.raise_for_status()
        data = await response.json()

        if data.get("status") == "FAILED":
            raise Exception(f"API error: {data.get('comment', 'Unknown error')}")

        return data.get("result", {})


async def get_all_problems(
    session: aiohttp.ClientSession,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all problems from Codeforces problemset

    Args:
        session: aiohttp session
        tags: Optional list of tags to filter

    Returns:
        List of problems with statistics
    """
    params = {}
    if tags:
        params["tags"] = ";".join(tags)

    result = await fetch_api(session, "problemset.problems", params)

    problems = result.get("problems", [])
    statistics = {s["index"]: s for s in result.get("problemStatistics", [])}

    # Merge problem info with statistics
    for problem in problems:
        contest_id = problem.get("contestId")
        index = problem.get("index")
        stat_key = f"{contest_id}{index}"

        if stat_key in statistics:
            problem["solvedCount"] = statistics[stat_key].get("solvedCount", 0)

    return problems


async def get_contest_problems(
    session: aiohttp.ClientSession,
    contest_id: int
) -> List[Dict[str, Any]]:
    """
    Get problems from a specific contest

    Args:
        session: aiohttp session
        contest_id: Contest ID

    Returns:
        List of problems in the contest
    """
    params = {
        "contestId": contest_id,
        "from": 1,
        "count": 100  # Usually contests have < 10 problems
    }

    result = await fetch_api(session, "contest.standings", params)
    return result.get("problems", [])


async def get_contest_list(
    session: aiohttp.ClientSession,
    gym: bool = False
) -> List[Dict[str, Any]]:
    """
    Get list of all contests

    Args:
        session: aiohttp session
        gym: Include gym contests

    Returns:
        List of contests
    """
    params = {"gym": "true" if gym else "false"}
    return await fetch_api(session, "contest.list", params)


def map_difficulty(rating: Optional[int]) -> int:
    """
    Map Codeforces rating to our 1-5 difficulty scale

    CF Rating ranges:
    - Gray (0-1199): 800-900
    - Green (1200-1399): 1000-1100
    - Cyan (1400-1599): 1200-1300
    - Blue (1600-1899): 1400-1600
    - Purple (1900-2099): 1700-1800
    - Yellow (2100-2299): 1900-2100
    - Red (2300-2399): 2200-2400
    - Orange (2400+): 2500+

    Our scale: 1 (easy) to 5 (expert)
    """
    if rating is None:
        return 2  # Default medium

    if rating < 1000:
        return 1  # Beginner
    elif rating < 1400:
        return 2  # Elementary
    elif rating < 1800:
        return 3  # Intermediate
    elif rating < 2200:
        return 4  # Advanced
    else:
        return 5  # Expert


def detect_course_from_tags(tags: List[str]) -> Optional[str]:
    """
    Detect course from problem tags

    Args:
        tags: List of problem tags

    Returns:
        Course code or None
    """
    tag_mapping = {
        "DSA": ["data structures", "trees", "graphs", "dfs and similar",
                "binary search", "sorting", "hashing", "stack", "queue"],
        "ADA": ["dp", "greedy", "divide and conquer", "binary search",
                "ternary search", "two pointers", "meet-in-the-middle"],
        "DiscreteMath": ["math", "number theory", "combinatorics",
                        "probability", "geometry", "algebra"],
        "C": ["c++", "pointers", "memory"],
        "Python": ["python"],
    }

    tags_lower = [t.lower() for t in tags]

    for course, course_tags in tag_mapping.items():
        for ct in course_tags:
            if ct.lower() in tags_lower:
                return course

    return None


def extract_knowledge_points(tags: List[str]) -> List[str]:
    """
    Convert CF tags to knowledge points

    Args:
        tags: CF tags

    Returns:
        Knowledge point list
    """
    # Map CF tags to Chinese knowledge points
    tag_mapping = {
        "implementation": "实现",
        "math": "数学",
        "greedy": "贪心",
        "dp": "动态规划",
        "data structures": "数据结构",
        "graphs": "图论",
        "trees": "树",
        "binary search": "二分查找",
        "sorting": "排序",
        "strings": "字符串",
        "number theory": "数论",
        "combinatorics": "组合数学",
        "geometry": "几何",
        "dfs and similar": "深度优先搜索",
        "bfs": "广度优先搜索",
        "bitmasks": "位运算",
        "constructive algorithms": "构造",
        "two pointers": "双指针",
        "hashing": "哈希",
        "divide and conquer": "分治",
        "recursion": "递归",
    }

    points = []
    for tag in tags:
        if tag.lower() in tag_mapping:
            points.append(tag_mapping[tag.lower()])
        else:
            points.append(tag)

    return list(set(points))


def convert_cf_to_exercise(
    problem: Dict[str, Any],
    course_id: Optional[int] = None
) -> Exercise:
    """
    Convert Codeforces problem to Exercise model

    Args:
        problem: CF problem data
        course_id: Optional course assignment

    Returns:
        Exercise instance
    """
    # Extract rating (difficulty)
    rating = problem.get("rating")
    difficulty = map_difficulty(rating)

    # Build content
    contest_id = problem.get("contestId")
    index = problem.get("index")

    content = {
        "title": problem.get("name", "Untitled"),
        "contest_id": contest_id,
        "index": index,
        "type": problem.get("type", "PROGRAMMING"),
        "points": problem.get("points"),
        "rating": rating,
        "cf_url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}" if contest_id else None,
        "source": f"Codeforces #{contest_id}{index}" if contest_id else "Codeforces",
    }

    # Get tags
    tags = problem.get("tags", [])
    knowledge_points = extract_knowledge_points(tags)

    # Detect course
    detected_course = detect_course_from_tags(tags)

    # Create exercise
    exercise = Exercise(
        source="codeforces",
        source_id=f"{contest_id}{index}" if contest_id else None,
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=knowledge_points,
        content=content,
        test_cases=None,  # CF doesn't provide test data via API
        hints=None,
        is_verified=True,
    )

    return exercise


async def import_problems(
    problems: List[Dict[str, Any]],
    course_code: Optional[str] = None
) -> Dict[str, int]:
    """
    Import problems to database

    Args:
        problems: List of CF problems
        course_code: Optional course to assign

    Returns:
        Statistics
    """
    stats = {
        "total": len(problems),
        "imported": 0,
        "errors": 0,
        "by_difficulty": {},
        "by_course": {},
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
                exercise = convert_cf_to_exercise(problem, course_id)
                session.add(exercise)

                stats["imported"] += 1
                diff = exercise.difficulty
                stats["by_difficulty"][diff] = stats["by_difficulty"].get(diff, 0) + 1

                course = exercise.knowledge_points[0] if exercise.knowledge_points else "unknown"
                stats["by_course"][course] = stats["by_course"].get(course, 0) + 1

            except Exception as e:
                print(f"Error importing problem: {e}")
                stats["errors"] += 1

        await session.commit()

    return stats


def print_stats(stats: Dict[str, int]):
    """Print import statistics"""
    print("\n" + "=" * 50)
    print("Import Statistics")
    print("=" * 50)
    print(f"Total problems:  {stats['total']}")
    print(f"Imported:        {stats['imported']}")
    print(f"Errors:          {stats['errors']}")

    if stats.get("by_difficulty"):
        print("\nBy Difficulty:")
        for diff, count in sorted(stats["by_difficulty"].items()):
            print(f"  Level {diff}: {count}")

    print("=" * 50)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fetch problems from Codeforces using official API"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Fetch all problems from problemset"
    )
    parser.add_argument(
        "--tags", "-t",
        type=str,
        nargs="+",
        help="Filter problems by tags (e.g., --tags dp math)"
    )
    parser.add_argument(
        "--contest", "-c",
        type=int,
        help="Fetch problems from a specific contest ID"
    )
    parser.add_argument(
        "--list-contests",
        action="store_true",
        help="List all contests"
    )
    parser.add_argument(
        "--import",
        dest="import_to_db",
        action="store_true",
        help="Import fetched problems to database"
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
        help="Output JSON file for fetched data"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Limit number of problems to fetch (0 = no limit)"
    )

    args = parser.parse_args()

    if not any([args.all, args.tags, args.contest, args.list_contests]):
        parser.print_help()
        print("\nError: Please specify what to fetch (--all, --tags, --contest, or --list-contests)")
        return

    async with aiohttp.ClientSession() as session:
        problems = []

        if args.list_contests:
            print("Fetching contest list...")
            contests = await get_contest_list(session)
            print(f"\nFound {len(contests)} contests:")
            for c in contests[:20]:
                print(f"  #{c.get('id'):5d} | {c.get('name', 'Unknown')[:50]}")
            print("  ... (showing first 20)")
            return

        if args.all or args.tags:
            print("Fetching problems from Codeforces problemset...")
            if args.tags:
                print(f"Filtering by tags: {args.tags}")
            problems = await get_all_problems(session, args.tags)

        if args.contest:
            print(f"Fetching problems from contest #{args.contest}...")
            contest_problems = await get_contest_problems(session, args.contest)
            problems.extend(contest_problems)

        # Apply limit
        if args.limit > 0:
            problems = problems[:args.limit]

        print(f"\nFetched {len(problems)} problems")

        # Show sample
        if problems:
            print("\nSample problems:")
            for p in problems[:5]:
                rating = p.get("rating", "N/A")
                tags = ", ".join(p.get("tags", [])[:3])
                print(f"  {p.get('contestId', '')}{p.get('index', '')}: {p.get('name', 'Unknown')[:40]}")
                print(f"    Rating: {rating} | Tags: {tags}")

        # Save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(problems, f, ensure_ascii=False, indent=2)
            print(f"\nSaved to: {args.output}")

        # Import to database
        if args.import_to_db and problems:
            print("\nImporting to database...")
            stats = await import_problems(problems, args.course)
            print_stats(stats)


if __name__ == "__main__":
    asyncio.run(main())
