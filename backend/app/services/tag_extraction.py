"""
Tag Extraction Service for Hybrid Recommendation

Uses AI to extract structured tags from exercises for better matching.

Tags extracted:
    - knowledge_points: Related concepts (e.g., ["数组", "双指针", "排序"])
    - algorithm_type: Algorithm category (e.g., "贪心", "动态规划")
    - data_structures: Required data structures (e.g., ["数组", "链表"])
    - difficulty_signals: Complexity indicators
    - prerequisite_skills: Skills needed to solve
    - problem_pattern: Problem type (e.g., "最值问题", "计数问题")
    - time_complexity: Expected complexity (e.g., "O(n)")
    - keywords: Important terms for matching
    - estimated_difficulty: AI-estimated difficulty (1-8)
"""

import json
from typing import Optional
from dataclasses import dataclass, field, asdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai import ai_service


@dataclass
class ExtractedTags:
    """Structured tags extracted from an exercise."""

    knowledge_points: list[str] = field(default_factory=list)
    algorithm_type: Optional[str] = None
    data_structures: list[str] = field(default_factory=list)
    difficulty_signals: list[str] = field(default_factory=list)
    prerequisite_skills: list[str] = field(default_factory=list)
    problem_pattern: Optional[str] = None
    time_complexity: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    estimated_difficulty: int = 3

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None and v != []}

    def to_embedding_text(self) -> str:
        """Convert to text for embedding."""
        parts = []

        if self.knowledge_points:
            parts.append(f"知识点：{', '.join(self.knowledge_points)}")
        if self.algorithm_type:
            parts.append(f"算法类型：{self.algorithm_type}")
        if self.data_structures:
            parts.append(f"数据结构：{', '.join(self.data_structures)}")
        if self.problem_pattern:
            parts.append(f"题目模式：{self.problem_pattern}")
        if self.time_complexity:
            parts.append(f"时间复杂度：{self.time_complexity}")
        if self.keywords:
            parts.append(f"关键词：{', '.join(self.keywords)}")
        if self.difficulty_signals:
            parts.append(f"难度信号：{', '.join(self.difficulty_signals)}")

        return "\n".join(parts)


