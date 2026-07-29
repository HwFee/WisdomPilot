"""Training cockpit domain - core business logic for the programming training platform.

Contains domain models, API routes, mastery tracking, badge evaluation,
and seed data. All training-related code lives here.
"""

# ──────────────────────────────────────────────────────────────────
# 训练舱（Deck）领域包 —— 整个平台的核心业务模块
# ──────────────────────────────────────────────────────────────────
# 本包（app/training/）承载了「AI 时代编程实战训练舱」的全部后端逻辑：
#
#   - models.py   ：数据模型（SQLAlchemy ORM），定义所有 deck_ 前缀的表
#   - mastery.py  ：掌握度纯函数引擎，基于 HLR 记忆模型 + 四级状态机
#   - badges.py   ：徽章定义 + 幂等判定引擎（定义在代码中，不入库）
#   - seed.py     ：种子数据（知识点、审查关卡、竞技场挑战、认证题目）
#   - service.py  ：业务服务层，编排模型、掌握度、徽章、智核经济
#   - router.py   ：FastAPI 路由，暴露 /api 前缀下的训练舱接口
#
# 设计原则：
#   1. 事件溯源 —— DeckMasteryEvent 是事实表，DeckUserMastery 只是缓存读模型
#   2. 纯函数 —— mastery.py / badges.py 不碰数据库，方便测试和推理
#   3. 单一账本 —— 智核（DeckCoreTransaction）是唯一变动途径
# ──────────────────────────────────────────────────────────────────
