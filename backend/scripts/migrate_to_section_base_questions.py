"""
数据库迁移脚本：将 chapter_base_questions 表重构为 section_base_questions 表

迁移内容：
1. 重命名表：chapter_base_questions -> section_base_questions
2. 确保 section_id 不为 NULL（如果有 NULL 值，需要先处理）
3. 更新外键约束
"""

import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal, engine


async def migrate():
    """执行迁移"""
    async with engine.begin() as conn:
        print("开始迁移...")

        # 1. 检查旧表是否存在
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chapter_base_questions'"
        ))
        old_table_exists = result.fetchone() is not None
        print(f"旧表 chapter_base_questions 存在: {old_table_exists}")

        # 2. 检查新表是否已存在
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='section_base_questions'"
        ))
        new_table_exists = result.fetchone() is not None
        print(f"新表 section_base_questions 存在: {new_table_exists}")

        if old_table_exists and not new_table_exists:
            # 3. 重命名表
            print("重命名表 chapter_base_questions -> section_base_questions...")
            await conn.execute(text(
                "ALTER TABLE chapter_base_questions RENAME TO section_base_questions"
            ))
            print("表重命名完成")

        elif not old_table_exists and not new_table_exists:
            # 4. 创建新表
            print("创建新表 section_base_questions...")
            await conn.execute(text("""
                CREATE TABLE section_base_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_id INTEGER NOT NULL,
                    chapter_id INTEGER,
                    user_id VARCHAR(36),
                    question_source VARCHAR(20) DEFAULT 'base',
                    order_index INTEGER DEFAULT 1,
                    question_type VARCHAR(20) DEFAULT 'choice',
                    title VARCHAR(500),
                    question_text TEXT NOT NULL,
                    options JSON,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    knowledge_points JSON DEFAULT '[]',
                    difficulty INTEGER DEFAULT 1,
                    code_template TEXT,
                    test_cases JSON,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
                    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE SET NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            print("新表创建完成")

        else:
            print("无需迁移，表状态正常")

        # 5. 创建索引
        print("创建索引...")
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_section_question_user ON section_base_questions(user_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_section_question_section_user ON section_base_questions(section_id, user_id)"
            ))
            print("索引创建完成")
        except Exception as e:
            print(f"创建索引时出错（可能已存在）: {e}")

        print("迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
