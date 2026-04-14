"""
Batch LOJ Problem Downloader with Embedding Generation

Downloads problems from LibreOJ and generates vector embeddings for semantic search.

Usage:
    # Download 100 problems starting from #1
    python -m app.scripts.batch_import_loj --start 1 --count 100

    # Download with embedding generation
    python -m app.scripts.batch_import_loj --start 1 --count 100 --embed

    # Download and assign to course
    python -m app.scripts.batch_import_loj --start 1 --count 100 --embed --course DSA
"""

import asyncio
import json
import argparse
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise
from app.config import get_settings

settings = get_settings()


# LOJ API endpoints
LOJ_API_URL = "https://api.loj.ac"

# Rate limiting
REQUEST_DELAY = 0.2  # seconds between requests

# LOJ 题目编号规则:
# 1-20: 基础题，但编号不连续
# 100+: 模板题和算法题，编号较连续
# 建议: 从 100 开始下载

# 已知的有效题目编号范围
RECOMMENDED_RANGES = [
    (1, 20),      # 基础题（部分跳过）
    (100, 7000),  # 主题目库（推荐）
]


async def api_request(
    session: aiohttp.ClientSession,
    endpoint: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Make a POST request to LOJ API"""
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
    """Get detailed problem information"""
    try:
        result = await api_request(session, "/api/problem/getProblem", {
            "displayId": pid,
            "localizedContentsOfAllLocales": True,
            "tagsOfLocale": "zh_CN",
            "samples": True,
            "judgeInfo": True,
            "testData": True,
            "additionalFiles": False,
        })

        if not result.get("localizedContentsOfAllLocales"):
            return None

        return result
    except Exception as e:
        print(f"  Error fetching problem {pid}: {e}")
        return None


async def download_test_data(
    session: aiohttp.ClientSession,
    problem_id: int,
    test_files: List[Dict[str, Any]]
) -> Dict[str, bytes]:
    """Download test data files with optimized concurrency"""
    if not test_files:
        return {}

    # 限制最多下载前 10 个测试文件（足够验证代码正确性）
    MAX_FILES = 10
    files_to_download = test_files[:MAX_FILES]

    try:
        result = await api_request(session, "/api/problem/downloadProblemFiles", {
            "problemId": problem_id,
            "type": "TestData",
            "filenameList": [f["filename"] for f in files_to_download],
        })

        if result.get("error"):
            return {}

        files = {}
        download_info = result.get("downloadInfo", [])

        # 使用信号量限制并发数
        sem = asyncio.Semaphore(3)  # 最多3个并发下载

        async def download_one(info):
            async with sem:
                try:
                    async with session.get(
                        info["downloadUrl"],
                        timeout=aiohttp.ClientTimeout(total=5)  # 5秒超时
                    ) as response:
                        if response.status == 200:
                            return info["filename"], await response.read()
                except asyncio.TimeoutError:
                    pass  # 超时就跳过
                except Exception:
                    pass
            return None, None

        # 并行下载
        tasks = [download_one(info) for info in download_info]
        results = await asyncio.gather(*tasks)

        for filename, content in results:
            if filename and content:
                files[filename] = content

        return files
    except Exception as e:
        print(f"  Download error: {e}")
        return {}


def parse_content_sections(problem: Dict[str, Any]) -> tuple[str, List[Dict[str, str]]]:
    """Parse problem content and samples"""
    samples = []
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

    description_parts = []
    for section in content.get("contentSections", []):
        section_type = section.get("type", "")
        section_title = section.get("sectionTitle", "")
        section_text = section.get("text", "")

        if section_type == "Sample":
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


def parse_test_cases(test_files: Dict[str, bytes]) -> List[Dict[str, str]]:
    """Parse test cases from downloaded files"""
    test_cases = []
    input_files = {}
    output_files = {}

    for filename, content in test_files.items():
        lower_name = filename.lower()
        if "input" in lower_name or lower_name.endswith(".in"):
            input_files[filename] = content
        elif "output" in lower_name or lower_name.endswith(".out") or lower_name.endswith(".ans"):
            output_files[filename] = content

    def extract_number(name: str) -> int:
        match = re.search(r'(\d+)', name)
        return int(match.group(1)) if match else 0

    input_list = sorted(input_files.items(), key=lambda x: extract_number(x[0]))
    output_list = sorted(output_files.items(), key=lambda x: extract_number(x[0]))

    for i, (inp_name, inp_content) in enumerate(input_list):
        if i < len(output_list):
            out_content = output_list[i][1]
        else:
            base_name = inp_name.rsplit('.', 1)[0]
            out_name = base_name + ".out"
            out_content = test_files.get(out_name, test_files.get(base_name + ".ans", b""))

        test_cases.append({
            "input": inp_content.decode('utf-8', errors='replace'),
            "output": out_content.decode('utf-8', errors='replace'),
            "name": f"test_{i+1}"
        })

    return test_cases


def build_text_for_embedding(problem: Dict[str, Any]) -> str:
    """Build text content for embedding generation"""
    parts = []

    # Title
    contents = problem.get("localizedContentsOfAllLocales", [])
    for c in contents:
        if c.get("locale") == "zh_CN":
            parts.append(f"题目: {c.get('title', '')}")
            break

    # Tags
    tags = [tag.get("name", "") for tag in problem.get("tagsOfLocale", [])]
    if tags:
        parts.append(f"标签: {', '.join(tags)}")

    # Content sections
    for c in contents:
        if c.get("locale") == "zh_CN":
            for section in c.get("contentSections", []):
                if section.get("type") != "Sample":
                    if section.get("sectionTitle"):
                        parts.append(f"{section['sectionTitle']}: {section.get('text', '')}")
                    elif section.get("text"):
                        parts.append(section["text"])
            break

    return "\n".join(parts)


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using OpenAI API or local model"""
    if not text.strip():
        return None

    try:
        # Try OpenAI first
        import openai

        api_key = settings.AI_API_KEY
        base_url = settings.AI_BASE_URL

        if api_key:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url if base_url else None
            )

            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limit text length
            )

            return response.data[0].embedding
    except Exception as e:
        print(f"  Embedding error: {str(e)[:50]}")

    # Fallback: return None (can implement local embedding later)
    return None


