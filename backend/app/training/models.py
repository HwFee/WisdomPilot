# ──────────────────────────────────────────────────────────────────
# 训舱数据模型模块（models.py）
# ──────────────────────────────────────────────────────────────────
# 本文件定义了训练舱领域的全部 SQLAlchemy ORM 模型（数据库表映射）。
#
# 命名规范：所有表名统一使用 deck_ 前缀，与已删除的旧系统（course_/challenge_
# 等）完全隔离，避免迁移冲突。
#
# 契约来源：前端 TypeScript 类型定义在 frontend/lib/api/deck/types.ts，
#           接口规格在 docs/backend-api/01-target-design.md。
#           修改字段时必须同步更新前端契约。
#
# 表结构概览（按业务域分组）：
#   知识点 & 掌握度：
#     - deck_knowledge_points   知识点定义（种子内置，三轴分组）
#     - deck_user_mastery       用户掌握度缓存（读模型，非事实源）
#     - deck_mastery_events     掌握度事件流（事实源，事件溯源）
#   能力 & 活动：
#     - deck_ability_axes       三轴经验值（review/debug/implement）
#     - deck_daily_activity     每日活动统计（节奏柱图/连续天数）
#     - deck_feed_events        动态流事件
#   代码审查室（Review Gym）：
#     - deck_review_sessions    审查关卡（种子内容）
#     - deck_injected_defects   注入缺陷（服务端秘密，绝不下发前端）
#     - deck_review_attempts    用户审查提交记录
#   调试竞技场（Arena）：
#     - deck_arena_challenges   竞技场挑战（种子内容）
#     - deck_arena_attempts     用户挑战提交记录
#     - deck_arena_ratings      用户 ELO 评分
#   智核经济：
#     - deck_core_transactions  智核流水账（唯一变动途径）
#   认证（Certification）：
#     - deck_cert_exams         考试定义（含定级测试）
#     - deck_cert_questions     考试题目（答案不下发）
#     - deck_certifications     用户已获认证凭证
#   徽章：
#     - deck_user_badges        已解锁徽章记录（事实表）
# ──────────────────────────────────────────────────────────────────

"""训练舱数据模型（全新表，与旧系统无关）。

表名统一 deck_ 前缀，避免与 legacy 表冲突。
schema 契约：frontend/lib/api/deck/types.ts（docs/backend-api/01-target-design.md）。
"""

# uuid 标准库：用于生成各表的主键（UUID v4 字符串）
import uuid
# datetime / date：时间类型，用于 created_at、day 等字段
from datetime import date, datetime

# SQLAlchemy 2.0 的列类型导入
from sqlalchemy import (
    Boolean,       # 布尔类型：如 correct（是否答对）
    Date,          # 日期类型：如 deck_daily_activity.day
    DateTime,      # 日期时间类型：如 created_at
    Float,         # 浮点类型：如 p_l（回忆概率，0~1）
    ForeignKey,    # 外键：建立表间关联
    Index,         # 复合索引：性能审计修复，加速 (user_id, created_at) 类查询
    Integer,       # 整数类型：如 xp、score
    JSON,          # JSON 类型：存储复杂结构（如 marks、payload、key_points）
    String,        # 字符串类型：如 name、title
    Text,          # 长文本类型：如 code、prompt
    UniqueConstraint,  # 唯一约束：如徽章的 user_id+badge_id 组合唯一
)
# SQLAlchemy 2.0 的类型安全映射工具
from sqlalchemy.orm import Mapped, mapped_column
# text 用于 partial unique index 的 WHERE 子句（SQLite 支持部分索引）
from sqlalchemy import text

# Base 是所有 ORM 模型的声明基类，定义在 app/database.py
from app.database import Base
# utc_now 返回当前 UTC 时间，作为时间字段的默认值工厂
from app.utils.time import utc_now


def _uuid() -> str:
    """生成 UUID v4 字符串，作为各表主键的默认值。

    Returns:
        str: 形如 "550e8400-e29b-41d4-a716-446655440000" 的 UUID 字符串。
    """
    return str(uuid.uuid4())


class DeckKnowledgePoint(Base):
    """知识点（种子内置，按三轴分组）"""

    __tablename__ = "deck_knowledge_points"

    # 知识点 ID：UUID 字符串主键，插入时自动生成
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 知识点名称：全局唯一，如"边界条件处理"、"动态规划状态设计"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # 分类标签：如"数据结构 · 排序"、"算法 · DP"，用于前端分组展示
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # 能力轴：三选一 -- review（代码审查）/ debug（调试排错）/ implement（编码实现）
    axis: Mapped[str] = mapped_column(String(20), nullable=False)  # review/debug/implement
    # 费曼检验评分要点：[{"keys": [同义词...], "label": 要点名}]，种子内置
    # 在苏格拉底导师的"考考我"模式中，用户讲述知识点时，
    # 系统会检查文本是否命中这些要点的同义词来评分
    key_points: Mapped[list | None] = mapped_column(JSON, nullable=True)


