"""
Batch embed exercises - 批量生成题目标签和Embedding

执行内容：
1. 填充 z_id (Z + source_id)
2. 生成 extracted_tags (基于 knowledge_points 和 content)
3. 生成 content embedding (基于题目内容)
4. 生成 tag embedding (基于提取的标签)
"""

import asyncio
import json
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.insert(0, "C:/Users/17445/Desktop/AIcodiingT eachdemo/backend")

from app.database import AsyncSessionLocal
from app.models.exercise import Exercise
from app.services.embedding import (
    EmbeddingService,
    ExerciseEmbeddingService,
    get_embedding_service,
)
from app.services.tag_extraction import TagExtractionService, ExtractedTags

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def fill_z_ids(db: AsyncSession) -> int:
    """填充 z_id: Z + source_id"""
    result = await db.execute(
        select(Exercise).where(
            Exercise.source_id.isnot(None),
            Exercise.z_id.is_(None),
        )
    )
    exercises = result.scalars().all()
    count = 0
    for ex in exercises:
        ex.z_id = f"Z{ex.source_id}"
        count += 1
    await db.commit()
    logger.info(f"[z_id] 填充了 {count} 道题的 z_id")
    return count


def create_default_tags(ex: Exercise) -> ExtractedTags:
    """基于现有数据创建默认标签"""
    content = ex.content or {}
    text = content.get("text", "") or content.get("description", "")
    title = content.get("title", "")

    # 使用现有的 knowledge_points
    kps = ex.knowledge_points or []
    if isinstance(kps, str):
        try:
            kps = json.loads(kps)
        except Exception:
            kps = []

    # 从题目文本中提取关键词
    keywords = []
    keyword_patterns = [
        "数组", "链表", "树", "图", "排序", "搜索", "递归", "迭代",
        "动态规划", "贪心", "分治", "回溯", "双指针", "滑动窗口",
        "哈希", "栈", "队列", "堆", "二叉树", "二分查找", "字符串",
        "模拟", "枚举", "DFS", "BFS", "前缀和", "差分", "并查集",
        "拓扑排序", "最短路", "最小生成树", "线段树", "树状数组",
    ]
    full_text = f"{title} {text}"
    for kw in keyword_patterns:
        if kw in full_text:
            keywords.append(kw)

    # 算法类型推断
    algorithm_type = None
    algo_patterns = {
        "动态规划": ["动态规划", "dp", "DP", "状态转移"],
        "贪心": ["贪心", "greedy"],
        "分治": ["分治", "divide"],
        "回溯": ["回溯", "backtrack", "剪枝"],
        "搜索": ["DFS", "BFS", "搜索", "遍历"],
        "模拟": ["模拟", "simulation"],
        "枚举": ["枚举", "暴力"],
        "数学": ["数学", "数论", "质数", "公约数"],
    }
    for algo, patterns in algo_patterns.items():
        if any(p in full_text for p in patterns):
            algorithm_type = algo
            break

    # 数据结构推断
    data_structures = []
    ds_patterns = {
        "数组": ["数组", "array"],
        "链表": ["链表", "linked list"],
        "栈": ["栈", "stack"],
        "队列": ["队列", "queue"],
        "树": ["树", "tree", "二叉树"],
        "图": ["图", "graph"],
        "堆": ["堆", "heap", "优先队列"],
        "哈希表": ["哈希", "hash", "map", "字典"],
    }
    for ds, patterns in ds_patterns.items():
        if any(p in full_text for p in patterns):
            data_structures.append(ds)

    # 题目模式推断
    problem_pattern = None
    pattern_keywords = {
        "最值问题": ["最大", "最小", "最长", "最短", "最优"],
        "计数问题": ["多少", "个数", "数量", "计数", "方案数"],
        "判断问题": ["是否", "判断", "能否"],
        "构造问题": ["构造", "构造一个", "构造方案"],
        "路径问题": ["路径", "路线", "走法"],
    }
    for pattern, patterns in pattern_keywords.items():
        if any(p in full_text for p in patterns):
            problem_pattern = pattern
            break

    return ExtractedTags(
        knowledge_points=kps if kps else keywords,
        algorithm_type=algorithm_type,
        data_structures=data_structures,
        keywords=keywords,
        problem_pattern=problem_pattern,
        estimated_difficulty=ex.difficulty,
    )


async def fill_extracted_tags(db: AsyncSession) -> int:
    """填充 extracted_tags (不使用AI，基于已有数据推断)"""
    result = await db.execute(
        select(Exercise).where(Exercise.extracted_tags.is_(None))
    )
    exercises = result.scalars().all()
    count = 0
    for ex in exercises:
        tags = create_default_tags(ex)
        ex.extracted_tags = tags.to_dict()
        count += 1
    await db.commit()
    logger.info(f"[tags] 填充了 {count} 道题的 extracted_tags")
    return count


def _exercise_to_text_truncated(ex: Exercise, max_chars: int = 600) -> str:
    """将题目转换为文本并截断到安全长度"""
    parts = []
    content = ex.content or {}
    if content.get("title"):
        parts.append(content["title"])
    if content.get("text"):
        parts.append(content["text"])
    if content.get("description"):
        parts.append(content["description"])
    if ex.knowledge_points:
        kp_list = ex.knowledge_points
        if isinstance(kp_list, str):
            try:
                kp_list = json.loads(kp_list)
            except Exception:
                kp_list = []
        if kp_list:
            parts.append(f"知识点：{', '.join(kp_list)}")

    text = "\n".join(parts)
    # 截断到安全长度避免 413
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


