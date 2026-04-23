"""
Test Sandbox Router - 沙箱测试专用接口

所有沙箱接口的请求头需要带 X-Test-Mode: true
沙箱模式下的数据：
- 不计入今日做题数
- 不影响正确率
- 不改变段位/星星
- 不解锁章节进度
- 但会真实消耗/获得智核
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.deps import get_current_user, get_db
from app.models.user import User
import logging

router = APIRouter(prefix="/api/test", tags=["test-sandbox"])


# 测试专用的虚拟题目
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "什么是变量？",
        "options": ["存储数据的容器", "一种函数", "一个类", "一种循环"],
        "correct_answer": "A",
        "difficulty": 1,
        "knowledge_point": "变量基础"
    },
    {
        "id": 2,
        "question": "int a = 5; 中 int 是什么？",
        "options": ["变量名", "数据类型", "函数", "运算符"],
        "correct_answer": "B",
        "difficulty": 1,
        "knowledge_point": "数据类型"
    },
    {
        "id": 3,
        "question": "for循环的执行顺序是？",
        "options": ["初始化-条件-循环体-迭代", "条件-初始化-循环体", "循环体-条件-迭代", "迭代-条件-初始化"],
        "correct_answer": "A",
        "difficulty": 2,
        "knowledge_point": "循环结构"
    },
]


@router.get("/mastery/questions")
async def get_test_mastery_questions(
    current_user: User = Depends(get_current_user),
):
    """[沙箱] 获取精进之路测试题目"""
    return {
        "questions": TEST_QUESTIONS,
        "total": len(TEST_QUESTIONS),
        "test_mode": True,
        "message": "沙箱模式：答题不影响真实统计"
    }


@router.post("/mastery/submit")
async def submit_test_mastery_answers(
    answers: list[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 提交精进之路测试答案

    只计算智核奖励，不影响：
    - 今日做题数
    - 正确率
    - 章节进度
    """
    from app.services.core_service import CoreService

    correct_count = 0
    total = len(answers)

    for answer in answers:
        question_id = answer.get("question_id")
        user_answer = answer.get("user_answer")

        # 查找对应题目
        for q in TEST_QUESTIONS:
            if q["id"] == question_id:
                if q["correct_answer"] == user_answer:
                    correct_count += 1
                break

    # 计算智核奖励（每题正确+2）
    cores_earned = correct_count * 2

    # 发放智核
    if cores_earned > 0:
        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=current_user.id,
            amount=cores_earned,
            category="mastery",
            reference_type="test_sandbox",
            reference_id="test_mastery",
            description=f"[沙箱测试] 精进之路答题正确{correct_count}题"
        )
        await db.refresh(current_user)

    return {
        "success": True,
        "total": total,
        "correct_count": correct_count,
        "wrong_count": total - correct_count,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": "沙箱模式：不影响真实统计"
    }


@router.get("/arena/exercises")
async def get_test_arena_exercises(
    current_user: User = Depends(get_current_user),
):
    """[沙箱] 获取挑战之路测试题目"""
    return {
        "exercises": [
            {
                "id": 101,
                "title": "测试题目1：基础运算",
                "difficulty": 2,
                "test_mode": True
            },
            {
                "id": 102,
                "title": "测试题目2：条件判断",
                "difficulty": 3,
                "test_mode": True
            }
        ],
        "test_mode": True,
        "message": "沙箱模式：答题不影响真实统计"
    }