class DeckUserMastery(Base):
    """用户知识点掌握度缓存。p_l=HLR 回忆概率、level=掌握等级，事件表才是事实源。
    存在任意行即视为已定级（has_placement）"""

    __tablename__ = "deck_user_mastery"

    # 联合主键：(user_id, kp_id) 唯一确定一个用户对一个知识点的掌握度
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    kp_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deck_knowledge_points.id"), primary_key=True
    )
    # 回忆概率 p_l：0~1 的浮点数，由 HLR 模型重放事件计算得出
    # 表示"此刻用户还能回忆起这个知识点的概率"，默认 0.5（五五开）
    p_l: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    # 掌握等级：四级状态机 -- 初识 / 熟悉 / 熟练 / 精通
    # 由 p_l + 答对次数 + 间隔重复 + 实战来源共同判定，不能仅看 p_l
    level: Mapped[str] = mapped_column(String(10), default="初识", nullable=False)
    # 最后更新时间：每次重算掌握度时刷新
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DeckMasteryEvent(Base):
    """掌握度事件流（事实源）：每次答题/检验一条，p_l 与 level 由它重放推导"""

    __tablename__ = "deck_mastery_events"
    # 性能审计修复：HLR 重放与趋势计算高频按 (user_id, kp_id) + created_at 排序查询，
    # 复合索引替代原来的单列 user_id / kp_id 索引，避免每用户每知识点的全表临时排序。
    __table_args__ = (
        Index("ix_deck_mastery_events_user_kp_created", "user_id", "kp_id", "created_at"),
        Index("ix_deck_mastery_events_user_created", "user_id", "created_at"),
    )

    # 事件 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引加速查询（按用户查询事件流是高频操作）
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 知识点 ID：外键关联知识点表，建索引加速查询
    kp_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deck_knowledge_points.id"), index=True
    )
    # 事件创建时间：由 utc_now 自动填充，是 HLR 模型计算时间衰减的关键输入
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    # 事件来源：标识这次答题发生在哪个模块
    # review_gym=代码审查室 / arena=调试竞技场 / feynman=费曼检验 /
    # certification=认证考试 / placement=定级测试
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # review_gym/arena/feynman/certification/placement
    # 是否答对：HLR 模型的核心输入，答对则半衰期增长，答错则缩短
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # 费曼评级：仅在 source=feynman 时有值（优秀/良好/待加强）
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)  # 费曼评级
    # 使用提示次数：影响智核奖励，提示越多奖励越少
    hints_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 响应延迟（毫秒）：可用于未来分析用户思考时长，当前未强制要求
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DeckAbilityAxis(Base):
    """三轴经验。等级 = 1 + xp//400，xp_next = level*400"""

    __tablename__ = "deck_ability_axes"

    # 联合主键：(user_id, axis) 唯一确定一个用户在一个能力轴上的经验
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    # 能力轴名：review / debug / implement，与知识点的 axis 字段对应
    axis: Mapped[str] = mapped_column(String(20), primary_key=True)
    # 经验值：每次答题根据正确率和难度增加
    # 等级公式：level = 1 + xp // 400（每 400 XP 升一级）
    # 下一级所需 XP：xp_next = level * 400
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DeckReviewSession(Base):
    """代码审查室关卡（种子内容）"""

    __tablename__ = "deck_review_sessions"

    # 关卡 ID：业务可读的短 ID（非 UUID），如 REVIEW-0247
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # REVIEW-0247
    # 关卡标题：如"快速排序实现"、"链表反转"
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    # 编程语言：如 python / c，影响前端代码高亮
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    # 待审查的代码：AI 生成的"看似正确但有缺陷"的代码
    code: Mapped[str] = mapped_column(Text, nullable=False)
    # 注入缺陷数量：告诉用户"这段代码里有 N 个 bug"（不告诉具体位置）
    defect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # 难度等级：1~5，影响预估时间和智核奖励
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    # 预估完成时间（分钟）：前端展示，帮助用户规划
    eta_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # 关联弱点知识点名称：完成关卡后可关联提升对应知识点的掌握度
    related_weakness: Mapped[str | None] = mapped_column(String(100), nullable=True)


