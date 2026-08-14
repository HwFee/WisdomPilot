"""回归测试：同一知识点在同一会话内连续记多条事件不得撞 UNIQUE。

回归缺陷：record_mastery_event 新建 DeckUserMastery 缓存行后不 flush，
db.get 不命中 pending 实例——autoflush=False 的会话（如测试环境）里
同一知识点第二次记事件会盲插重复行，flush 时撞 (user_id, kp_id) UNIQUE。
认证/竞技场提交会对同一知识点连记多条事件，正是这条路径。
"""

import pytest
from sqlalchemy import select

from app.training.models import DeckKnowledgePoint, DeckUserMastery
from app.training.seed import seed_deck
from app.training import service


@pytest.mark.asyncio
async def test_repeated_events_same_kp_single_mastery_row(db_session, auth_user):
    await seed_deck(db_session)
    kp = (
        await db_session.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == "指针的内存布局")
        )
    ).scalar_one()
    for _ in range(6):
        await service.record_mastery_event(
            db_session, auth_user.id, kp.id, "certification", True
        )
    await db_session.commit()

    rows = (
        await db_session.execute(
            select(DeckUserMastery).where(DeckUserMastery.user_id == auth_user.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].kp_id == kp.id
