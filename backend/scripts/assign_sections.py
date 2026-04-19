#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分配现有基础测试题到小节

每个章节的基础测试题（5道）均匀分配到该章节的小节
"""

import asyncio
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.utils.time import utc_now


async def assign_base_questions():
    """分配基础测试题到小节"""
    async with AsyncSessionLocal() as db:
        now = utc_now().isoformat()

        # 1. 为没有小节的章节创建小节
        result = await db.execute(text('''
            SELECT c.id, c.title
            FROM chapters c
            LEFT JOIN sections s ON s.chapter_id = c.id
            WHERE s.id IS NULL
            ORDER BY c.id
        '''))
        chapters_without_sections = result.fetchall()

        print(f"需要创建小节的章节数: {len(chapters_without_sections)}")

        for chapter_id, chapter_title in chapters_without_sections:
            # 创建3个小节
            for i, suffix in enumerate(["基础概念", "深入理解", "实践应用"], 1):
                await db.execute(text(f'''
                    INSERT INTO sections (chapter_id, title, description, order_index, estimated_minutes, is_active, created_at, updated_at)
                    VALUES ({chapter_id}, '{chapter_title} - {suffix}', '{suffix}学习', {i}, 15, 1, '{now}', '{now}')
                '''))
            print(f"  章节 {chapter_id} 创建了 3 个小节")

        await db.commit()

        # 2. 获取所有小节，按章节分组
        result = await db.execute(text('''
            SELECT id, chapter_id, order_index
            FROM sections
            ORDER BY chapter_id, order_index
        '''))
        sections = result.fetchall()

        chapter_sections = {}
        for section_id, chapter_id, order_index in sections:
            if chapter_id not in chapter_sections:
                chapter_sections[chapter_id] = []
            chapter_sections[chapter_id].append(section_id)

        # 3. 分配题目到小节（每章节的题目轮流分配）
        result = await db.execute(text('''
            SELECT id, chapter_id, order_index
            FROM chapter_base_questions
            WHERE section_id IS NULL
            ORDER BY chapter_id, order_index
        '''))
        questions = result.fetchall()

        updated = 0
        for question_id, chapter_id, order_index in questions:
            if chapter_id in chapter_sections:
                sections_list = chapter_sections[chapter_id]
                # 按题目顺序分配到不同小节
                section_index = (order_index - 1) % len(sections_list) if order_index else updated % len(sections_list)
                section_id = sections_list[section_index]

                await db.execute(text(f'''
                    UPDATE chapter_base_questions SET section_id = {section_id} WHERE id = {question_id}
                '''))
                updated += 1

        await db.commit()
        print(f"\n分配完成！共更新 {updated} 道题目")

        # 4. 验证
        result = await db.execute(text('''
            SELECT s.id, s.title, COUNT(q.id) as cnt
            FROM sections s
            LEFT JOIN chapter_base_questions q ON q.section_id = s.id
            GROUP BY s.id
            ORDER BY s.chapter_id, s.order_index
            LIMIT 15
        '''))
        print("\n=== 小节题目分布 ===")
        for row in result.fetchall():
            title = row[1][:25] if len(row[1]) > 25 else row[1]
            print(f"小节{row[0]}: {title}... | {row[2]}题")


if __name__ == "__main__":
    print("=" * 50)
    print(" 分配基础测试题到小节")
    print("=" * 50)
    asyncio.run(assign_base_questions())