async def generate_content_embeddings(db: AsyncSession, batch_size: int = 10) -> dict:
    """批量生成 content embedding"""
    embedding_service = get_embedding_service()

    # 获取没有 embedding 的题目
    result = await db.execute(
        select(Exercise).where(Exercise.embedding.is_(None)).limit(1000)
    )
    exercises = list(result.scalars().all())

    if not exercises:
        logger.info("[embedding] 所有题目已有 content embedding")
        return {"total": 0, "updated": 0, "failed": 0}

    total = len(exercises)
    updated = 0
    failed = 0

    logger.info(f"[embedding] 开始生成 {total} 道题的 content embedding...")

    for i in range(0, total, batch_size):
        batch = exercises[i:i + batch_size]
        logger.info(f"[embedding] 处理第 {i+1}-{min(i+batch_size, total)} 题...")

        for ex in batch:
            try:
                text = _exercise_to_text_truncated(ex)
                if not text:
                    logger.warning(f"[embedding] 题目 {ex.id} 无有效文本，跳过")
                    failed += 1
                    continue

                embedding = await embedding_service.generate_embedding(text)
                if embedding:
                    ex.embedding = json.dumps(embedding)
                    updated += 1
                else:
                    logger.warning(f"[embedding] 题目 {ex.id} embedding 生成失败")
                    failed += 1
            except Exception as e:
                logger.error(f"[embedding] 题目 {ex.id} 处理失败: {e}")
                failed += 1

        # 每批提交
        await db.commit()
        # 小延迟避免触发限流
        await asyncio.sleep(0.5)

    logger.info(f"[embedding] content embedding 完成: total={total}, updated={updated}, failed={failed}")
    return {"total": total, "updated": updated, "failed": failed}


async def generate_tag_embeddings(db: AsyncSession, batch_size: int = 10) -> dict:
    """批量生成 tag embedding"""
    embedding_service = get_embedding_service()
    exercise_emb_service = ExerciseEmbeddingService(db, embedding_service)

    # 获取有 extracted_tags 但没有 tag_embedding 的题目
    result = await db.execute(
        select(Exercise).where(
            Exercise.extracted_tags.isnot(None),
            Exercise.tag_embedding.is_(None),
        ).limit(1000)
    )
    exercises = list(result.scalars().all())

    if not exercises:
        logger.info("[tag_embedding] 所有题目已有 tag embedding")
        return {"total": 0, "updated": 0, "failed": 0}

    total = len(exercises)
    updated = 0
    failed = 0

    logger.info(f"[tag_embedding] 开始生成 {total} 道题的 tag embedding...")

    for i in range(0, total, batch_size):
        batch = exercises[i:i + batch_size]
        logger.info(f"[tag_embedding] 处理第 {i+1}-{min(i+batch_size, total)} 题...")

        for ex in batch:
            try:
                tags_dict = ex.extracted_tags or {}
                tags = ExtractedTags(
                    knowledge_points=tags_dict.get("knowledge_points", []),
                    algorithm_type=tags_dict.get("algorithm_type"),
                    data_structures=tags_dict.get("data_structures", []),
                    keywords=tags_dict.get("keywords", []),
                    problem_pattern=tags_dict.get("problem_pattern"),
                    time_complexity=tags_dict.get("time_complexity"),
                    difficulty_signals=tags_dict.get("difficulty_signals", []),
                    prerequisite_skills=tags_dict.get("prerequisite_skills", []),
                    estimated_difficulty=tags_dict.get("estimated_difficulty", 3),
                )

                embedding = await embedding_service.generate_embedding(tags.to_embedding_text())
                if embedding:
                    ex.tag_embedding = json.dumps(embedding)
                    updated += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"[tag_embedding] 题目 {ex.id} 处理失败: {e}")
                failed += 1

        await db.commit()
        await asyncio.sleep(0.5)

    logger.info(f"[tag_embedding] tag embedding 完成: total={total}, updated={updated}, failed={failed}")
    return {"total": total, "updated": updated, "failed": failed}


async def main():
    async with AsyncSessionLocal() as db:
        logger.info("=" * 60)
        logger.info("开始批量处理 Exercise 数据")
        logger.info("=" * 60)

        # 1. 填充 z_id
        z_count = await fill_z_ids(db)

        # 2. 填充 extracted_tags
        tag_count = await fill_extracted_tags(db)

        # 3. 生成 content embedding
        emb_stats = await generate_content_embeddings(db, batch_size=5)

        # 4. 生成 tag embedding
        tag_emb_stats = await generate_tag_embeddings(db, batch_size=5)

        logger.info("=" * 60)
        logger.info("批量处理完成!")
        logger.info(f"  z_id 填充: {z_count}")
        logger.info(f"  tags 填充: {tag_count}")
        logger.info(f"  content embedding: {emb_stats}")
        logger.info(f"  tag embedding: {tag_emb_stats}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
