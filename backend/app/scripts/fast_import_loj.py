"""
Fast LOJ Problem Importer - Without Test Data Download

For fast batch import, this version skips test data download.
Test data can be downloaded later for specific problems.

Usage:
    # Fast import 100 problems (metadata only)
    python -m app.scripts.fast_import_loj --start 100 --count 100

    # Import with embedding generation
    python -m app.scripts.fast_import_loj --start 100 --count 100 --embed
"""

import asyncio
import json
import argparse
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

LOJ_API_URL = "https://api.loj.ac"
REQUEST_DELAY = 0.1  # Reduced delay


async def api_request(session: aiohttp.ClientSession, endpoint: str, data: Dict) -> Dict:
    """Make API request"""
    url = f"{LOJ_API_URL}{endpoint}"
    async with session.post(url, json=data, headers={"Content-Type": "application/json"},
                            timeout=aiohttp.ClientTimeout(total=10)) as resp:
        return await resp.json()


async def get_problem(session: aiohttp.ClientSession, pid: int) -> Optional[Dict]:
    """Get problem info (no test data)"""
    try:
        return await api_request(session, "/api/problem/getProblem", {
            "displayId": pid,
            "localizedContentsOfAllLocales": True,
            "tagsOfLocale": "zh_CN",
            "samples": True,
            "judgeInfo": True,
            "testData": False,  # Skip test data
            "additionalFiles": False,
        })
    except Exception as e:
        return None


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding"""
    if not text.strip():
        return None
    try:
        import openai
        if settings.AI_API_KEY:
            client = openai.OpenAI(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL)
            response = client.embeddings.create(model="text-embedding-ada-002", input=text[:8000])
            return response.data[0].embedding
    except:
        pass
    return None


def build_text_for_embedding(problem: Dict) -> str:
    """Build text for embedding"""
    parts = []
    contents = problem.get("localizedContentsOfAllLocales", [])
    for c in contents:
        if c.get("locale") == "zh_CN":
            parts.append(f"题目: {c.get('title', '')}")
            break
    tags = [tag.get("name", "") for tag in problem.get("tagsOfLocale", [])]
    if tags:
        parts.append(f"标签: {', '.join(tags)}")
    for c in contents:
        if c.get("locale") == "zh_CN":
            for section in c.get("contentSections", []):
                if section.get("type") != "Sample" and section.get("text"):
                    parts.append(section["text"][:500])
            break
    return "\n".join(parts)


def convert_to_exercise(problem: Dict, embedding: Optional[List[float]] = None) -> Optional[Exercise]:
    """Convert to Exercise model"""
    if not problem.get("localizedContentsOfAllLocales"):
        return None

    meta = problem.get("meta", {})
    display_id = meta.get("displayId", 0)
    contents = problem.get("localizedContentsOfAllLocales", [])

    title = "Untitled"
    for c in contents:
        if c.get("locale") == "zh_CN":
            title = c.get("title", "Untitled")
            break

    tags = [tag.get("name", "") for tag in problem.get("tagsOfLocale", [])]
    judge = problem.get("judgeInfo", {})

    # Parse content
    description_parts = []
    samples = []
    for c in contents:
        if c.get("locale") == "zh_CN":
            for section in c.get("contentSections", []):
                if section.get("type") == "Sample":
                    sample_id = section.get("sampleId", 0)
                    sample_data = problem.get("samples", [])[sample_id] if sample_id < len(problem.get("samples", [])) else None
                    if sample_data:
                        samples.append({"input": sample_data.get("inputData", ""), "output": sample_data.get("outputData", "")})
                else:
                    if section.get("sectionTitle"):
                        description_parts.append(f"## {section['sectionTitle']}\n{section.get('text', '')}")
            break

    content = {
        "title": title,
        "description": "\n\n".join(description_parts),
        "time_limit": judge.get("timeLimit", 1000) / 1000,
        "memory_limit": judge.get("memoryLimit", 256),
        "source": f"LibreOJ #{display_id}",
        "loj_url": f"https://loj.ac/p/{display_id}",
        "samples": samples if samples else None,
    }

    # Estimate difficulty
    difficulty = 2
    accepted = meta.get("acceptedSubmissionCount", 0)
    submitted = meta.get("submissionCount", 1)
    if submitted > 0:
        rate = accepted / submitted
        if rate < 0.1: difficulty = 5
        elif rate < 0.2: difficulty = 4
        elif rate < 0.4: difficulty = 3
        elif rate < 0.6: difficulty = 2
        else: difficulty = 1

    return Exercise(
        source="loj",
        source_id=str(display_id),
        type="programming",
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,
        knowledge_points=tags,
        content=content,
        test_cases=samples if samples else None,  # Use samples as test cases
        embedding=json.dumps(embedding) if embedding else None,
        is_verified=True,
    )


async def batch_import(start_id: int, count: int, generate_embed: bool = False) -> Dict[str, int]:
    """Batch import problems"""
    stats = {"total": count, "imported": 0, "errors": 0, "with_embeddings": 0}

    async with aiohttp.ClientSession() as session:
        async with AsyncSessionLocal() as db:
            print(f"Importing problems #{start_id} to #{start_id + count - 1}...")
            print("=" * 50)

            for i, pid in enumerate(range(start_id, start_id + count)):
                print(f"[{i+1}/{count}] #{pid}...", end=" ", flush=True)

                try:
                    problem = await get_problem(session, pid)
                    if not problem or not problem.get("localizedContentsOfAllLocales"):
                        print("skip")
                        continue

                    embedding = None
                    if generate_embed:
                        text = build_text_for_embedding(problem)
                        embedding = await generate_embedding(text)
                        if embedding:
                            stats["with_embeddings"] += 1

                    exercise = convert_to_exercise(problem, embedding)
                    if exercise:
                        db.add(exercise)
                        stats["imported"] += 1
                        title = exercise.content.get("title", "")[:25]
                        print(f"OK - {title}")
                    else:
                        print("skip")

                except Exception as e:
                    print(f"err: {str(e)[:30]}")
                    stats["errors"] += 1

                await asyncio.sleep(REQUEST_DELAY)

                if (i + 1) % 50 == 0:
                    await db.commit()
                    print(f"  -> Committed {i+1}")

            await db.commit()

    return stats


async def main():
    parser = argparse.ArgumentParser(description="Fast LOJ importer")
    parser.add_argument("--start", "-s", type=int, default=100)
    parser.add_argument("--count", "-c", type=int, default=100)
    parser.add_argument("--embed", "-e", action="store_true")
    args = parser.parse_args()

    print(f"Fast LOJ Importer (no test data download)")
    print(f"Start: {args.start}, Count: {args.count}, Embeddings: {args.embed}")
    print()

    stats = await batch_import(args.start, args.count, args.embed)

    print("\n" + "=" * 50)
    print(f"Imported: {stats['imported']}/{stats['total']}")
    print(f"Errors: {stats['errors']}")
    print(f"With embeddings: {stats['with_embeddings']}")


if __name__ == "__main__":
    asyncio.run(main())
