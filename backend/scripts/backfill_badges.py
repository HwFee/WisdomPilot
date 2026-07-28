"""回填徽章：对全部用户各跑一次 evaluate_and_award（ctx=None）。

仅依赖历史事实的规则会补发；依赖瞬时上下文的规则（如竞技场三连胜历史峰值）
不回填。幂等，可重复执行——已解锁的徽章会跳过。

用法：cd backend && python -m scripts.backfill_badges
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.training import badges
from app.training import models as deck_models  # noqa: F401 - 注册 deck 表到 Base
from app.auth.models import User


async def backfill_badges() -> None:
    async with AsyncSessionLocal() as db:
        user_ids = (await db.execute(select(User.id))).scalars().all()
        awarded_total = 0
        for user_id in user_ids:
            unlocked = await badges.evaluate_and_award(db, user_id)
            awarded_total += len(unlocked)
            if unlocked:
                names = ", ".join(b["id"] for b in unlocked)
                print(f"[backfill] {user_id}: +{len(unlocked)} ({names})")
        await db.commit()
        print(f"[backfill] done: {len(user_ids)} users, {awarded_total} badges awarded")


if __name__ == "__main__":
    asyncio.run(backfill_badges())