def convert_loj_to_exercise(
    problem: Dict[str, Any],
    test_cases: List[Dict[str, str]],
    embedding: Optional[List[float]] = None
) -> Exercise:
    """Convert LOJ problem to Exercise model"""
    meta = problem.get("meta", {})
    display_id = meta.get("displayId", 0)

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

    # Judge info
    judge = problem.get("judgeInfo", {})
    time_limit = judge.get("timeLimit", 1000)
    memory_limit = judge.get("memoryLimit", 256)

    # Parse content
    description, samples = parse_content_sections(problem)

    # Build content
    content = {
        "title": title,
        "description": description,
        "time_limit": time_limit / 1000,
        "memory_limit": memory_limit,
        "source": f"LibreOJ #{display_id}",
        "loj_url": f"https://loj.ac/p/{display_id}",
        "submission_count": meta.get("submissionCount", 0),
        "accepted_count": meta.get("acceptedSubmissionCount", 0),
    }

    if samples:
        content["samples"] = samples

    # Estimate difficulty
    difficulty = 2
    accepted = meta.get("acceptedSubmissionCount", 0)
    submitted = meta.get("submissionCount", 1)
    if submitted > 0:
        rate = accepted / submitted
        if rate < 0.1:
            difficulty = 5
        elif rate < 0.2:
            difficulty = 4
        elif rate < 0.4:
            difficulty = 3
        elif rate < 0.6:
            difficulty = 2
        else:
            difficulty = 1

    # Create exercise
    exercise = Exercise(
        source="loj",
        source_id=str(display_id),
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=tags.copy(),
        content=content,
        test_cases=test_cases if test_cases else None,
        embedding=json.dumps(embedding) if embedding else None,
        is_verified=True,
    )

    return exercise


