"""
LibreOJ (LOJ) Problem Crawler - with full test data download

This script crawls problems from LibreOJ (https://loj.ac) including:
- Problem description, title, tags
- Full test data (.in/.out files)
- Difficulty mapping

Based on: https://github.com/hydro-dev/loj-download

Usage:
    # Crawl problems by difficulty range and import
    python -m app.scripts.crawl_loj --difficulty 1 2 --count 50 --import

    # Crawl specific problem IDs
    python -m app.scripts.crawl_loj --problems 1 2 3 --import

    # Crawl a range and import
    python -m app.scripts.crawl_loj --range 1 100 --import
"""

import asyncio
import json
import re
import socket
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import aiohttp

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise


# LOJ API endpoints
LOJ_API_URL = "https://api.loj.ac"


async def fetch_post(
    session: aiohttp.ClientSession,
    url: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """POST request to LOJ API"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    async with session.post(url, json=data, headers=headers) as response:
        response.raise_for_status()
        return await response.json()


async def get_problem_full_detail(
    session: aiohttp.ClientSession,
    pid: int
) -> Optional[Dict[str, Any]]:
    """
    Get full problem details including test data file list.

    Uses LOJ v3 API: POST /api/problem/getProblem
    """
    url = f"{LOJ_API_URL}/api/problem/getProblem"
    payload = {
        "displayId": pid,
        "localizedContentsOfAllLocales": True,
        "tagsOfLocale": "zh_CN",
        "samples": True,
        "judgeInfo": True,
        "testData": True,
        "additionalFiles": True,
    }

    try:
        result = await fetch_post(session, url, payload)
        if not result.get("localizedContentsOfAllLocales"):
            return None  # Problem doesn't exist
        return result
    except Exception as e:
        print(f"  Error fetching problem {pid} detail: {e}")
        return None


async def download_single_file(
    session: aiohttp.ClientSession,
    download_url: str,
    filename: str,
) -> Tuple[str, bytes]:
    """Download a single file."""
    try:
        async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            resp.raise_for_status()
            content = await resp.read()
            return (filename, content)
    except Exception as e:
        print(f"  Error downloading {filename}: {e}")
        return (filename, b"")


async def download_test_data_files(
    session: aiohttp.ClientSession,
    problem_meta_id: int,
    test_data_files: List[Dict[str, Any]]
) -> List[Tuple[str, bytes]]:
    """
    Download test data files from LOJ (concurrently).

    Uses LOJ v3 API: POST /api/problem/downloadProblemFiles
    Returns list of (filename, content_bytes).
    """
    if not test_data_files:
        return []

    url = f"{LOJ_API_URL}/api/problem/downloadProblemFiles"
    payload = {
        "problemId": problem_meta_id,
        "type": "TestData",
        "filenameList": [f["filename"] for f in test_data_files],
    }

    try:
        result = await fetch_post(session, url, payload)
        if result.get("error"):
            print(f"  API error: {result['error']}")
            return []

        download_info = result.get("downloadInfo", [])

        # Download all files concurrently
        tasks = []
        for info in download_info:
            download_url = info.get("downloadUrl")
            filename = info.get("filename")
            if download_url:
                tasks.append(download_single_file(session, download_url, filename))

        files = await asyncio.gather(*tasks)
        # Filter out failed downloads (empty content)
        return [(f[0], f[1]) for f in files if f[1]]

    except Exception as e:
        print(f"  Error downloading test data: {e}")
        return []


def parse_test_cases_from_files(files: List[Tuple[str, bytes]]) -> List[Dict[str, str]]:
    """
    Parse .in/.out file pairs into test_cases format.

    LOJ test data naming conventions:
    - 1.in / 1.out
    - input1.txt / output1.txt
    - data.in / data.out
    - etc.
    """
    # Group files by base name
    inputs = {}   # base_name -> content
    outputs = {}  # base_name -> content

    for filename, content in files:
        name = filename.lower()
        text = content.decode('utf-8', errors='replace')

        # Determine if input or output
        if name.endswith('.in') or name.endswith('.txt') and ('in' in name or 'input' in name):
            base = re.sub(r'\.(in|txt)$', '', filename, flags=re.I)
            # Remove input/in suffix from base
            base = re.sub(r'(_input|_in|input|in)$', '', base, flags=re.I)
            inputs[base] = text
        elif name.endswith('.out') or name.endswith('.txt') and ('out' in name or 'output' in name):
            base = re.sub(r'\.(out|txt)$', '', filename, flags=re.I)
            # Remove output/out suffix from base
            base = re.sub(r'(_output|_out|output|out)$', '', base, flags=re.I)
            outputs[base] = text
        elif name.endswith('.ans'):
            base = re.sub(r'\.ans$', '', filename, flags=re.I)
            outputs[base] = text
        else:
            # Try to infer from naming pattern
            if re.search(r'\d+\.in', name):
                base = re.sub(r'\.in$', '', filename, flags=re.I)
                inputs[base] = text
            elif re.search(r'\d+\.out', name):
                base = re.sub(r'\.out$', '', filename, flags=re.I)
                outputs[base] = text
            elif 'input' in name:
                base = re.sub(r'input', '', filename, flags=re.I)
                base = re.sub(r'[^\w]', '', base) or '1'
                inputs[base] = text
            elif 'output' in name:
                base = re.sub(r'output', '', filename, flags=re.I)
                base = re.sub(r'[^\w]', '', base) or '1'
                outputs[base] = text

    # Pair input/output by base name
    test_cases = []
    all_bases = set(inputs.keys()) | set(outputs.keys())

    for base in sorted(all_bases, key=lambda x: (len(x), x)):
        inp = inputs.get(base, '')
        out = outputs.get(base, '')
        if inp or out:  # At least one side exists
            test_cases.append({
                "input": inp,
                "output": out,
                "name": base if base else f"test{len(test_cases)+1}"
            })

    return test_cases


def get_loj_difficulty(tags: List[str], pid: int, title: str, time_limit: int, test_case_count: int) -> int:
    """
    Estimate difficulty using multiple signals:

    1. Tag-based estimation (LOJ uses standard OJ difficulty tags)
    2. Problem ID heuristic (earlier problems tend to be simpler)
    3. Title complexity (simple titles like "A+B" indicate easy problems)
    4. Time limit (shorter limits often for simpler problems)
    5. Test case count (fewer test cases often for simpler problems)

    Returns difficulty 1-5.
    """
    # 1. Tag-based estimation
    difficulty_map = {
        "入门": 1, "普及-": 2, "普及/提高-": 3,
        "普及+/提高": 4, "提高+/省选-": 5,
        "省选/NOI-": 5, "NOI": 5, "NOI+/CTSC": 5,
    }
    for tag in tags:
        for key, val in difficulty_map.items():
            if key in tag:
                return min(5, val)

    # 2. Advanced topic tags indicate harder problems
    hard_tags = ["动态规划", "图论", "数据结构", "网络流", "后缀自动机",
                 "树链剖分", "虚树", "FFT", "NTT", "生成函数", "莫比乌斯反演",
                 "矩阵", "线段树", "平衡树", "树状数组", "LCT", "SAM"]
    medium_tags = ["数学", "数论", "几何", "DP", "贪心", "搜索", "二分",
                   "分治", "递推", "博弈论", "组合数学", "线性代数"]

    for tag in tags:
        if any(h in tag for h in hard_tags):
            return 5
    for tag in tags:
        if any(m in tag for m in medium_tags):
            return 4

    # 3. Title-based estimation for very simple problems
    simple_titles = ["A+B", "A + B", "A-B", "A - B", "Hello World",
                     "输入输出", "高精度加法", "高精度减法"]
    title_upper = title.upper()
    for simple in simple_titles:
        if simple.upper() in title_upper:
            return 1

    # 4. Problem ID heuristic (early LOJ problems are simpler)
    if pid <= 10:
        return 1
    elif pid <= 50:
        return 2
    elif pid <= 100:
        return 2

    # 5. Time limit and test case count heuristics
    if time_limit <= 500 and test_case_count <= 5:
        return 2  # Very short time limit often for simple problems

    # 6. Check for "模板" (template) tag - usually medium difficulty
    if any("模板" in tag for tag in tags):
        return 2

    # Default to medium
    return 3


def convert_loj_to_exercise(
    detail: Dict[str, Any],
    test_cases: List[Dict[str, str]],
    pid: int
) -> Exercise:
    """Convert LOJ problem detail to Exercise model."""
    # Get Chinese title
    contents = detail.get("localizedContentsOfAllLocales", [])
    title = f"LOJ #{pid}"
    description = ""

    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", title)
            # Build description from sections
            sections = c.get("contentSections", [])
            parts = []
            for section in sections:
                if section.get("type") == "Text":
                    parts.append(section.get("text", ""))
            description = "\n\n".join(parts)
            break

    if not description and contents:
        # Fallback to first available
        sections = contents[0].get("contentSections", [])
        parts = []
        for section in sections:
            if section.get("type") == "Text":
                parts.append(section.get("text", ""))
        description = "\n\n".join(parts)

    # Tags -> knowledge points
    tags = detail.get("tagsOfLocale", [])
    knowledge_points = [t.get("name", "") for t in tags if t.get("name")]

    # Judge info
    judge = detail.get("judgeInfo", {}) or {}
    time_limit = judge.get("timeLimit", 1000)  # ms
    memory_limit = judge.get("memoryLimit", 256)  # MB

    # Samples for content
    samples = detail.get("samples", [])
    content_samples = []
    for i, s in enumerate(samples):
        content_samples.append({
            "input": s.get("inputData", ""),
            "output": s.get("outputData", ""),
        })

    # Build content
    content = {
        "title": title,
        "description": description,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "source": f"LibreOJ #{pid}",
        "samples": content_samples,
    }

    # Difficulty: use multiple signals for estimation
    tag_names = [t.get("name", "") for t in tags]
    difficulty = get_loj_difficulty(
        tags=tag_names,
        pid=pid,
        title=title,
        time_limit=time_limit,
        test_case_count=len(test_cases) if test_cases else 0
    )
    # Cap at 5 for our system
    difficulty = min(5, max(1, difficulty))

    # If test_cases is empty, fall back to samples
    if not test_cases and content_samples:
        test_cases = [
            {"input": s["input"], "output": s["output"], "name": f"sample{i+1}"}
            for i, s in enumerate(content_samples)
        ]

    exercise = Exercise(
        source="loj",
        source_id=str(pid),
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=knowledge_points,
        content=content,
        test_cases=test_cases if test_cases else None,
        is_verified=True,
    )

    return exercise


async def crawl_single_problem(
    session: aiohttp.ClientSession,
    pid: int,
    target_difficulties: Optional[List[int]] = None
) -> Optional[Exercise]:
    """Crawl a single problem with full test data.
    If target_difficulties is provided, skips downloading test data for non-matching difficulties.
    """
    print(f"Crawling problem #{pid}...")

    # Step 1: Get problem detail (lightweight - only metadata)
    detail = await get_problem_full_detail(session, pid)
    if not detail:
        print(f"  Problem #{pid} not found")
        return None

    meta = detail.get("meta", {})
    title = "Unknown"
    contents = detail.get("localizedContentsOfAllLocales", [])
    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", title)
            break
    if title == "Unknown" and contents:
        title = contents[0].get("title", title)

    # Early difficulty estimation using metadata only (no test data download yet)
    tags = detail.get("tagsOfLocale", [])
    tag_names = [t.get("name", "") for t in tags if t.get("name")]
    judge = detail.get("judgeInfo", {}) or {}
    time_limit = judge.get("timeLimit", 1000)
    test_data_files = detail.get("testData", [])

    estimated_difficulty = get_loj_difficulty(
        tags=tag_names,
        pid=pid,
        title=title,
        time_limit=time_limit,
        test_case_count=len(test_data_files)
    )
    estimated_difficulty = min(5, max(1, estimated_difficulty))

    # Skip early if difficulty doesn't match
    if target_difficulties and estimated_difficulty not in target_difficulties:
        print(f"  Skipped (difficulty {estimated_difficulty} not in {target_difficulties}): {title}")
        return None

    print(f"  Title: {title} [difficulty ~{estimated_difficulty}]")
    print(f"  Test data files: {len(test_data_files)}")

    # Step 2: Download test data files (only if difficulty matches)
    test_cases = []
    if test_data_files:
        problem_meta_id = meta.get("id", pid)
        files = await download_test_data_files(session, problem_meta_id, test_data_files)
        print(f"  Downloaded {len(files)} files")

        if files:
            test_cases = parse_test_cases_from_files(files)
            print(f"  Parsed {len(test_cases)} test case pairs")
            for tc in test_cases[:3]:
                inp_preview = tc["input"][:50].replace('\n', '\\n')
                out_preview = tc["output"][:50].replace('\n', '\\n')
                print(f"    [{tc['name']}] in={inp_preview}... out={out_preview}...")

    # Step 3: Convert to Exercise
    exercise = convert_loj_to_exercise(detail, test_cases, pid)
    return exercise


async def get_existing_loj_ids() -> set:
    """Query database for already imported LOJ problem IDs."""
    from sqlalchemy import select
    existing = set()
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Exercise.source_id).where(Exercise.source == "loj")
            )
            for row in result.scalars().all():
                try:
                    existing.add(int(row))
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        print(f"  Warning: could not query existing IDs: {e}")
    return existing


async def crawl_until_count(
    target_count: int,
    start_id: int,
    import_to_db: bool = False,
    target_difficulties: Optional[List[int]] = None,
    concurrency: int = 5,
) -> List[Exercise]:
    """
    Crawl problems starting from start_id until we have target_count valid exercises.

    Strategy: Use concurrent workers to speed up crawling.
    Skips already imported problems to avoid redundant network requests.
    """
    exercises = []
    current_id = start_id
    max_id = start_id + 5000  # Safety limit
    lock = asyncio.Lock()

    # Pre-fetch existing LOJ IDs to avoid re-crawling
    existing_ids = await get_existing_loj_ids()
    if existing_ids:
        print(f"  Found {len(existing_ids)} existing LOJ problems in DB, will skip them.")
        # Fast-forward start if needed
        while current_id in existing_ids and current_id < max_id:
            current_id += 1

    connector = aiohttp.TCPConnector(family=socket.AF_INET, limit=concurrency)

    async def worker(session: aiohttp.ClientSession, worker_id: int):
        nonlocal current_id
        while True:
            async with lock:
                if len(exercises) >= target_count or current_id > max_id:
                    return
                # Skip already imported IDs
                while current_id in existing_ids and current_id <= max_id:
                    current_id += 1
                if current_id > max_id:
                    return
                pid = current_id
                current_id += 1

            try:
                exercise = await crawl_single_problem(session, pid, target_difficulties)
                if not exercise:
                    continue
                # Skip if test_cases is empty
                if not exercise.test_cases or len(exercise.test_cases) == 0:
                    continue

                async with lock:
                    if len(exercises) < target_count:
                        exercises.append(exercise)
                        print(f"  [OK #{len(exercises)}] LOJ #{pid}: {exercise.content.get('title', 'Unknown')} "
                              f"[difficulty={exercise.difficulty}, test_cases={len(exercise.test_cases or [])}]")
            except Exception:
                pass  # Silently skip errors for speed

    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [worker(session, i) for i in range(concurrency)]
        await asyncio.gather(*workers)

    if import_to_db and exercises:
        await import_exercises(exercises)

    return exercises


async def crawl_problems(
    pids: List[int],
    import_to_db: bool = False,
    target_difficulties: Optional[List[int]] = None,
) -> List[Exercise]:
    """Crawl multiple problems and optionally filter by difficulty.
    Skips already imported problems to avoid redundant network requests.
    """
    exercises = []

    # Pre-fetch existing LOJ IDs
    existing_ids = await get_existing_loj_ids()
    skipped_existing = 0

    # Filter out already imported IDs
    new_pids = []
    for pid in pids:
        if pid in existing_ids:
            skipped_existing += 1
        else:
            new_pids.append(pid)

    if skipped_existing:
        print(f"  Skipped {skipped_existing} already imported problems.")
    if not new_pids:
        print("  All specified problems already exist in DB.")
        return exercises

    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    async with aiohttp.ClientSession(connector=connector) as session:
        for pid in new_pids:
            try:
                exercise = await crawl_single_problem(session, pid, target_difficulties)
                if not exercise:
                    continue

                # Skip if test_cases is empty or only has samples (no real test data)
                if not exercise.test_cases or len(exercise.test_cases) == 0:
                    print("  Skipped (no test cases)")
                    continue

                exercises.append(exercise)
                print(f"  [OK] Imported: {exercise.content.get('title', 'Unknown')} "
                      f"[difficulty={exercise.difficulty}, test_cases={len(exercise.test_cases or [])}]")

                # Rate limiting
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  Error crawling problem {pid}: {e}")
                continue

    if import_to_db and exercises:
        await import_exercises(exercises)

    return exercises


async def import_exercises(exercises: List[Exercise]) -> Dict[str, int]:
    """Import exercises to database, skipping duplicates."""
    stats = {"total": len(exercises), "imported": 0, "skipped": 0, "errors": 0}

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        for exercise in exercises:
            try:
                # Check for duplicate by source_id
                result = await session.execute(
                    select(Exercise).where(Exercise.source_id == exercise.source_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  Skipping duplicate: LOJ #{exercise.source_id}")
                    stats["skipped"] += 1
                    continue

                session.add(exercise)
                stats["imported"] += 1
            except Exception as e:
                print(f"  Error importing LOJ #{exercise.source_id}: {e}")
                stats["errors"] += 1

        await session.commit()

    return stats


async def delete_garbage_exercises() -> Dict[str, int]:
    """Delete exercises with insufficient test cases."""
    from sqlalchemy import select, delete
    from app.database import AsyncSessionLocal

    stats = {"deleted": 0, "kept": 0}

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Exercise))
        exercises = result.scalars().all()

        to_delete = []
        for ex in exercises:
            # Check if test_cases is insufficient
            has_good_tests = False
            if ex.test_cases and len(ex.test_cases) > 0:
                # Check if test_cases are real (not just samples)
                # Real test data has multiple cases or meaningful content
                if len(ex.test_cases) >= 2:
                    has_good_tests = True
                elif len(ex.test_cases) == 1:
                    # Single test case might be just a sample - check if it's substantial
                    tc = ex.test_cases[0]
                    inp = tc.get("input", "")
                    out = tc.get("output", "")
                    if len(inp) > 20 or len(out) > 20 or '\n' in inp:
                        has_good_tests = True

            if not has_good_tests:
                to_delete.append(ex.id)

        print(f"Found {len(to_delete)} exercises with insufficient test cases to delete")
        print(f"Keeping {len(exercises) - len(to_delete)} exercises")

        if to_delete:
            for ex_id in to_delete:
                await session.execute(
                    delete(Exercise).where(Exercise.id == ex_id)
                )
            await session.commit()
            stats["deleted"] = len(to_delete)

        stats["kept"] = len(exercises) - len(to_delete)

    return stats


async def main():
    parser = argparse.ArgumentParser(description="Crawl problems from LibreOJ with full test data")
    parser.add_argument("--problem", "-p", type=int, help="Single problem ID")
    parser.add_argument("--problems", type=int, nargs="+", help="Multiple problem IDs")
    parser.add_argument("--range", type=int, nargs=2, help="Range: start end")
    parser.add_argument("--difficulty", "-d", type=int, nargs="+", help="Target difficulty levels (1-5)")
    parser.add_argument("--count", "-c", type=int, default=400, help="Target count of valid problems to crawl")
    parser.add_argument("--start", "-s", type=int, default=1, help="Starting problem ID (default: 1)")
    parser.add_argument("--concurrency", "-n", type=int, default=10, help="Number of concurrent workers (default: 10)")
    parser.add_argument("--import", dest="import_to_db", action="store_true", help="Import to DB")
    parser.add_argument("--delete-garbage", action="store_true", help="Delete exercises with bad test data")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")

    args = parser.parse_args()

    # Delete garbage first if requested
    if args.delete_garbage:
        print("Deleting garbage exercises...")
        stats = await delete_garbage_exercises()
        print(f"Deleted: {stats['deleted']}, Kept: {stats['kept']}")
        if not any([args.problem, args.problems, args.range]):
            return

    # Determine problem IDs
    pids = []
    if args.problem:
        pids.append(args.problem)
    if args.problems:
        pids.extend(args.problems)
    if args.range:
        pids.extend(range(args.range[0], args.range[1] + 1))

    target_diffs = args.difficulty

    if pids:
        # Legacy mode: crawl specific problem IDs
        pids = pids[:args.count]
        print(f"Will crawl up to {len(pids)} problems from LibreOJ")
        if target_diffs:
            print(f"Target difficulties: {target_diffs}")
        print("=" * 60)
        exercises = await crawl_problems(pids, args.import_to_db, target_diffs)
    else:
        # New mode: crawl until we have target_count valid problems
        print(f"Will crawl problems starting from #{args.start} until {args.count} valid problems found")
        print(f"Concurrency: {args.concurrency} workers")
        if target_diffs:
            print(f"Target difficulties: {target_diffs}")
        print("=" * 60)
        exercises = await crawl_until_count(args.count, args.start, args.import_to_db, target_diffs, args.concurrency)

    print("\n" + "=" * 60)
    print(f"Crawled {len(exercises)} valid exercises")

    # Difficulty distribution
    dist = {}
    for ex in exercises:
        d = ex.difficulty
        dist[d] = dist.get(d, 0) + 1
    print("Difficulty distribution:")
    for d in sorted(dist.keys()):
        print(f"  Difficulty {d}: {dist[d]} exercises")

    if args.output:
        data = []
        for ex in exercises:
            data.append({
                "source_id": ex.source_id,
                "title": ex.content.get("title", ""),
                "difficulty": ex.difficulty,
                "test_cases_count": len(ex.test_cases) if ex.test_cases else 0,
            })
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved summary to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
