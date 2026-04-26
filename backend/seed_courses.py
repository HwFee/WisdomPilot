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