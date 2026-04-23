"""
迁移脚本：创建小节知识点内容表，并重新生成第一章数据

执行方式：
python -m migrations.005_create_knowledge_points_and_questions
"""

import asyncio
import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete, text
from app.database import AsyncSessionLocal, engine
from app.models.section_knowledge_point import SectionKnowledgePoint
from app.models.section_base_question import SectionBaseQuestion
from app.models.section import Section
from app.models.chapter import Chapter
from app.services.ai import ai_service
from app.schemas.ai import AIProviderConfig
from app.config import get_settings


def configure_ai():
    """配置 AI 服务"""
    settings = get_settings()
    config = AIProviderConfig(
        provider=settings.AI_PROVIDER,
        api_key=settings.AI_API_KEY,
        model=settings.AI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        base_url=settings.AI_BASE_URL,
        local_base_url=settings.AI_LOCAL_BASE_URL,
        is_local_first=settings.AI_LOCAL_FIRST,
    )
    ai_service.configure(config)
    return ai_service.is_configured()


async def create_table():
    """创建新表"""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS section_knowledge_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                order_index INTEGER DEFAULT 1,
                content TEXT,
                summary VARCHAR(500),
                code_example TEXT,
                code_language VARCHAR(20) DEFAULT 'c',
                code_explanation TEXT,
                difficulty INTEGER DEFAULT 1,
                importance INTEGER DEFAULT 1,
                related_points JSON,
                tips JSON,
                common_mistakes JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_skp_section_order
            ON section_knowledge_points(section_id, order_index)
        """))
    print("[OK] Created section_knowledge_points table")


async def generate_section_content(section: Section, db) -> tuple:
    """为单个小节生成知识点内容和题目

    Returns:
        (知识点列表, 题目列表)
    """
    if not ai_service.is_configured():
        print(f"  [WARN] AI not configured, skip section {section.id}")
        return [], []

    prompt = f"""你是一位专业的C语言编程教学老师。请为以下小节设计学习内容。

小节标题：{section.title}
小节描述：{section.description or '无'}
小节内容概要：{section.content or '无'}
学习目标：{json.dumps(section.learning_objectives or [], ensure_ascii=False)}

请生成：
1. 3-5 个知识点（每个知识点包含：名称、讲解内容、代码示例）
2. 基础测试题（每个知识点 2 道题，确保做完能掌握）

重要要求：
- 知识点必须与小节内容直接相关
- 每个知识点要有清晰的讲解
- 代码示例要简单易懂
- 题目要覆盖所有知识点
- 题目难度为入门级别（1-2）

请以 JSON 格式返回：
```json
{{
  "knowledge_points": [
    {{
      "name": "知识点名称",
      "order_index": 1,
      "content": "知识点详细讲解内容，可以包含多个段落",
      "summary": "简要总结一句话",
      "code_example": "代码示例",
      "code_language": "c",
      "code_explanation": "代码解释",
      "difficulty": 1,
      "tips": ["提示1", "提示2"],
      "common_mistakes": ["常见错误1"]
    }}
  ],
  "questions": [
    {{
      "order_index": 1,
      "type": "choice",
      "text": "题目内容",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct_answer": "A",
      "explanation": "解析",
      "knowledge_points": ["知识点名称"],
      "difficulty": 1
    }}
  ]
}}
```

现在请生成内容："""

    try:
        response = await ai_service.generate(prompt)

        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group(0))
            return data.get('knowledge_points', []), data.get('questions', [])
        else:
            print(f"  [WARN] No JSON found in response")
            return [], []

    except Exception as e:
        print(f"  [ERROR] {e}")
        return [], []


async def main():
    """主函数"""

    # 1. 创建新表
    print("=" * 60)
    print("Step 1: Creating table...")
    await create_table()

    # 2. 配置 AI
    print("\n" + "=" * 60)
    print("Step 2: Configuring AI...")
    if not configure_ai():
        print("[ERROR] AI service configuration failed")
        return
    print(f"[OK] AI configured: {get_settings().AI_PROVIDER}")

    # 3. 为第一章生成数据
    print("\n" + "=" * 60)
    print("Step 3: Generating content for Chapter 1...")

    async with AsyncSessionLocal() as db:
        # 获取第一章的小节
        result = await db.execute(
            select(Section).where(Section.chapter_id == 1).order_by(Section.order_index)
        )
        sections = result.scalars().all()

        print(f"Found {len(sections)} sections")

        total_kps = 0
        total_questions = 0

        for section in sections:
            print(f"\n--- Section {section.order_index}: {section.title} ---")

            # 删除旧数据
            await db.execute(
                delete(SectionKnowledgePoint).where(SectionKnowledgePoint.section_id == section.id)
            )
            await db.execute(
                delete(SectionBaseQuestion).where(
                    SectionBaseQuestion.section_id == section.id,
                    SectionBaseQuestion.question_source == 'base'
                )
            )

            # 生成新内容
            kps_data, questions_data = await generate_section_content(section, db)

            # 保存知识点
            for kp_data in kps_data:
                kp = SectionKnowledgePoint(
                    section_id=section.id,
                    name=kp_data.get('name', ''),
                    order_index=kp_data.get('order_index', 1),
                    content=kp_data.get('content', ''),
                    summary=kp_data.get('summary', ''),
                    code_example=kp_data.get('code_example', ''),
                    code_language=kp_data.get('code_language', 'c'),
                    code_explanation=kp_data.get('code_explanation', ''),
                    difficulty=kp_data.get('difficulty', 1),
                    tips=kp_data.get('tips', []),
                    common_mistakes=kp_data.get('common_mistakes', []),
                    is_active=True,
                )
                db.add(kp)
                total_kps += 1

            # 保存题目
            for q_data in questions_data:
                question = SectionBaseQuestion(
                    section_id=section.id,
                    chapter_id=section.chapter_id,
                    order_index=q_data.get('order_index', 1),
                    question_type=q_data.get('type', 'choice'),
                    question_text=q_data.get('text', ''),
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer', ''),
                    explanation=q_data.get('explanation', ''),
                    knowledge_points=q_data.get('knowledge_points', []),
                    difficulty=q_data.get('difficulty', 1),
                    question_source='base',
                    is_active=True,
                )
                db.add(question)
                total_questions += 1

            await db.commit()
            print(f"  Generated: {len(kps_data)} knowledge points, {len(questions_data)} questions")

            # 避免 API 限流
            await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print(f"DONE! Total: {total_kps} knowledge points, {total_questions} questions")


if __name__ == "__main__":
    asyncio.run(main())
