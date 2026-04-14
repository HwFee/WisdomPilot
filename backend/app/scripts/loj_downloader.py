"""
LibreOJ (LOJ) Problem Downloader with Test Data

Based on hydro-dev/loj-download: https://github.com/hydro-dev/loj-download
This script downloads problems from LOJ including test data.

Usage:
    # Download a single problem
    python -m app.scripts.loj_downloader --problem 1

    # Download multiple problems
    python -m app.scripts.loj_downloader --problems 1 2 3 4 5

    # Download a range of problems
    python -m app.scripts.loj_downloader --range 1 100

    # Import downloaded problems to database
    python -m app.scripts.loj_downloader --problems 1 2 3 --import
"""

import asyncio
import json
import argparse
import zipfile
import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise


# LOJ API endpoints
LOJ_API_URL = "https://api.loj.ac"
LOJ_PROBLEM_URL = "https://loj.ac/p/{pid}"

# Download directory
DOWNLOAD_DIR = Path(__file__).parent.parent.parent / "downloads" / "loj"


async def api_request(
    session: aiohttp.ClientSession,
    endpoint: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make a POST request to LOJ API

    Args:
        session: aiohttp session
        endpoint: API endpoint (e.g., "/api/problem/getProblem")
        data: Request body

    Returns:
        API response data
    """
    url = f"{LOJ_API_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with session.post(url, json=data, headers=headers) as response:
        response.raise_for_status()
        return await response.json()


async def get_problem_info(
    session: aiohttp.ClientSession,
    pid: int
) -> Optional[Dict[str, Any]]:
    """
    Get detailed problem information including test data metadata

    Args:
        session: aiohttp session
        pid: Problem display ID

    Returns:
        Problem data or None if not found
    """
    try:
        result = await api_request(session, "/api/problem/getProblem", {
            "displayId": pid,
            "localizedContentsOfAllLocales": True,
            "tagsOfLocale": "zh_CN",
            "samples": True,
            "judgeInfo": True,
            "testData": True,
            "additionalFiles": True,
        })

        # Check if problem exists
        if not result.get("localizedContentsOfAllLocales"):
            return None

        return result
    except Exception as e:
        print(f"Error fetching problem {pid}: {e}")
        return None


async def download_test_data(
    session: aiohttp.ClientSession,
    problem_id: int,
    test_files: List[Dict[str, Any]]
) -> Dict[str, bytes]:
    """
    Download test data files

    Args:
        session: aiohttp session
        problem_id: Internal problem ID (not display ID)
        test_files: List of test file metadata

    Returns:
        Dict mapping filename to file content
    """
    if not test_files:
        return {}

    try:
        result = await api_request(session, "/api/problem/downloadProblemFiles", {
            "problemId": problem_id,
            "type": "TestData",
            "filenameList": [f["filename"] for f in test_files],
        })

        if result.get("error"):
            print(f"Error downloading test data: {result['error']}")
            return {}

        files = {}
        for info in result.get("downloadInfo", []):
            download_url = info["downloadUrl"]
            filename = info["filename"]

            async with session.get(download_url) as response:
                if response.status == 200:
                    files[filename] = await response.read()

        return files
    except Exception as e:
        print(f"Error downloading test files: {e}")
        return {}


def parse_content_sections(
    problem: Dict[str, Any]
) -> tuple[str, List[Dict[str, str]]]:
    """
    Parse problem content and samples from LOJ format

    Args:
        problem: Problem data from API

    Returns:
        Tuple of (description, samples)
    """
    samples = []

    # Find Chinese content first, fallback to English
    contents = problem.get("localizedContentsOfAllLocales", [])
    content = None
    for c in contents:
        if c.get("locale") == "zh_CN":
            content = c
            break
    if not content and contents:
        content = contents[0]

    if not content:
        return "", []

    # Parse sections
    description_parts = []
    for section in content.get("contentSections", []):
        section_type = section.get("type", "")
        section_title = section.get("sectionTitle", "")
        section_text = section.get("text", "")

        if section_type == "Sample":
            # Handle sample
            sample_id = section.get("sampleId", 0)
            sample_data = problem.get("samples", [])[sample_id] if sample_id < len(problem.get("samples", [])) else None

            if sample_data:
                samples.append({
                    "input": sample_data.get("inputData", ""),
                    "output": sample_data.get("outputData", ""),
                })

            if section_text:
                description_parts.append(f"## 样例\n{section_text}")
        else:
            if section_title:
                description_parts.append(f"## {section_title}\n{section_text}")
            elif section_text:
                description_parts.append(section_text)

    return "\n\n".join(description_parts), samples


def parse_test_cases(
    test_files: Dict[str, bytes],
    judge_info: Optional[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Parse test cases from downloaded test files

    Args:
        test_files: Dict mapping filename to content
        judge_info: Judge configuration

    Returns:
        List of test cases
    """
    test_cases = []

    # Find input/output file pairs
    input_files = {}
    output_files = {}

    for filename, content in test_files.items():
        lower_name = filename.lower()
        if "input" in lower_name or lower_name.endswith(".in"):
            input_files[filename] = content
        elif "output" in lower_name or lower_name.endswith(".out") or lower_name.endswith(".ans"):
            output_files[filename] = content

    # Match input/output pairs by number or name
    def extract_number(name: str) -> int:
        match = re.search(r'(\d+)', name)
        return int(match.group(1)) if match else 0

    # Sort by number
    input_list = sorted(input_files.items(), key=lambda x: extract_number(x[0]))
    output_list = sorted(output_files.items(), key=lambda x: extract_number(x[0]))

    # Pair them up
    for i, (inp_name, inp_content) in enumerate(input_list):
        if i < len(output_list):
            out_content = output_list[i][1]
        else:
            # Try to find matching output
            base_name = inp_name.rsplit('.', 1)[0]
            out_name = base_name + ".out"
            if out_name in test_files:
                out_content = test_files[out_name]
            else:
                out_name = base_name + ".ans"
                out_content = test_files.get(out_name, b"")

        test_cases.append({
            "input": inp_content.decode('utf-8', errors='replace'),
            "output": out_content.decode('utf-8', errors='replace'),
            "name": f"test_{i+1}"
        })

    return test_cases


def convert_loj_to_exercise(
    problem: Dict[str, Any],
    test_cases: List[Dict[str, str]]
) -> Exercise:
    """
    Convert LOJ problem to Exercise model

    Args:
        problem: Problem data from API
        test_cases: Parsed test cases

    Returns:
        Exercise instance
    """
    # Get problem metadata
    meta = problem.get("meta", {})
    display_id = meta.get("displayId", 0)
    internal_id = meta.get("id", 0)

    # Get title
    contents = problem.get("localizedContentsOfAllLocales", [])
    title = "Untitled"
    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", "Untitled")
            break
    if title == "Untitled" and contents:
        title = contents[0].get("title", "Untitled")

    # Get tags
    tags = [tag.get("name", "") for tag in problem.get("tagsOfLocale", [])]

    # Get judge info
    judge = problem.get("judgeInfo", {})
    time_limit = judge.get("timeLimit", 1000)  # ms
    memory_limit = judge.get("memoryLimit", 256)  # MB

    # Parse content
    description, samples = parse_content_sections(problem)

    # Build content dict
    content = {
        "title": title,
        "description": description,
        "time_limit": time_limit / 1000,  # Convert to seconds
        "memory_limit": memory_limit,
        "source": f"LibreOJ #{display_id}",
        "loj_url": f"https://loj.ac/p/{display_id}",
        "submission_count": meta.get("submissionCount", 0),
        "accepted_count": meta.get("acceptedSubmissionCount", 0),
    }

    # Add samples to content
    if samples:
        content["samples"] = samples

    # Estimate difficulty from tags and acceptance rate
    difficulty = 2  # Default
    accepted = meta.get("acceptedSubmissionCount", 0)
    submitted = meta.get("submissionCount", 1)
    if submitted > 0:
        rate = accepted / submitted
        if rate < 0.1:
            difficulty = 5  # Very hard
        elif rate < 0.2:
            difficulty = 4  # Hard
        elif rate < 0.4:
            difficulty = 3  # Medium
        elif rate < 0.6:
            difficulty = 2  # Easy
        else:
            difficulty = 1  # Very easy

    # Map tags to knowledge points
    knowledge_points = tags.copy()

    # Create exercise
    exercise = Exercise(
        source="loj",
        source_id=str(display_id),
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=knowledge_points,
        content=content,
        test_cases=test_cases if test_cases else None,
        is_verified=True,
    )

    return exercise


async def download_problem(
    session: aiohttp.ClientSession,
    pid: int,
    save_dir: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Download a single problem with test data

    Args:
        session: aiohttp session
        pid: Problem display ID
        save_dir: Optional directory to save downloaded files

    Returns:
        Problem data with test cases
    """
    print(f"Downloading problem #{pid}...")

    # Get problem info
    problem = await get_problem_info(session, pid)

    if not problem:
        print(f"  Problem #{pid} not found")
        return None

    # Get problem metadata
    meta = problem.get("meta", {})
    internal_id = meta.get("id", 0)
    title = "Unknown"
    contents = problem.get("localizedContentsOfAllLocales", [])
    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", "Unknown")
            break

    print(f"  Found: {title}")

    # Download test data
    test_files = problem.get("testData", [])
    downloaded_files = await download_test_data(session, internal_id, test_files)

    print(f"  Downloaded {len(downloaded_files)} test files")

    # Parse test cases
    test_cases = parse_test_cases(downloaded_files, problem.get("judgeInfo"))

    print(f"  Parsed {len(test_cases)} test cases")

    # Save to disk if requested
    if save_dir:
        problem_dir = save_dir / str(pid)
        problem_dir.mkdir(parents=True, exist_ok=True)

        # Save problem info
        with open(problem_dir / "problem.json", 'w', encoding='utf-8') as f:
            json.dump(problem, f, ensure_ascii=False, indent=2)

        # Save test files
        test_dir = problem_dir / "testdata"
        test_dir.mkdir(exist_ok=True)
        for filename, content in downloaded_files.items():
            with open(test_dir / filename, 'wb') as f:
                f.write(content)

    return {
        "problem": problem,
        "test_cases": test_cases,
    }


async def download_problems(
    pids: List[int],
    save_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Download multiple problems

    Args:
        pids: List of problem IDs
        save_dir: Directory to save downloaded files

    Returns:
        List of downloaded problems
    """
    results = []

    async with aiohttp.ClientSession() as session:
        for pid in pids:
            result = await download_problem(session, pid, save_dir)
            if result:
                results.append(result)

            # Be nice to the server
            await asyncio.sleep(0.5)

    return results


async def import_problems(
    problems: List[Dict[str, Any]],
    course_code: Optional[str] = None
) -> Dict[str, int]:
    """
    Import downloaded problems to database

    Args:
        problems: List of downloaded problem data
        course_code: Optional course assignment

    Returns:
        Statistics
    """
    stats = {
        "total": len(problems),
        "imported": 0,
        "errors": 0,
        "with_test_cases": 0,
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

        for data in problems:
            try:
                problem = data["problem"]
                test_cases = data["test_cases"]

                exercise = convert_loj_to_exercise(problem, test_cases)
                session.add(exercise)

                stats["imported"] += 1
                if test_cases:
                    stats["with_test_cases"] += 1

            except Exception as e:
                print(f"Error importing problem: {e}")
                stats["errors"] += 1

        await session.commit()

    return stats


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download problems from LibreOJ with test data"
    )
    parser.add_argument(
        "--problem", "-p",
        type=int,
        help="Single problem ID to download"
    )
    parser.add_argument(
        "--problems",
        type=int,
        nargs="+",
        help="Multiple problem IDs to download"
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
        help="Import downloaded problems to database"
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
        help="Output directory for downloaded files"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Limit number of problems to download (0 = no limit)"
    )

    args = parser.parse_args()

    # Determine problem IDs to download
    pids = []
    if args.problem:
        pids.append(args.problem)
    if args.problems:
        pids.extend(args.problems)
    if args.range:
        pids.extend(range(args.range[0], args.range[1] + 1))

    # Remove duplicates and sort
    pids = sorted(set(pids))

    # Apply limit
    if args.limit > 0:
        pids = pids[:args.limit]

    if not pids:
        parser.print_help()
        print("\nError: Please specify problems to download")
        return

    print(f"Will download {len(pids)} problems from LibreOJ")
    print("=" * 50)

    # Set output directory
    output_dir = args.output or DOWNLOAD_DIR

    # Download problems
    problems = await download_problems(pids, output_dir)

    print("\n" + "=" * 50)
    print(f"Downloaded {len(problems)}/{len(pids)} problems")

    # Import to database
    if args.import_to_db and problems:
        print("\nImporting to database...")
        stats = await import_problems(problems, args.course)
        print(f"\nImport Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Imported: {stats['imported']}")
        print(f"  With test cases: {stats['with_test_cases']}")
        print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    asyncio.run(main())
