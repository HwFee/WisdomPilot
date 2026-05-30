"""Tests for AI module endpoints (choice-explanation, code-review, config)"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.ai import OpenAIProvider as DeepSeekProvider, AIService, ai_service
from app.schemas.ai import AIProviderConfig


@pytest.fixture(autouse=True)
def configure_ai_service():
    """Configure AI service with test settings for all AI tests"""
    config = AIProviderConfig(
        provider="deepseek",
        api_key="test-key",
        model="deepseek-v4-flash",
        temperature=0.7,
    )
    ai_service.configure(config)
    yield



class TestAIServiceConfigure:
    """Test AIService provider configuration"""

    def test_ai_service_configure_deepseek_provider(self):
        """AIService creates DeepSeekProvider when provider is 'deepseek'"""
        service = AIService()
        config = AIProviderConfig(
            provider="deepseek",
            api_key="sk-test",
            model="deepseek-v4-flash",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert isinstance(service._provider, DeepSeekProvider)

class TestChoiceExplanation:
    """Test AI choice explanation endpoint"""

    @pytest.mark.asyncio
    async def test_choice_explanation_success(self, client, auth_headers):
        """Authenticated user gets AI explanation for wrong answer"""
        payload = {
            "chapter_id": 1,
            "subsection_index": 0,
            "exercise_id": 1,
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "user_selected_index": 0,
            "correct_index": 1,
        }
        with patch("app.routers.ai.ai_service.generate_choice_explanation",
                   new=AsyncMock(return_value="2+2 等于 4")):
            response = await client.post(
                "/api/ai/choice-explanation", json=payload, headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0

    @pytest.mark.asyncio
    async def test_choice_explanation_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        payload = {
            "chapter_id": 1,
            "subsection_index": 0,
            "exercise_id": 1,
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "user_selected_index": 0,
            "correct_index": 1,
        }
        response = await client.post(
            "/api/ai/choice-explanation", json=payload
        )
        assert response.status_code in (401, 403)


class TestCodeReview:
    """Test AI code review endpoint"""

    @pytest.mark.asyncio
    async def test_code_review_success(self, client, auth_headers):
        """User gets AI review for submitted code"""
        payload = {
            "code": "print('hello')",
            "language": "python",
            "chapter_id": 1,
            "subsection_index": 0,
        }
        with patch("app.routers.ai.ai_service.generate_code_review",
                   new=AsyncMock(return_value="代码整体结构不错。建议添加错误处理。")):
            response = await client.post(
                "/api/ai/code-review", json=payload, headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "review" in data

    @pytest.mark.asyncio
    async def test_code_review_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        payload = {
            "code": "print('hello')",
            "language": "python",
        }
        response = await client.post(
            "/api/ai/code-review", json=payload
        )
        assert response.status_code in (401, 403)


class TestAIChat:
    """Test AI chat endpoint"""

    @pytest.mark.asyncio
    async def test_chat_success(self, client, auth_headers):
        """Authenticated user gets AI reply"""
        payload = {"message": "Python 列表推导式是什么？"}
        with patch("app.routers.ai.ai_service.generate_chat",
                   new=AsyncMock(return_value="列表推导式是 Python 的一种简洁创建列表的方式。")):
            response = await client.post(
                "/api/ai/chat", json=payload, headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    @pytest.mark.asyncio
    async def test_chat_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        payload = {"message": "hello"}
        response = await client.post("/api/ai/chat", json=payload)
        assert response.status_code in (401, 403)


class TestAIConfig:
    """Test AI config management endpoint"""

    @pytest.mark.asyncio
    async def test_ai_config_get(self, client, admin_auth_headers):
        """Get current AI configuration"""
        response = await client.get(
            "/api/admin/ai/config", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "model" in data
        assert "temperature" in data
        assert "is_configured" in data

    @pytest.mark.asyncio
    async def test_ai_config_update(self, client, admin_auth_headers):
        """Update AI configuration"""
        response = await client.put(
            "/api/admin/ai/config",
            json={"model": "gpt-4o", "temperature": 0.5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ai_config_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        response = await client.get("/api/admin/ai/config")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_ai_config_non_admin_forbidden(self, client, auth_headers):
        """Non-admin user gets 403"""
        response = await client.get("/api/admin/ai/config", headers=auth_headers)
        assert response.status_code == 403


class TestChoiceAnalysis:
    """Test AI choice analysis endpoint (refactored from choice-explanation)"""

    @pytest.mark.asyncio
    async def test_choice_analysis_success(self, client, auth_headers):
        """Authenticated user gets AI analysis for wrong answer"""
        payload = {
            "question_text": "哪个是合法变量名?",
            "options": ["1abc", "a_b", "a b", "a-b"],
            "user_selected": 0,
            "correct_answer": 1,
            "chapter_id": 1,
            "exercise_id": "q1",
        }
        with patch("app.routers.ai.ai_service.generate_choice_analysis",
                   new=AsyncMock(return_value={"analysis": "a_b is legal because...", "is_correct": False})):
            response = await client.post(
                "/api/ai/choice-analysis", json=payload, headers=auth_headers
            )
        if response.status_code != 200:
            print(f"Error: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "is_correct" in data
        assert data["is_correct"] is False

    @pytest.mark.asyncio
    async def test_choice_analysis_correct_answer(self, client, auth_headers, capsys):
        """When user picks correct answer, is_correct is True"""
        payload = {
            "question_text": "Which is a valid variable name?",
            "options": ["1abc", "a_b", "a b", "a-b"],
            "user_selected": 1,
            "correct_answer": 1,
            "chapter_id": 1,
            "exercise_id": "q1",
        }
        with patch("app.routers.ai.ai_service.generate_choice_analysis",
                   new=AsyncMock(return_value={"analysis": "Correct!", "is_correct": True})):
            response = await client.post(
                "/api/ai/choice-analysis", json=payload, headers=auth_headers
            )
        if response.status_code != 200:
            print(f"Error detail: {response.json()}", flush=True)
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True

    @pytest.mark.asyncio
    async def test_choice_analysis_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        payload = {
            "question_text": "test",
            "options": ["a", "b"],
            "user_selected": 0,
            "correct_answer": 1,
            "chapter_id": 1,
            "exercise_id": "q1",
        }
        response = await client.post("/api/ai/choice-analysis", json=payload)
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_choice_analysis_requires_question(self, client, auth_headers):
        """Missing question_text returns 422"""
        payload = {
            "options": ["a", "b"],
            "user_selected": 0,
            "correct_answer": 1,
            "chapter_id": 1,
            "exercise_id": "q1",
        }
        response = await client.post("/api/ai/choice-analysis", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestCodeFeedback:
    """Test AI code feedback endpoint (refactored from code-review)"""

    @pytest.mark.asyncio
    async def test_code_feedback_success(self, client, auth_headers):
        """User gets AI feedback (diagnosis + suggestions + optimized code)"""
        payload = {
            "code": "print(\"hello)",
            "language": "python",
            "exercise_description": "输出 Hello World",
            "expected_output": "Hello World",
            "actual_output": "",
            "status": "SyntaxError",
            "error_message": "EOL while scanning string literal",
            "chapter_id": 1,
            "exercise_id": "ex1",
        }
        with patch("app.routers.ai.ai_service.generate_code_feedback",
                   new=AsyncMock(return_value={
                       "diagnosis": "字符串未闭合",
                       "suggestions": "检查引号",
                       "optimized_code": "print(\"hello\")",
                   })):
            response = await client.post(
                "/api/ai/code-feedback", json=payload, headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "diagnosis" in data
        assert "suggestions" in data
        assert "optimized_code" in data

    @pytest.mark.asyncio
    async def test_code_feedback_minimal_fields(self, client, auth_headers):
        """Code feedback works with minimal fields"""
        payload = {
            "code": "x = 1",
            "language": "python",
            "exercise_description": "Assign 1 to x",
            "expected_output": "1",
            "actual_output": "1",
            "status": "Accepted",
            "chapter_id": 1,
            "exercise_id": "ex2",
        }
        with patch("app.routers.ai.ai_service.generate_code_feedback",
                   new=AsyncMock(return_value={
                       "diagnosis": "代码正确",
                       "suggestions": "保持良好风格",
                       "optimized_code": "x = 1  # 清晰",
                   })):
            response = await client.post(
                "/api/ai/code-feedback", json=payload, headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert "diagnosis" in data

    @pytest.mark.asyncio
    async def test_code_feedback_unauthenticated(self, client):
        """Unauthenticated user gets 401"""
        payload = {
            "code": "x = 1",
            "language": "python",
            "exercise_description": "test",
            "expected_output": "1",
            "actual_output": "1",
            "status": "Accepted",
            "chapter_id": 1,
            "exercise_id": "ex2",
        }
        response = await client.post("/api/ai/code-feedback", json=payload)
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_code_feedback_requires_code(self, client, auth_headers):
        """Missing code returns 422"""
        payload = {
            "language": "python",
            "exercise_description": "test",
            "expected_output": "1",
            "actual_output": "1",
            "status": "Accepted",
            "chapter_id": 1,
            "exercise_id": "ex2",
        }
        response = await client.post("/api/ai/code-feedback", json=payload, headers=auth_headers)
        assert response.status_code == 422
