"""
初始化C语言课程章节并关联练习题

根据source_id中的知识点将题目分配到对应章节
"""

import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.exercise import Exercise


# C语言课程章节定义
C_LANGUAGE_CHAPTERS = [
    {
        "order_index": 1,
        "title": "C语言入门",
        "description": "学习C语言的基本概念，包括变量、数据类型、输入输出等基础知识",
        "learning_objectives": ["理解C语言程序结构", "掌握基本数据类型", "学会使用printf和scanf", "理解变量和常量"],
        "difficulty_tags": ["入门", "基础"],
        "keywords": ["入门", "基础", "A+B", "输出", "输入", "变量"],
        "estimated_minutes": 60
    },
    {
        "order_index": 2,
        "title": "运算符与表达式",
        "description": "学习算术运算符、关系运算符、逻辑运算符及表达式计算",
        "learning_objectives": ["掌握算术运算符", "理解运算符优先级", "学会使用关系和逻辑运算符"],
        "difficulty_tags": ["运算符", "表达式"],
        "keywords": ["运算", "表达式", "加减乘除", "取余", "比较"],
        "estimated_minutes": 45
    },
    {
        "order_index": 3,
        "title": "流程控制",
        "description": "学习if语句、switch语句、for循环、while循环等流程控制结构",
        "learning_objectives": ["掌握条件判断", "学会使用循环结构", "理解break和continue"],
        "difficulty_tags": ["流程控制", "循环", "判断"],
        "keywords": ["if", "else", "for", "while", "循环", "判断", "分支", "switch"],
        "estimated_minutes": 90
    },
    {
        "order_index": 4,
        "title": "数组与字符串",
        "description": "学习一维数组、二维数组、字符数组和字符串处理",
        "learning_objectives": ["理解数组概念", "掌握一维和二维数组", "学会字符串处理"],
        "difficulty_tags": ["数组", "字符串"],
        "keywords": ["数组", "字符串", "字符", "二维数组", "排序"],
        "estimated_minutes": 90
    },
    {
        "order_index": 5,
        "title": "函数",
        "description": "学习函数的定义、调用、参数传递和递归",
        "learning_objectives": ["理解函数概念", "掌握参数传递", "学会递归编程"],
        "difficulty_tags": ["函数", "递归"],
        "keywords": ["函数", "递归", "阶乘", "斐波那契", "调用"],
        "estimated_minutes": 120
    },
    {
        "order_index": 6,
        "title": "指针",
        "description": "学习指针的概念、指针运算、指针与数组、指针与函数",
        "learning_objectives": ["理解指针概念", "掌握指针运算", "学会指针与数组配合使用"],
        "difficulty_tags": ["指针", "内存"],
        "keywords": ["指针", "地址", "内存", "引用"],
        "estimated_minutes": 120
    },
    {
        "order_index": 7,
        "title": "结构体与联合体",
        "description": "学习结构体的定义、使用、结构体数组、链表基础",
        "learning_objectives": ["理解结构体概念", "掌握结构体操作", "学会链表基础"],
        "difficulty_tags": ["结构体", "链表"],
        "keywords": ["结构体", "struct", "链表", "节点"],
        "estimated_minutes": 90
    },
    {
        "order_index": 8,
        "title": "文件操作",
        "description": "学习文件的打开、关闭、读写操作",
        "learning_objectives": ["理解文件概念", "掌握文件读写", "学会文件操作函数"],
        "difficulty_tags": ["文件", "IO"],
        "keywords": ["文件", "file", "fopen", "读写"],
        "estimated_minutes": 60
    },
    {
        "order_index": 9,
        "title": "算法基础",
        "description": "学习基础算法思想，包括查找、排序、递归算法等",
        "learning_objectives": ["理解算法思想", "掌握基本排序算法", "学会二分查找"],
        "difficulty_tags": ["算法", "排序", "查找"],
        "keywords": ["算法", "排序", "查找", "二分", "冒泡", "选择", "插入"],
        "estimated_minutes": 150
    },
    {
        "order_index": 10,
        "title": "数据结构入门",
        "description": "学习基础数据结构，包括栈、队列、链表、树等",
        "learning_objectives": ["理解数据结构概念", "掌握栈和队列", "学会基本树操作"],
        "difficulty_tags": ["数据结构", "栈", "队列"],
        "keywords": ["数据结构", "栈", "队列", "树", "链表"],
        "estimated_minutes": 180
    }
]


async def init_chapters():
    """初始化C语言章节"""
    async with AsyncSessionLocal() as session:
        # 获取C语言课程
        result = await session.execute(select(Course).where(Course.code == 'C'))
        course = result.scalar_one_or_none()

        if not course:
            print("未找到C语言课程！")
            return

        print(f"课程: {course.name} (ID: {course.id})")

        # 检查是否已有章节
        result = await session.execute(
            select(Chapter).where(Chapter.course_id == course.id)
        )
        existing = result.scalars().all()

        if existing:
            print(f"已有 {len(existing)} 个章节，跳过创建")
            chapters = {ch.order_index: ch for ch in existing}
        else:
            # 创建章节
            chapters = {}
            for ch_data in C_LANGUAGE_CHAPTERS:
                chapter = Chapter(
                    course_id=course.id,
                    order_index=ch_data["order_index"],
                    title=ch_data["title"],
                    description=ch_data["description"],
                    learning_objectives=ch_data["learning_objectives"],
                    difficulty_tags=ch_data["difficulty_tags"],
                    estimated_minutes=ch_data["estimated_minutes"]
                )
                session.add(chapter)
                chapters[ch_data["order_index"]] = chapter

            await session.commit()
            print(f"已创建 {len(chapters)} 个章节")

        # 关联练习题到章节
        await assign_exercises_to_chapters(session, chapters)

        await session.commit()
        print("完成！")


async def assign_exercises_to_chapters(session, chapters):
    """将练习题关联到章节"""
    # 获取所有练习题
    result = await session.execute(select(Exercise))
    exercises = result.scalars().all()

    print(f"\n共 {len(exercises)} 道练习题")

    assigned_count = 0

    for ex in exercises:
        source_id = ex.source_id or ""
        content = ex.content or {}
        title = content.get("title", "")
        description = content.get("description", "")

        # 合并所有文本用于匹配
        text = f"{source_id} {title} {description}".lower()

        # 根据关键词匹配章节
        chapter_id = None

        for order_idx, ch_data in enumerate(C_LANGUAGE_CHAPTERS, 1):
            keywords = ch_data.get("keywords", [])
            for kw in keywords:
                if kw.lower() in text:
                    chapter_id = chapters[order_idx].id
                    break
            if chapter_id:
                break

        # 如果没有匹配，根据难度分配
        if not chapter_id:
            if ex.difficulty <= 1:
                chapter_id = chapters[1].id  # 入门章节
            elif ex.difficulty == 2:
                chapter_id = chapters[5].id  # 函数章节
            elif ex.difficulty == 3:
                chapter_id = chapters[9].id  # 算法基础
            else:
                chapter_id = chapters[10].id  # 数据结构

        ex.chapter_id = chapter_id
        assigned_count += 1

    print(f"已关联 {assigned_count} 道题目到章节")

    # 统计各章节数量
    for order_idx, chapter in chapters.items():
        result = await session.execute(
            select(Exercise).where(Exercise.chapter_id == chapter.id)
        )
        count = len(result.scalars().all())
        print(f"  章节{order_idx} ({chapter.title}): {count} 题")


if __name__ == "__main__":
    asyncio.run(init_chapters())
