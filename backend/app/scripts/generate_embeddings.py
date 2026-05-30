"""
Generate embeddings for LOJ problems using SiliconFlow

Usage:
    python -m app.scripts.generate_embeddings --batch 100
"""

import asyncio
import json
import os
import argparse
from pathlib import Path
from typing import Optional, List
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise
from sqlalchemy import select, or_

# 硅基流动 API 配置
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = 'https://api.siliconflow.cn/v1'
EMBEDDING_MODEL = 'BAAI/bge-large-zh-v1.5'  # 中文嵌入模型，1024维


def generate_embedding_sync(text: str) -> Optional[List[float]]:
    """Generate embedding using SiliconFlow API"""
    if not text.strip():
        return None
    try:
        response = requests.post(
            f'{SILICONFLOW_BASE_URL}/embeddings',
            headers={
                'Authorization': f'Bearer {SILICONFLOW_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': EMBEDDING_MODEL,
                'input': text[:8000]
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['data'][0]['embedding']
        else:
            print(f"  API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")
        return None


def build_text_for_embedding(exercise: Exercise) -> str:
    """Build text content for embedding (limit to avoid API limits)"""
    parts = []

    # Title
    title = exercise.content.get("title", "")
    if title:
        parts.append(f"题目: {title}")

    # Tags
    if exercise.knowledge_points:
        parts.append(f"标签: {', '.join(exercise.knowledge_points)}")

    # Description - limit to 500 chars to avoid 413 error
    description = exercise.content.get("description", "")
    if description:
        parts.append(description[:500])

    return "\n".join(parts)


async def generate_all_embeddings(batch_size: int = 50):
    """Generate embeddings for all LOJ problems"""
    async with AsyncSessionLocal() as session:
        # Get exercises without embeddings
        result = await session.execute(
            select(Exercise)
            .where(Exercise.source == 'loj')
            .where(or_(Exercise.embedding.is_(None), Exercise.embedding == ''))
            .order_by(Exercise.id)
        )
        exercises = result.scalars().all()

        total = len(exercises)
        if total == 0:
            print("All exercises already have embeddings!")
            return

        print(f"Generating embeddings for {total} exercises...")
        print(f"Using model: {EMBEDDING_MODEL}")
        print("=" * 50)

        updated = 0
        errors = 0

        for i, exercise in enumerate(exercises):
            title = exercise.content.get('title', '')[:25]
            # Remove non-ascii chars for Windows console
            title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"[{i+1}/{total}] #{exercise.source_id}: {title}...", end=" ", flush=True)

            text = build_text_for_embedding(exercise)
            embedding = generate_embedding_sync(text)

            if embedding:
                exercise.embedding = json.dumps(embedding)
                updated += 1
                print(f"OK (dim={len(embedding)})")
            else:
                errors += 1
                print("FAILED")

            # Commit in batches
            if (i + 1) % batch_size == 0:
                await session.commit()
                print(f"  -> Committed {i+1}")

        await session.commit()

        print("\n" + "=" * 50)
        print(f"Total: {total}")
        print(f"Updated: {updated}")
        print(f"Errors: {errors}")


async def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for LOJ problems")
    parser.add_argument("--batch", "-b", type=int, default=50, help="Batch size for commits")
    args = parser.parse_args()

    await generate_all_embeddings(args.batch)


if __name__ == "__main__":
    asyncio.run(main())
