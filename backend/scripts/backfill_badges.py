"""
回填徽章脚本：对全部用户各跑一次 evaluate_and_award（ctx=None）。

本脚本的用途：
    在徽章系统上线后，对历史已存在的用户补发他们本应获得、但因徽章功能
    尚未上线而未被记录的徽章。

回填规则说明：
    - 仅依赖历史事实的规则会补发（例如：累计提交次数达到阈值）
    - 依赖瞬时上下文的规则（如竞技场三连胜历史峰值）不回填，因为这些
      瞬时状态没有被持久化，历史数据已无法重建
    - 依赖调用时上下文（ctx）的规则，回填时传 ctx=None，引擎会自动跳过

幂等性保证：
    evaluate_and_award 是幂等的，已解锁的徽章会被跳过，不会重复发放。
    因此本脚本可以安全地重复执行多次。

用法：
    cd backend && python -m scripts.backfill_badges
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.training import badges
# noqa: F401 - 导入 deck 模型是为了将所有 SQLAlchemy 模型注册到 Base.metadata，
# 确保 evaluate_and_award 中涉及的表已被 ORM 映射
from app.training import models as deck_models  # noqa: F401 - 注册 deck 表到 Base
from app.auth.models import User


async def backfill_badges() -> None:
    """
    为所有用户回填徽章。

    执行流程:
        1. 打开一个异步数据库会话
        2. 查询所有用户 ID
        3. 逐个用户调用 evaluate_and_award 进行徽章评估与发放
        4. 统计本次回填新发放的徽章数量
        5. 提交事务并打印汇总信息

    注意:
        - 所有用户共享同一个数据库会话，最后统一 commit
        - 如果中途某个用户评估出错，整个事务会回滚
    """
    async with AsyncSessionLocal() as db:
        # 查询所有用户 ID，scalars().all() 将结果展平为纯 ID 列表
        user_ids = (await db.execute(select(User.id))).scalars().all()
        awarded_total = 0  # 累计本次回填新发放的徽章总数

        for user_id in user_ids:
            # 对每个用户执行徽章评估；ctx=None 表示无瞬时上下文（回填模式）
            unlocked = await badges.evaluate_and_award(db, user_id)
            awarded_total += len(unlocked)

            if unlocked:
                # 拼接本次新解锁的徽章 ID，用于日志展示
                names = ", ".join(b["id"] for b in unlocked)
                print(f"[backfill] {user_id}: +{len(unlocked)} ({names})")

        # 统一提交所有徽章变更
        await db.commit()
        print(f"[backfill] done: {len(user_ids)} users, {awarded_total} badges awarded")


if __name__ == "__main__":
    # asyncio.run 创建事件循环并运行异步主函数，运行完毕后自动关闭事件循环
    asyncio.run(backfill_badges())
