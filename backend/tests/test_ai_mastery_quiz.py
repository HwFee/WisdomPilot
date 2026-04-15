"""
Tests for AI Service - Mastery Quiz Generation

TDD: Testing AI service methods for mastery quiz generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestGenerateKnowledgeContent:
    """Tests for AI knowledge content generation"""

    @pytest.mark.asyncio
    async def test_generate_knowledge_content_success(self):
        """Should generate knowledge content successfully"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig

        # Configure AI service
        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            temperature=0.7
        )
        ai_service.configure(config)

        # Mock the provider
        mock_response = json.dumps({
            "knowledge_points": [
                {
                    "id": "kp_001",
                    "title": "变量与数据类型",
                    "content": "变量是存储数据的容器...",
                    "examples": ["int x = 10;"],
                    "difficulty": 1
                }
            ]
        })

        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response

            result = await ai_service.generate_knowledge_content(
                chapter_title="C语言基础",
                chapter_description="学习C语言的基本概念",
                course_name="C语言程序设计"
            )

            assert result is not None
            assert "knowledge_points" in result
            assert len(result["knowledge_points"]) == 1
            assert result["knowledge_points"][0]["title"] == "变量与数据类型"

    @pytest.mark.asyncio
    async def test_generate_knowledge_content_not_configured(self):
        """Should return empty dict when AI not configured"""
        from app.services.ai import AIService

        # Create unconfigured service
        service = AIService()

        result = await service.generate_knowledge_content(
            chapter_title="测试章节",
            chapter_description="测试描述"
        )

        assert result == {}


class TestGeneratePersonalizedQuiz:
    """Tests for AI personalized quiz generation"""

    @pytest.mark.asyncio
    async def test_generate_quiz_with_user_profile(self):
        """Should generate quiz based on user profile"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig
        from app.schemas.mastery_quiz import UserProfileForQuiz

        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        ai_service.configure(config)

        user_profile = UserProfileForQuiz(
            user_id="user_001",
            course_id=1,
            current_level=2.5,
            weak_knowledge_points=["指针", "数组"],
            strong_knowledge_points=["变量", "运算符"],
            recent_accuracy=0.65
        )

        mock_response = json.dumps([
            {
                "id": "q_001",
                "type": "choice",
                "difficulty": 2,
                "content": {
                    "text": "关于指针，以下说法正确的是？",
                    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"]
                },
                "solution": {"answer": "B", "explanation": "解释"},
                "knowledge_points": ["指针"]
            }
        ])

        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response

            result = await ai_service.generate_personalized_quiz(
                chapter_title="指针基础",
                chapter_description="学习指针的概念和用法",
                user_profile=user_profile,
                question_count=5,
                question_types=["choice", "programming"],
                difficulty_range=(1, 3)
            )

            assert result is not None
            assert len(result) == 1
            assert result[0]["type"] == "choice"

    @pytest.mark.asyncio
    async def test_generate_quiz_without_user_profile(self):
        """Should generate quiz without user profile"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig

        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        ai_service.configure(config)

        mock_response = json.dumps([
            {
                "id": "q_001",
                "type": "choice",
                "difficulty": 2,
                "content": {
                    "text": "测试题目",
                    "options": ["A", "B", "C", "D"]
                },
                "solution": {"answer": "A"},
                "knowledge_points": ["测试"]
            }
        ])

        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response

            result = await ai_service.generate_personalized_quiz(
                chapter_title="测试章节",
                chapter_description="测试描述",
                user_profile=None,
                question_count=3
            )

            assert result is not None
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_generate_quiz_not_configured(self):
        """Should return empty list when AI not configured"""
        from app.services.ai import AIService

        service = AIService()

        result = await service.generate_personalized_quiz(
            chapter_title="测试",
            chapter_description="测试"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_generate_quiz_json_parse_error(self):
        """Should return empty list on JSON parse error"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig

        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        ai_service.configure(config)

        # Invalid JSON response
        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "This is not valid JSON"

            result = await ai_service.generate_personalized_quiz(
                chapter_title="测试",
                chapter_description="测试"
            )

            assert result == []


class TestGenerateQuestionAnalysis:
    """Tests for AI question analysis generation"""

    @pytest.mark.asyncio
    async def test_generate_question_analysis_for_wrong_answer(self):
        """Should generate analysis for wrong answer"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig

        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        ai_service.configure(config)

        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "你的答案错误了，因为..."

            result = await ai_service.generate_question_analysis(
                question_text="关于指针，以下说法正确的是？",
                options=["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                user_answer="A",
                correct_answer="B",
                is_correct=False
            )

            assert result is not None
            assert "analysis" in result
            assert result["is_correct"] is False

    @pytest.mark.asyncio
    async def test_generate_question_analysis_for_correct_answer(self):
        """Should generate analysis for correct answer"""
        from app.services.ai import ai_service
        from app.schemas.ai import AIProviderConfig

        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        ai_service.configure(config)

        with patch.object(ai_service._provider, 'generate_explanation', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "正确！你很好地理解了指针的概念。"

            result = await ai_service.generate_question_analysis(
                question_text="测试题目",
                options=["A", "B", "C", "D"],
                user_answer="B",
                correct_answer="B",
                is_correct=True
            )

            assert result["is_correct"] is True
