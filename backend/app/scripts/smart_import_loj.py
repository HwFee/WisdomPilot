"""
Smart LOJ Problem Importer

Efficiently imports LOJ problems by scanning valid ID ranges.

Usage:
    python -m app.scripts.smart_import_loj --count 500
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

# LOJ 有效题目范围 (通过扫描确定的)
VALID_RANGES = [
    (1, 20),          # 基础题 (稀疏)
    (100, 200),       # 模板题 (连续)
    (500, 580),       # 比赛题 (连续)
    (2000, 2100),     # 扩展题
    (6000, 6100),     # 更多题目
    (10000, 10200),   # 最新题目
]


async def api_request(session: aiohttp.ClientSession, endpoint: str, data: Dict) -> Dict:
    url = f"{LOJ_API_URL}{endpoint}"
    async with session.post(url, json=data, headers={"Content-Type": "application/json"},
                            timeout=aiohttp.ClientTimeout(total=10)) as resp:
        return await resp.json()


async def get_problem(session: aiohttp.ClientSession, pid: int) -> Optional[Dict]:
    try:
        return await api_request(session, "/api/problem/getProblem", {
            "displayId": pid,
            "localizedContentsOfAllLocales": True,
            "tagsOfLocale": "zh_CN",
            "samples": True,
            "judgeInfo": True,
            "testData": False,
            "additionalFiles": False,
        })
    except:
        return None


async def generate_embedding(text: str) -> Optional[List[float]]:
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
        test_cases=samples if samples else None,
        embedding=json.dumps(embedding) if embedding else None,
        is_verified=True,
    )


async def smart_import(target_count: int, generate_embed: bool = False) -> Dict[str, int]:
    """智能导入：按有效范围扫描，跳过已存在的题目"""
    stats = {"scanned": 0, "imported": 0, "skipped": 0, "errors": 0, "with_embeddings": 0}

    async with aiohttp.ClientSession() as session:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            # 获取已导入的题目 ID
            result = await db.execute(select(Exercise.source_id).where(Exercise.source == 'loj'))
            existing_ids = set(r[0] for r in result.fetchall())
            print(f"Already imported: {len(existing_ids)} problems")
            print(f"Target: {target_count} problems")
            print("=" * 50)

            for start, end in VALID_RANGES:
                if stats["imported"] >= target_count:
                    break

                print(f"\nScanning range {start}-{end}...")

                for pid in range(start, end + 1):
                    if stats["imported"] >= target_count:
                        break

                    stats["scanned"] += 1

                    # 跳过已存在的
                    if str(pid) in existing_ids:
                        stats["skipped"] += 1
                        continue

                    try:
                        problem = await get_problem(session, pid)

                        if not problem or not problem.get("localizedContentsOfAllLocales"):
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
                            existing_ids.add(str(pid))
                            stats["imported"] += 1

                            title = exercise.content.get("title", "")[:25]
                            print(f"  #{pid}: {title}")

                    except Exception as e:
                        stats["errors"] += 1

                    # 每 50 个提交一次
                    if stats["scanned"] % 50 == 0:
                        await db.commit()

            await db.commit()

    return stats


async def main():
    parser = argparse.ArgumentParser(description="Smart LOJ importer")
    parser.add_argument("--count", "-c", type=int, default=300, help="Target number of problems")
    parser.add_argument("--embed", "-e", action="store_true", help="Generate embeddings")
    args = parser.parse_args()

    print(f"Smart LOJ Importer")
    print(f"Target: {args.count} problems")
    print(f"Embeddings: {args.embed}")
    print()

    stats = await smart_import(args.count, args.embed)

    print("\n" + "=" * 50)
    print(f"Scanned: {stats['scanned']}")
    print(f"Imported: {stats['imported']}")
    print(f"Skipped (existing): {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"With embeddings: {stats['with_embeddings']}")


if __name__ == "__main__":
    asyncio.run(main())