class TagExtractionService:
    """
    Service for extracting structured tags from exercises using AI.

    Usage:
        service = TagExtractionService()
        tags = await service.extract_tags(
            question_text="题目内容...",
            exercise_type="programming",
        )
    """

    def __init__(self):
        self._cache: dict[int, ExtractedTags] = {}

    async def extract_tags(
        self,
        question_text: str,
        exercise_type: str = "choice",
        options: Optional[list[str]] = None,
        code_template: Optional[str] = None,
        existing_knowledge_points: Optional[list[str]] = None,
    ) -> ExtractedTags:
        """
        Extract structured tags from exercise content.

        Args:
            question_text: The question text
            exercise_type: Type of exercise (choice, programming, fill_blank)
            options: Optional list of choice options
            code_template: Optional code template for programming exercises
            existing_knowledge_points: Existing knowledge points to include

        Returns:
            ExtractedTags object with structured tags
        """
        if not ai_service.is_configured():
            # Return default tags if AI not configured
            return self._default_tags(question_text, existing_knowledge_points)

        # Build prompt
        prompt = self._build_extraction_prompt(
            question_text, exercise_type, options, code_template, existing_knowledge_points
        )

        try:
            response = await ai_service._provider.generate_explanation(prompt)
            tags = self._parse_response(response)

            # Merge with existing knowledge points
            if existing_knowledge_points:
                for kp in existing_knowledge_points:
                    if kp not in tags.knowledge_points:
                        tags.knowledge_points.append(kp)

            return tags
        except Exception as e:
            # Fallback to default tags on error
            return self._default_tags(question_text, existing_knowledge_points)

    def _build_extraction_prompt(
        self,
        question_text: str,
        exercise_type: str,
        options: Optional[list[str]],
        code_template: Optional[str],
        existing_knowledge_points: Optional[list[str]],
    ) -> str:
        """Build AI prompt for tag extraction."""
        type_labels = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
        }

        context_parts = [
            f"题目类型：{type_labels.get(exercise_type, '未知')}",
            f"题目内容：{question_text}",
        ]

        if options:
            context_parts.append(f"选项：{', '.join(options)}")

        if code_template:
            context_parts.append(f"代码模板：\n{code_template}")

        if existing_knowledge_points:
            context_parts.append(f"已有知识点标签：{', '.join(existing_knowledge_points)}")

        context = "\n".join(context_parts)

        return f"""请分析以下编程练习题，提取结构化标签：

{context}

请以 JSON 格式返回以下信息：
```json
{{
  "knowledge_points": ["知识点1", "知识点2"],
  "algorithm_type": "算法类型（如：贪心、动态规划、分治等，没有可填null）",
  "data_structures": ["数据结构1", "数据结构2"],
  "difficulty_signals": ["难度信号1", "难度信号2"],
  "prerequisite_skills": ["前置技能1", "前置技能2"],
  "problem_pattern": "题目模式（如：最值问题、计数问题、路径问题等）",
  "time_complexity": "时间复杂度（如：O(n)、O(nlogn)等）",
  "keywords": ["关键词1", "关键词2"],
  "estimated_difficulty": 3
}}
```

要求：
1. estimated_difficulty 使用 1-8 级洛谷体系：1入门 2普及- 3普及/提高- 4普及+/提高 5提高+/省选- 6省选/NOI- 7NOI 8NOI+/CTSC
2. 根据题目复杂度合理估计难度
3. knowledge_points 是最重要的标签，请详细列出
4. difficulty_signals 描述题目的难点（如：边界条件多、需要优化空间、代码量大等）
5. prerequisite_skills 列出解决此题需要掌握的基础知识
6. JSON 格式必须合法

请直接返回 JSON，不要有其他内容："""

    def _parse_response(self, response: str) -> ExtractedTags:
        """Parse AI response into ExtractedTags."""
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                data = json.loads(response)

            return ExtractedTags(
                knowledge_points=data.get("knowledge_points", []),
                algorithm_type=data.get("algorithm_type"),
                data_structures=data.get("data_structures", []),
                difficulty_signals=data.get("difficulty_signals", []),
                prerequisite_skills=data.get("prerequisite_skills", []),
                problem_pattern=data.get("problem_pattern"),
                time_complexity=data.get("time_complexity"),
                keywords=data.get("keywords", []),
                estimated_difficulty=data.get("estimated_difficulty", 3),
            )
        except (json.JSONDecodeError, KeyError):
            return ExtractedTags()

    def _default_tags(
        self,
        question_text: str,
        existing_knowledge_points: Optional[list[str]],
    ) -> ExtractedTags:
        """Generate default tags when AI is not available."""
        # Simple keyword extraction from question text
        keywords = []

        # Common programming keywords to look for
        keyword_patterns = [
            "数组", "链表", "树", "图", "排序", "搜索", "递归", "迭代",
            "动态规划", "贪心", "分治", "回溯", "双指针", "滑动窗口",
            "哈希", "栈", "队列", "堆", "二叉树", "二分查找",
        ]

        for kw in keyword_patterns:
            if kw in question_text:
                keywords.append(kw)

        return ExtractedTags(
            knowledge_points=existing_knowledge_points or keywords,
            keywords=keywords,
            estimated_difficulty=3,
        )

    async def batch_extract(
        self,
        exercises: list[dict],
    ) -> list[ExtractedTags]:
        """
        Extract tags for multiple exercises.

        Args:
            exercises: List of exercise dicts with 'id', 'content', 'type'

        Returns:
            List of ExtractedTags in same order
        """
        results = []

        for ex in exercises:
            content = ex.get("content", {})
            question_text = content.get("text", "") or content.get("description", "")
            options = content.get("options")
            code_template = content.get("code_template")
            existing_kp = ex.get("knowledge_points")

            tags = await self.extract_tags(
                question_text=question_text,
                exercise_type=ex.get("type", "choice"),
                options=options,
                code_template=code_template,
                existing_knowledge_points=existing_kp,
            )
            results.append(tags)

        return results


# Singleton instance
tag_extraction_service = TagExtractionService()


def get_tag_extraction_service() -> TagExtractionService:
    """Get the tag extraction service singleton."""
    return tag_extraction_service
