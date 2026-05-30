"""
清理 ai_hint_cache 表中的重复记录，保留最新的一条。
在添加唯一约束前必须先执行此脚本。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.ai_hint_cache import AIHintCache
from sqlalchemy import func


async def cleanup_duplicates():
    async with AsyncSessionLocal() as db:
        # 找出有重复的组合
        from sqlalchemy import text
        dup_query = text("""
            SELECT user_id, exercise_id, hint_level, COUNT(*) as cnt
            FROM ai_hint_cache
            GROUP BY user_id, exercise_id, hint_level
            HAVING cnt > 1
        """)
        result = await db.execute(dup_query)
        duplicates = result.all()

        if not duplicates:
            print("✅ 没有发现重复记录")
            return

        print(f"发现 {len(duplicates)} 组重复记录，开始清理...")

        for user_id, exercise_id, hint_level, count in duplicates:
            # 获取该组合的所有记录，按创建时间倒序
            stmt = select(AIHintCache).where(
                AIHintCache.user_id == user_id,
                AIHintCache.exercise_id == exercise_id,
                AIHintCache.hint_level == hint_level,
            ).order_by(AIHintCache.created_at.desc())
            result = await db.execute(stmt)
            records = result.scalars().all()

            # 保留最新的一条，删除其余的
            keep_id = records[0].id
            delete_ids = [r.id for r in records[1:]]

            await db.execute(
                delete(AIHintCache).where(AIHintCache.id.in_(delete_ids))
            )
            print(f"  保留 {keep_id}，删除 {len(delete_ids)} 条重复记录")

        await db.commit()
        print("✅ 清理完成")


if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