class DeckInjectedDefect(Base):
    """注入缺陷（服务端秘密，绝不下发）"""

    __tablename__ = "deck_injected_defects"

    # 缺陷 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 所属审查关卡：外键关联 deck_review_sessions，建索引加速
    session_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("deck_review_sessions.id"), nullable=False, index=True
    )
    # 缺陷所在行号：用户提交标记后，按行号匹配判断是否命中
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    # 缺陷类型：boundary（边界）/ logic（逻辑）/ performance（性能）等
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 缺陷解释：用户提交后下发，解释为什么这行有问题
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class DeckReviewAttempt(Base):
    """审查提交记录（幂等键 user_id+session_id 由 service 层保证）"""

    __tablename__ = "deck_review_attempts"

    # 提交记录 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 关卡 ID：外键关联 deck_review_sessions
    session_id: Mapped[str] = mapped_column(String(20), ForeignKey("deck_review_sessions.id"))
    # 用户标记的缺陷位置：JSON 数组，如 [{"line": 6, "type": "boundary"}, ...]
    marks: Mapped[list] = mapped_column(JSON, nullable=False)
    # 判定结果：JSON 对象，包含命中/遗漏/误报等详情，由 service 层计算
    verdict: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 提交时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # 性能审计修复："最近 N 次提交"查询按 user_id + created_at 排序，
    # 复合索引避免全历史临时排序。
    __table_args__ = (Index("ix_deck_review_attempts_user_created", "user_id", "created_at"),)


class DeckArenaChallenge(Base):
    """调试竞技场挑战（种子内容，按日轮换）"""

    __tablename__ = "deck_arena_challenges"

    # 挑战 ID：业务可读的短 ID，如 DEBUG-0091
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # DEBUG-0091
    # 挑战标题：如"中位数统计 · 测试全挂"
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    # 编程语言：如 python，影响前端代码高亮
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    # 有 bug 的代码：用户需要找到并修复其中的缺陷
    code: Mapped[str] = mapped_column(Text, nullable=False)
    # 失败输出：测试运行的真实输出，展示给用户作为调试线索
    failing_output: Mapped[str] = mapped_column(Text, nullable=False)
    # 测试用例列表（Judge0 判题用）：[{"input": str, "expected_output": str}, ...]
    # 服务端秘密，绝不下发前端；为空时判题降级为关键字匹配
    test_cases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 时间限制（秒）：竞技场限时挑战，超时判定失败
    time_limit_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    # 难度等级：1~5，影响 ELO 评分变化幅度和智核奖励
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)


class DeckArenaAttempt(Base):
    """调试竞技场提交记录"""

    __tablename__ = "deck_arena_attempts"

    # 提交记录 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 挑战 ID：外键关联 deck_arena_challenges
    challenge_id: Mapped[str] = mapped_column(String(20), ForeignKey("deck_arena_challenges.id"))
    # 是否解决：0=未解决 / 1=已解决（用 Integer 而非 Boolean，兼容 SQLite）
    solved: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    # 通过的测试用例数
    passed: Mapped[int] = mapped_column(Integer, default=0)
    # 总测试用例数
    total: Mapped[int] = mapped_column(Integer, default=0)
    # 提交时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # 性能审计修复：连胜/周榜/回顾查询按 user_id + created_at 过滤排序，
    # 复合索引避免全表扫描；同时支撑已攻克挑战的幂等检查。
    # 安全审计修复（TOCTOU 兜底）：partial unique index 保证同一 (用户, 挑战)
    # 至多存在一条 solved=1 记录。并发双击同时通过"是否已攻克"的 SELECT 检查时，
    # 第二个 INSERT 撞唯一约束抛 IntegrityError，由端点捕获后按已攻克处理，
    # 从数据库层杜绝重复发奖。
    __table_args__ = (
        Index("ix_deck_arena_attempts_user_created", "user_id", "created_at"),
        Index(
            "uq_deck_arena_attempts_solved_once",
            "user_id",
            "challenge_id",
            unique=True,
            sqlite_where=text("solved = 1"),
        ),
    )


class DeckArenaRating(Base):
    """调试竞技场 ELO 评分（每用户一行）"""

    __tablename__ = "deck_arena_ratings"
    # 性能审计修复：排行榜 ORDER BY rating DESC 与周榜 COUNT(rating > x)
    # 每次请求全表扫描，加 rating 索引使其走索引扫描。
    __table_args__ = (Index("ix_deck_arena_ratings_rating", "rating"),)

    # 用户 ID：主键，每用户仅一行评分记录
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    # ELO 评分：初始 1200（标准国际象棋起始分），根据胜负浮动
    rating: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    # 连胜次数：用于连胜奖励和前端展示，失败时归零
    win_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 最后更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DeckCoreTransaction(Base):
    """智核一本账（唯一变动途径）"""

    __tablename__ = "deck_core_transactions"

    # 流水 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 变动数额：正数=获得智核 / 负数=消耗智核
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    # 变动原因：如"审查关卡通过"、"费曼检验优秀"等，供流水展示
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    # 变动后余额：冗余字段，方便审计时直接查看任意时刻余额
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    # 流水时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # 性能审计修复：流水展示按 user_id + created_at 倒序查询，复合索引避免临时排序。
    __table_args__ = (Index("ix_deck_core_transactions_user_created", "user_id", "created_at"),)


