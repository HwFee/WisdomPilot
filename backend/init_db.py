"""
一键初始化脚本 - 初始化课程、章节和关卡数据
用于新用户克隆项目后快速启动

使用方法：
    cd backend
    python init_db.py
"""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.stage import Stage


# 8门课程数据
COURSES = [
    {"code": "C", "name": "C语言程序设计", "description": "C语言基础语法、指针、内存管理、算法实现", "difficulty_level": 1, "icon": "c-icon"},
    {"code": "CPP", "name": "C++程序设计", "description": "C++面向对象、STL模板库、Modern C++特性", "difficulty_level": 2, "icon": "cpp-icon"},
    {"code": "Python", "name": "Python程序设计", "description": "Python基础语法、数据结构、网络编程、人工智能应用", "difficulty_level": 1, "icon": "python-icon"},
    {"code": "Java", "name": "Java程序设计", "description": "Java面向对象、JVM、并发编程、Spring框架", "difficulty_level": 2, "icon": "java-icon"},
    {"code": "Rust", "name": "Rust程序设计", "description": "Rust内存安全、所有权系统、并发编程、系统编程", "difficulty_level": 4, "icon": "rust-icon"},
    {"code": "DSA", "name": "数据结构与算法", "description": "数组、链表、树、图、排序、搜索、动态规划", "difficulty_level": 3, "icon": "dsa-icon"},
    {"code": "ADA", "name": "算法设计与分析", "description": "分治、贪心、动态规划、回溯、近似算法、随机算法", "difficulty_level": 4, "icon": "ada-icon"},
    {"code": "DiscreteMath", "name": "离散数学", "description": "集合论、数理逻辑、图论、组合数学、离散概率", "difficulty_level": 3, "icon": "discrete-icon"},
]

# C语言章节（作为示例，其他课程可以后续添加）
C_LANGUAGE_CHAPTERS = [
    {"order_index": 1, "title": "C语言入门", "description": "学习C语言的基本概念，包括变量、数据类型、输入输出等基础知识"},
    {"order_index": 2, "title": "变量与数据类型", "description": "学习C语言中的基本数据类型、变量定义和常量"},
    {"order_index": 3, "title": "运算符与表达式", "description": "学习算术运算符、关系运算符、逻辑运算符及表达式计算"},
    {"order_index": 4, "title": "流程控制", "description": "学习if语句、switch语句、for循环、while循环等流程控制结构"},
    {"order_index": 5, "title": "数组与字符串", "description": "学习一维数组、二维数组、字符数组和字符串处理"},
    {"order_index": 6, "title": "函数", "description": "学习函数的定义、调用、参数传递和递归"},
    {"order_index": 7, "title": "指针基础", "description": "学习指针的概念、指针运算、指针与数组"},
    {"order_index": 8, "title": "指针进阶", "description": "学习指针与函数、指针数组、多级指针"},
    {"order_index": 9, "title": "结构体与联合体", "description": "学习结构体的定义、使用、结构体数组、链表基础"},
    {"order_index": 10, "title": "文件操作", "description": "学习文件的打开、关闭、读写操作"},
]

# 为每个章节创建对应的关卡
def get_stages_for_chapter(chapter_order: int, chapter_title: str) -> list:
    """为章节生成关卡"""
    return [
        {"title": f"{chapter_title} - 基础练习", "description": f"掌握{chapter_title}的基础知识", "difficulty": 1, "order_index": 1},
        {"title": f"{chapter_title} - 进阶练习", "description": f"深入理解{chapter_title}", "difficulty": 2, "order_index": 2},
    ]


async def init_all_data():
    """初始化所有数据"""
    print("🚀 开始初始化数据库...")

    # 初始化数据库表结构
    await init_db()
    print("✅ 数据库表结构初始化完成")

    async with AsyncSessionLocal() as db:
        # 1. 初始化课程
        print("\n📚 初始化课程...")
        for course_data in COURSES:
            result = await db.execute(select(Course).where(Course.code == course_data["code"]))
            existing = result.scalar_one_or_none()
            if not existing:
                course = Course(**course_data)
                db.add(course)
                print(f"   + {course_data['code']}: {course_data['name']}")
            else:
                print(f"   ✓ {course_data['code']}: 已存在")

        await db.commit()

        # 2. 初始化C语言章节和关卡
        print("\n📖 初始化C语言章节和关卡...")
        c_course = (await db.execute(select(Course).where(Course.code == "C"))).scalar_one_or_none()
        if c_course:
            for chapter_data in C_LANGUAGE_CHAPTERS:
                result = await db.execute(
                    select(Chapter).where(Chapter.course_id == c_course.id, Chapter.order_index == chapter_data["order_index"])
                )
                existing_chapter = result.scalar_one_or_none()

                if not existing_chapter:
                    chapter = Chapter(
                        course_id=c_course.id,
                        order_index=chapter_data["order_index"],
                        title=chapter_data["title"],
                        description=chapter_data["description"],
                    )
                    db.add(chapter)
                    await db.flush()  # 获取 chapter.id

                    # 为章节创建关卡
                    stages = get_stages_for_chapter(chapter_data["order_index"], chapter_data["title"])
                    for stage_data in stages:
                        stage = Stage(
                            course_id=c_course.id,
                            chapter_id=chapter.id,
                            title=stage_data["title"],
                            description=stage_data["description"],
                            difficulty=stage_data["difficulty"],
                            order_index=stage_data["order_index"],
                        )
                        db.add(stage)
                    print(f"   + {chapter_data['title']} (含{len(stages)}个关卡)")
                else:
                    print(f"   ✓ {chapter_data['title']}: 已存在")

        await db.commit()

        # 3. 统计数据
        courses_count = (await db.execute(select(Course))).scalars().all().__len__()
        chapters_count = (await db.execute(select(Chapter))).scalars().all().__len__()
        stages_count = (await db.execute(select(Stage))).scalars().all().__len__()

        print("\n" + "="*50)
        print("✅ 初始化完成!")
        print(f"   📚 课程: {courses_count} 门")
        print(f"   📖 章节: {chapters_count} 个")
        print(f"   🎯 关卡: {stages_count} 个")
        print("="*50)
        print("\n💡 提示: 运行后端服务:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    asyncio.run(init_all_data())