@router.post("/arena/submit")
async def submit_test_arena_exercise(
    exercise_id: int,
    passed: bool,  # 简化：直接传是否通过
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 提交挑战之路测试答案

    只计算智核奖励，不影响：
    - 今日做题数
    - 正确率
    - 段位/星星
    """
    from app.services.core_service import CoreService

    cores_earned = 0

    if passed:
        cores_earned = 3  # 挑战之路正确+3

        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=current_user.id,
            amount=cores_earned,
            category="arena",
            reference_type="test_sandbox",
            reference_id="test_arena",
            description="[沙箱测试] 挑战之路答题正确"
        )
        await db.refresh(current_user)

    return {
        "success": True,
        "exercise_id": exercise_id,
        "passed": passed,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": "沙箱模式：不影响真实统计"
    }


@router.post("/checkin")
async def test_checkin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试签到

    不影响真实签到状态，只获得智核
    """
    from app.services.core_service import CoreService

    cores_earned = 5  # 沙箱签到固定+5

    core_service = CoreService(db)
    await core_service.earn_cores(
        user_id=current_user.id,
        amount=cores_earned,
        category="checkin",
        reference_type="test_sandbox",
        reference_id="test_checkin",
        description="[沙箱测试] 模拟签到奖励"
    )
    await db.refresh(current_user)

    return {
        "success": True,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": "沙箱模式：不影响真实签到状态"
    }


@router.post("/ai-hint/{level}")
async def test_ai_hint(
    level: str,  # light, medium, deep
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试AI提示消耗

    消耗智核，返回模拟的提示内容
    """
    from app.services.core_service import CoreService

    costs = {"light": 1, "medium": 3, "deep": 5}
    hints = {
        "light": "💡 提示：这道题考察的是基础概念，可以先回顾一下变量的定义。",
        "medium": "💡 提示：1. 先分析题目要求 2. 确定数据类型 3. 选择合适的变量名",
        "deep": "💡 完整解析：这道题需要定义一个整型变量，使用int关键字。步骤：1. 写数据类型int 2. 写变量名 3. 用=赋值 4. 加分号结束。示例：int age = 25;"
    }

    if level not in costs:
        return {"success": False, "error": "无效的提示级别"}

    cost = costs[level]

    if current_user.cores < cost:
        return {"success": False, "error": "智核不足", "balance": current_user.cores}

    core_service = CoreService(db)
    await core_service.spend_cores(
        user_id=current_user.id,
        amount=cost,
        category=f"ai_hint_{level}",
        reference_type="test_sandbox",
        reference_id="test_ai_hint",
        description=f"[沙箱测试] AI{level}提示"
    )
    await db.refresh(current_user)

    return {
        "success": True,
        "hint": hints[level],
        "cost": cost,
        "balance_after": current_user.cores,
        "test_mode": True
    }


# ============================================
# 其他智核获取方式测试
# ============================================

@router.post("/study-time")
async def test_study_time_reward(
    minutes: int = 30,  # 学习时长（分钟）
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试学习时长奖励

    模拟学习一定时长后获得的智核奖励
    规则：每30分钟 +5 智核
    """
    from app.services.core_service import CoreService

    # 计算奖励：每30分钟5智核
    cores_earned = (minutes // 30) * 5

    if cores_earned > 0:
        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=current_user.id,
            amount=cores_earned,
            category="study_time",
            reference_type="test_sandbox",
            reference_id="test_study_time",
            description=f"[沙箱测试] 学习时长奖励 ({minutes}分钟)"
        )
        await db.refresh(current_user)

    return {
        "success": True,
        "minutes": minutes,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": f"学习{minutes}分钟，获得{cores_earned}智核"
    }


@router.post("/daily-exercises")
async def test_daily_exercises_reward(
    completed: int = 10,  # 完成的题目数
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试每日练习完成奖励

    模拟完成每日练习任务后获得的智核奖励
    规则：完成10题 +3 智核，完成20题 +5 智核，完成30题 +10 智核
    """
    from app.services.core_service import CoreService

    # 计算奖励
    cores_earned = 0
    if completed >= 30:
        cores_earned = 10
    elif completed >= 20:
        cores_earned = 5
    elif completed >= 10:
        cores_earned = 3

    if cores_earned > 0:
        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=current_user.id,
            amount=cores_earned,
            category="daily_exercises",
            reference_type="test_sandbox",
            reference_id="test_daily_exercises",
            description=f"[沙箱测试] 每日练习完成奖励 ({completed}题)"
        )
        await db.refresh(current_user)

    return {
        "success": True,
        "completed": completed,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": f"完成{completed}题练习，获得{cores_earned}智核"
    }


@router.post("/daily-accuracy")
async def test_daily_accuracy_reward(
    accuracy: float = 80.0,  # 正确率 (0-100)
    total_questions: int = 20,  # 总题数
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试正确率奖励

    模拟高正确率获得的额外智核奖励
    规则：
    - 正确率 >= 90%: +10 智核
    - 正确率 >= 80%: +5 智核
    - 正确率 >= 70%: +3 智核
    - 需要至少做10题才能获得
    """
    from app.services.core_service import CoreService

    cores_earned = 0

    if total_questions >= 10:
        if accuracy >= 90:
            cores_earned = 10
        elif accuracy >= 80:
            cores_earned = 5
        elif accuracy >= 70:
            cores_earned = 3

    if cores_earned > 0:
        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=current_user.id,
            amount=cores_earned,
            category="daily_accuracy",
            reference_type="test_sandbox",
            reference_id="test_daily_accuracy",
            description=f"[沙箱测试] 正确率奖励 ({accuracy}%)"
        )
        await db.refresh(current_user)

    return {
        "success": True,
        "accuracy": accuracy,
        "total_questions": total_questions,
        "cores_earned": cores_earned,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": f"正确率{accuracy}%，获得{cores_earned}智核"
    }


@router.post("/bonus")
async def test_bonus_reward(
    amount: int = Query(10, le=1000, description="奖励金额，最大1000"),  # 限制上限
    reason: str = "系统测试奖励",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[沙箱] 测试系统奖励

    模拟系统发放的奖励智核
    """
    from app.services.core_service import CoreService

    core_service = CoreService(db)
    await core_service.earn_cores(
        user_id=current_user.id,
        amount=amount,
        category="bonus",
        reference_type="test_sandbox",
        reference_id="test_bonus",
        description=f"[沙箱测试] {reason}"
    )
    await db.refresh(current_user)

    return {
        "success": True,
        "cores_earned": amount,
        "reason": reason,
        "balance_after": current_user.cores,
        "test_mode": True,
        "message": f"系统奖励 +{amount} 智核"
    }


@router.get("/summary")
async def test_summary(
    current_user: User = Depends(get_current_user),
):
    """[沙箱] 获取测试功能总结"""
    return {
        "earn_methods": [
            {
                "name": "每日签到",
                "endpoint": "POST /api/test/checkin",
                "reward": "+5 智核",
                "description": "模拟每日签到"
            },
            {
                "name": "精进之路答题",
                "endpoint": "POST /api/test/mastery/submit",
                "reward": "+2 智核/题",
                "description": "模拟精进之路答题正确"
            },
            {
                "name": "挑战之路答题",
                "endpoint": "POST /api/test/arena/submit",
                "reward": "+3 智核/题",
                "description": "模拟挑战之路答题正确"
            },
            {
                "name": "学习时长奖励",
                "endpoint": "POST /api/test/study-time?minutes=30",
                "reward": "+5 智核/30分钟",
                "description": "模拟学习时长奖励"
            },
            {
                "name": "每日练习完成",
                "endpoint": "POST /api/test/daily-exercises?completed=20",
                "reward": "+3/5/10 智核",
                "description": "10题+3, 20题+5, 30题+10"
            },
            {
                "name": "正确率奖励",
                "endpoint": "POST /api/test/daily-accuracy?accuracy=80",
                "reward": "+3/5/10 智核",
                "description": "70%+3, 80%+5, 90%+10"
            },
            {
                "name": "系统奖励",
                "endpoint": "POST /api/test/bonus?amount=10",
                "reward": "自定义",
                "description": "模拟系统发放奖励"
            }
        ],
        "spend_methods": [
            {
                "name": "轻度提示",
                "endpoint": "POST /api/test/ai-hint/light",
                "cost": "-1 智核",
                "description": "获取思路方向提示"
            },
            {
                "name": "中度提示",
                "endpoint": "POST /api/test/ai-hint/medium",
                "cost": "-3 智核",
                "description": "获取关键步骤提示"
            },
            {
                "name": "深度解析",
                "endpoint": "POST /api/test/ai-hint/deep",
                "cost": "-5 智核",
                "description": "获取完整解题思路"
            }
        ]
    }


logger = logging.getLogger(__name__)