async def download_and_import_problem(
    session: aiohttp.ClientSession,
    pid: int,
    generate_embed: bool = False
) -> Optional[Exercise]:
    """Download a single problem and create Exercise"""
    problem = await get_problem_info(session, pid)

    if not problem:
        return None

    meta = problem.get("meta", {})
    internal_id = meta.get("id", 0)

    # Get title for logging
    contents = problem.get("localizedContentsOfAllLocales", [])
    title = "Unknown"
    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", "Unknown")
            break

    # Download test data
    test_files = problem.get("testData", [])
    downloaded_files = await download_test_data(session, internal_id, test_files)

    # Parse test cases
    test_cases = parse_test_cases(downloaded_files)

    # Generate embedding
    embedding = None
    if generate_embed:
        text = build_text_for_embedding(problem)
        embedding = await generate_embedding(text)

    # Create exercise
    exercise = convert_loj_to_exercise(problem, test_cases, embedding)

    return exercise


async def batch_import(
    start_id: int,
    count: int,
    generate_embed: bool = False,
    course_code: Optional[str] = None
) -> Dict[str, int]:
    """Batch download and import problems"""
    stats = {
        "total": count,
        "imported": 0,
        "errors": 0,
        "with_test_cases": 0,
        "with_embeddings": 0,
    }

    async with aiohttp.ClientSession() as session:
        async with AsyncSessionLocal() as db:
            from app.models.course import Course
            from sqlalchemy import select

            # Get course ID
            course_id = None
            if course_code:
                result = await db.execute(
                    select(Course).where(Course.code == course_code)
                )
                course = result.scalar_one_or_none()
                if course:
                    course_id = course.id

            end_id = start_id + count - 1
            print(f"Downloading problems #{start_id} to #{end_id}...")
            print("=" * 60)

            for i, pid in enumerate(range(start_id, start_id + count)):
                progress = f"[{i+1}/{count}]"
                print(f"{progress} Problem #{pid}...", end=" ")

                try:
                    exercise = await download_and_import_problem(session, pid, generate_embed)

                    if exercise:
                        db.add(exercise)
                        stats["imported"] += 1

                        if exercise.test_cases:
                            stats["with_test_cases"] += 1

                        if exercise.embedding:
                            stats["with_embeddings"] += 1

                        print(f"OK {exercise.content.get('title', 'Unknown')[:30]} ({len(exercise.test_cases or [])} tests)")
                    else:
                        print("SKIP (not found)")

                except Exception as e:
                    print(f"ERR: {e}")
                    stats["errors"] += 1

                # Rate limiting
                await asyncio.sleep(REQUEST_DELAY)

                # Commit every 10 problems
                if (i + 1) % 10 == 0:
                    await db.commit()
                    print(f"  → Committed {i+1} problems")

            # Final commit
            await db.commit()

    return stats


def print_stats(stats: Dict[str, int]):
    """Print import statistics"""
    print("\n" + "=" * 60)
    print("Import Statistics")
    print("=" * 60)
    print(f"Total requested:  {stats['total']}")
    print(f"Imported:         {stats['imported']}")
    print(f"Errors:           {stats['errors']}")
    print(f"With test cases:  {stats['with_test_cases']}")
    print(f"With embeddings:  {stats['with_embeddings']}")
    print("=" * 60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Batch download problems from LibreOJ with embeddings"
    )
    parser.add_argument(
        "--start", "-s",
        type=int,
        default=1,
        help="Starting problem ID (default: 1)"
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=100,
        help="Number of problems to download (default: 100)"
    )
    parser.add_argument(
        "--embed", "-e",
        action="store_true",
        help="Generate embeddings for semantic search"
    )
    parser.add_argument(
        "--course",
        type=str,
        choices=["C", "CPP", "Python", "Java", "Rust", "DSA", "ADA", "DiscreteMath"],
        help="Assign problems to this course"
    )

    args = parser.parse_args()

    print(f"Batch LOJ Importer")
    print(f"Start: #{args.start}")
    print(f"Count: {args.count}")
    print(f"Embeddings: {'Yes' if args.embed else 'No'}")
    print(f"Course: {args.course or 'None'}")
    print()

    stats = await batch_import(
        args.start,
        args.count,
        args.embed,
        args.course
    )

    print_stats(stats)


if __name__ == "__main__":
    asyncio.run(main())
