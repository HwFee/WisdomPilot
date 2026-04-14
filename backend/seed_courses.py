"""Seed script to populate initial course data"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal, init_db
from app.models.course import Course


COURSES = [
    {
        "code": "C",
        "name": "C语言程序设计",
        "description": "C语言基础语法、指针、内存管理、算法实现",
        "difficulty_level": 1,
        "icon": "c-icon"
    },
    {
        "code": "CPP",
        "name": "C++程序设计",
        "description": "C++面向对象、STL模板库、Modern C++特性",
        "difficulty_level": 2,
        "icon": "cpp-icon"
    },
    {
        "code": "Python",
        "name": "Python程序设计",
        "description": "Python基础语法、数据结构、网络编程、人工智能应用",
        "difficulty_level": 1,
        "icon": "python-icon"
    },
    {
        "code": "Java",
        "name": "Java程序设计",
        "description": "Java面向对象、JVM、并发编程、Spring框架",
        "difficulty_level": 2,
        "icon": "java-icon"
    },
    {
        "code": "Rust",
        "name": "Rust程序设计",
        "description": "Rust内存安全、所有权系统、并发编程、系统编程",
        "difficulty_level": 4,
        "icon": "rust-icon"
    },
    {
        "code": "DSA",
        "name": "数据结构与算法",
        "description": "数组、链表、树、图、排序、搜索、动态规划",
        "difficulty_level": 3,
        "icon": "dsa-icon"
    },
    {
        "code": "ADA",
        "name": "算法设计与分析",
        "description": "分治、贪心、动态规划、回溯、近似算法、随机算法",
        "difficulty_level": 4,
        "icon": "ada-icon"
    },
    {
        "code": "DiscreteMath",
        "name": "离散数学",
        "description": "集合论、数理逻辑、图论、组合数学、离散概率",
        "difficulty_level": 3,
        "icon": "discrete-icon"
    },
]


async def seed_courses():
    await init_db()
    async with AsyncSessionLocal() as db:
        for course_data in COURSES:
            # Check if course already exists
            from sqlalchemy import select
            result = await db.execute(
                select(Course).where(Course.code == course_data["code"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Course {course_data['code']} already exists, skipping")
                continue

            course = Course(**course_data)
            db.add(course)
            print(f"Added course: {course_data['code']} - {course_data['name']}")

        await db.commit()
        print("\nSeeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_courses())