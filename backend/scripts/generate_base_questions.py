"""
生成章节基础测试题的脚本

使用 Minimax AI 为每个章节生成 3-5 道基础测试题。
题目超级基础，仅测试知识点掌握。
"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.chapter import Chapter
from app.models.section_base_question import SectionBaseQuestion
from app.services.ai import ai_service
from app.schemas.ai import AIProviderConfig
from app.config import get_settings
from app.utils.time import utc_now


def configure_ai_service():
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


async def generate_with_retry(prompt: str, max_retries: int = 3, delay: float = 5.0) -> str:
    """带重试的 AI 生成"""
    import httpx

    for attempt in range(max_retries):
        try:
            response = await ai_service._provider.generate_explanation(prompt)
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [429, 500, 529]:  # Rate limit or server error
                if attempt < max_retries - 1:
                    wait_time = delay * (attempt + 1)  # Exponential backoff
                    print(f"    [RETRY] Server busy, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            else:
                raise
    return ""


async def generate_base_questions_for_chapter(chapter: Chapter, count: int = 5) -> list:
    """为单个章节生成基础测试题"""

    if not ai_service.is_configured():
        print(f"  [WARN] AI not configured, skip chapter {chapter.id}")
        return []

    prompt = f"""你是一位专业的编程教学出题老师。请为以下章节生成 {count} 道基础测试题。

章节标题：{chapter.title}
章节描述：{chapter.description or '无描述'}
章节序号：{chapter.order_index}

要求：
1. 题目必须超级基础，仅测试知识点的基本掌握
2. 难度固定为 1-2（入门/基础级别）
3. 大部分为选择题（type: choice），可以有 1-2 道填空题（type: fill_blank）
4. 每道题聚焦一个核心知识点
5. 选择题必须有 4 个选项，正确答案为 A/B/C/D 之一

请以 JSON 数组格式返回，格式如下：
```json
[
  {{
    "order_index": 1,
    "type": "choice",
    "text": "题目内容",
    "options": ["选项A内容", "选项B内容", "选项C内容", "选项D内容"],
    "correct_answer": "A",
    "explanation": "答案解析",
    "knowledge_points": ["知识点1"]
  }}
]
```

现在请生成 {count} 道基础测试题："""

    try:
        # 使用带重试的 AI 生成
        response = await generate_with_retry(prompt, max_retries=5, delay=10.0)

        if not response:
            print(f"  [ERROR] Empty response after retries")
            return []

        # 提取 JSON 数组
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response

        questions_data = json.loads(json_str)
        return questions_data

    except Exception as e:
        print(f"  [ERROR] AI generation failed: {e}")
        return []


async def main():
    """主函数：为所有章节生成基础题"""

    # 首先配置 AI 服务
    if not configure_ai_service():
        print("[ERROR] AI service configuration failed")
        print("Please check your .env file for AI_PROVIDER, AI_API_KEY, AI_MODEL settings")
        return

    print(f"[INFO] AI Service configured successfully")
    print(f"       Provider: {get_settings().AI_PROVIDER}")
    print(f"       Model: {get_settings().AI_MODEL}")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        # 获取所有章节
        result = await db.execute(
            select(Chapter).where(Chapter.is_active == True).order_by(Chapter.course_id, Chapter.order_index)
        )
        chapters = result.scalars().all()

        print(f"[INFO] Found {len(chapters)} chapters")
        print("=" * 50)

        generated_count = 0

        for chapter in chapters:
            print(f"\n[CHAPTER] Processing: {chapter.title} (ID: {chapter.id})")

            # 检查是否已有基础题
            existing_result = await db.execute(
                select(SectionBaseQuestion).where(SectionBaseQuestion.chapter_id == chapter.id)
            )
            existing = existing_result.scalars().all()

            if len(existing) >= 3:
                print(f"  [SKIP] Already has {len(existing)} questions")
                continue

            # 生成基础题
            questions_data = await generate_base_questions_for_chapter(chapter, count=5)

            if not questions_data:
                print(f"  [WARN] No questions generated")
                continue

            # 保存到数据库
            for q_data in questions_data:
                question = SectionBaseQuestion(
                    chapter_id=chapter.id,
                    order_index=q_data.get("order_index", 1),
                    question_type=q_data.get("type", "choice"),
                    question_text=q_data.get("text", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", ""),
                    explanation=q_data.get("explanation", ""),
                    knowledge_points=q_data.get("knowledge_points", []),
                    difficulty=q_data.get("difficulty", 1),
                    is_active=True,
                )
                db.add(question)
                generated_count += 1

            await db.commit()
            print(f"  [OK] Generated {len(questions_data)} questions")

            # 添加章节间延迟，避免 API 限流
            await asyncio.sleep(3)

        print("\n" + "=" * 50)
        print(f"[DONE] Total generated: {generated_count} base questions")


if __name__ == "__main__":
    asyncio.run(main())