class DeckCertExam(Base):
    """认证考试（种子内容；id=placement 为定级测试）"""

    __tablename__ = "deck_cert_exams"

    # 考试 ID：业务可读短 ID
    # cert-pointer = 指针认证考试 / placement = 入门定级测试（新用户首次评估）
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # cert-pointer / placement
    # 考试主题：如"指针"、"定级测试"
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    # 时间限制（分钟）：超时自动交卷
    time_limit_min: Mapped[int] = mapped_column(Integer, nullable=False)
    # 及格分数：达到此分数视为通过，placement 为 0（定级测试不设及格线）
    pass_score: Mapped[int] = mapped_column(Integer, nullable=False)


class DeckCertQuestion(Base):
    """认证题目（答案不下发）"""

    __tablename__ = "deck_cert_questions"

    # 题目 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 所属考试 ID：外键关联 deck_cert_exams，建索引加速按考试查询
    exam_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("deck_cert_exams.id"), nullable=False, index=True
    )
    # 题目编号：前端用，如 q1/q2（认证考试）/ p1/p2（定级测试）
    qid: Mapped[str] = mapped_column(String(10), nullable=False)  # q1/p1，前端用
    # 题型：mcq=选择题 / code=编程题
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # mcq/code
    # 题干文本
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # 选项列表：仅 mcq 题型有值，如 ["5", "10", "未定义", "编译错误"]
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 起始代码：仅 code 题型有值，提供函数签名供用户补全
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 选择题正确答案：仅 mcq 题型有值，服务端比对，绝不下发前端
    answer_correct: Mapped[str | None] = mapped_column(String(500), nullable=True)  # mcq 答案
    # 编程题关键片段：仅 code 题型有值，用户提交代码包含这些片段即算正确
    answer_includes: Mapped[list | None] = mapped_column(JSON, nullable=True)  # code 关键片段
    # 编程题测试用例列表（Judge0 判题用）：[{"input": str, "expected_output": str}, ...]
    # 服务端秘密，绝不下发前端；为空时 code 题判分降级为关键片段匹配
    test_cases: Mapped[list | None] = mapped_column(JSON, nullable=True)  # code 测试用例
    # 排序序号：控制题目在前端的显示顺序
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class DeckCertification(Base):
    """能力凭证"""

    __tablename__ = "deck_certifications"

    # 凭证 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 认证主题：如"指针"，与考试的 topic 对应
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    # 认证等级：如"合格"/"优秀"，根据考试分数判定
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    # 考试分数
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    # 验证码：全局唯一，用于外部验证凭证真实性（如求职时出示）
    verify_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # 认证时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DeckDailyActivity(Base):
    """每日活动（节奏柱图 / 今日统计 / 连续天数）"""

    __tablename__ = "deck_daily_activity"

    # 联合主键：(user_id, day) 唯一确定一个用户某一天的活动汇总
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    # 日期：仅日期不含时间，用于按天聚合
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    # 当日学习时长（分钟）：前端节奏柱图展示
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    # 当日练习题数
    exercises: Mapped[int] = mapped_column(Integer, default=0)
    # 当日答对题数
    correct: Mapped[int] = mapped_column(Integer, default=0)


class DeckFeedEvent(Base):
    """动态流。payload.segments 与前端 FeedItem.segments 同构"""

    __tablename__ = "deck_feed_events"

    # 事件 ID：UUID 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 事件类型：如 review_pass / arena_solved / badge_unlocked / cert_earned 等
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # 事件载荷：JSON 对象，包含事件详情
    # 其中的 segments 字段与前端 FeedItem.segments 结构一致，用于渲染动态卡片
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 事件创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # 性能审计修复：动态流按 user_id + created_at 倒序取最近 N 条，复合索引避免临时排序。
    __table_args__ = (Index("ix_deck_feed_events_user_created", "user_id", "created_at"),)


class DeckUserBadge(Base):
    """已解锁徽章（事实表）。徽章定义不入库，见 app/training/badges.py"""

    __tablename__ = "deck_user_badges"
    # 唯一约束：同一用户同一徽章只能解锁一次，保证 evaluate_and_award 幂等
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_deck_user_badge"),
    )

    # 自增主键：徽章记录使用自增整数 ID（其他表用 UUID）
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 用户 ID：外键关联 users 表，建索引
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # 徽章 ID：字符串标识符，对应 badges.py 中定义的徽章 key，如"first_review_pass"
    badge_id: Mapped[str] = mapped_column(String(40), nullable=False)
    # 解锁时间
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
