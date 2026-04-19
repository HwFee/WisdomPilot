"""Tests for AI module endpoints (choice-explanation, code-review, config)"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.ai import OllamaProvider, LMStudioProvider, MiniMaxProvider, OpenAIProvider, AIService, ai_service
from app.schemas.ai import AIProviderConfig


@pytest.fixture(autouse=True)
def configure_ai_service():
    """Configure AI service with test settings for all AI tests"""
    config = AIProviderConfig(
        provider="openai",
        api_key="test-key",
        model="gpt-4o-mini",
        temperature=0.7,
    )
    ai_service.configure(config)
    yield


class TestOllamaProvider:
    """Test OllamaProvider calls local LLM endpoint"""

    @pytest.mark.asyncio
    async def test_ollama_provider_generate_explanation(self):
        """OllamaProvider calls local endpoint for explanation"""
        config = AIProviderConfig(
            provider="ollama",
            api_key="test-key",
            model="local-model",
            temperature=0.7,
            local_base_url="http://localhost:8080",
        )
        provider = OllamaProvider(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "这是一段AI解释"}}]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai.httpx.AsyncClient", return_value=mock_client):
            result = await provider.generate_explanation("测试问题")

        assert "这是一段AI解释" in result
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert "localhost:8080/v1/chat/completions" in call_kwargs.kwargs.get("url", call_kwargs[0][0])

    @pytest.mark.asyncio
    async def test_ollama_provider_review_code(self):
        """OllamaProvider calls local endpoint for code review"""
        config = AIProviderConfig(
            provider="ollama",
            api_key="test-key",
            model="local-model",
            temperature=0.5,
            local_base_url="http://localhost:8080",
        )
        provider = OllamaProvider(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "代码审查结果：结构良好"}}]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai.httpx.AsyncClient", return_value=mock_client):
            result = await provider.review_code("print('hello')", "python")

        assert "代码审查结果" in result
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_ollama_provider_without_base_url(self):
        """OllamaProvider uses default local URL when local_base_url not set"""
        config = AIProviderConfig(
            provider="ollama",
            api_key="test-key",
            model="local-model",
            temperature=0.7,
        )
        provider = OllamaProvider(config)
        # Default should point to Ollama default port
        assert provider.base_url == "http://localhost:11434"


class TestAIServiceLocalProvider:
    """Test AIService switching to OllamaProvider"""

    def test_ai_service_configure_ollama_provider(self):
        """AIService creates OllamaProvider when provider is 'ollama'"""
        service = AIService()
        config = AIProviderConfig(
            provider="ollama",
            api_key="test-key",
            model="ollama-model",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert isinstance(service._provider, OllamaProvider)

    def test_ai_service_configure_local_fallback(self):
        """AIService creates OllamaProvider when provider is 'local' (backwards compat)"""
        service = AIService()
        config = AIProviderConfig(
            provider="local",
            api_key="test-key",
            model="ollama-model",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert isinstance(service._provider, OllamaProvider)

    def test_ai_service_configure_lmstudio_provider(self):
        """AIService creates LMStudioProvider when provider is 'lmstudio'"""
        service = AIService()
        config = AIProviderConfig(
            provider="lmstudio",
            api_key="test-key",
            model="lmstudio-model",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert isinstance(service._provider, LMStudioProvider)

    def test_ai_service_configure_openai_provider(self):
        """AIService creates OpenAIProvider when provider is 'openai'"""
        service = AIService()
        config = AIProviderConfig(
            provider="openai",
            api_key="sk-test",
            model="gpt-4o-mini",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert isinstance(service._provider, OpenAIProvider)


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


class TestMiniMaxProvider:
    """Test MiniMaxProvider handles Anthropic format correctly"""

    @pytest.mark.asyncio
    async def test_minimax_provider_generate_explanation(self):
        """MiniMaxProvider calls Anthropic-format endpoint"""
        config = AIProviderConfig(
            provider="minimax",
            api_key="test-key",
            model="MiniMax-M2.7",
            temperature=0.7,
            base_url="https://api.minimaxi.com/anthropic",
        )
        provider = MiniMaxProvider(config)

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "content": [
                {"type": "thinking", "thinking": "thought process", "signature": "abc"},
                {"type": "text", "text": "AI explanation result"},
            ]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai.httpx.AsyncClient", return_value=mock_client):
            result = await provider.generate_explanation("test question")

        assert "AI explanation result" == result
        call_kwargs = mock_client.post.call_args
        assert "/v1/messages" in call_kwargs.kwargs.get("url", call_kwargs[0][0])
        assert "x-api-key" in call_kwargs.kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_minimax_provider_default_url(self):
        """MiniMaxProvider uses default Anthropic-compatible URL"""
        config = AIProviderConfig(
            provider="minimax",
            api_key="test-key",
            model="MiniMax-M2.7",
            temperature=0.7,
        )
        provider = MiniMaxProvider(config)
        assert provider.base_url == "https://api.minimaxi.com/anthropic"


class TestAIServiceMiniMaxConfig:
    """Test AIService MiniMax configuration"""

    def test_configure_minimax_provider(self):
        """AIService can configure MiniMax provider independently"""
        service = AIService()
        # Configure main provider first
        config = AIProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4o-mini",
            temperature=0.7,
        )
        service.configure(config)
        assert service.is_configured()
        assert not service.is_minimax_configured()

        # Configure MiniMax
        service.configure_minimax(api_key="minimax-test-key")
        assert service.is_minimax_configured()
        assert isinstance(service.minimax_provider, MiniMaxProvider)

    def test_configure_minimax_empty_key_disables(self):
        """Empty API key disables MiniMax provider"""
        service = AIService()
        service.configure_minimax(api_key="")
        assert not service.is_minimax_configured()
        assert service.minimax_provider is None

    def test_configure_minimax_custom_model(self):
        """Can configure MiniMax with custom model"""
        service = AIService()
        service.configure_minimax(
            api_key="test-key",
            model="MiniMax-M2.7-Pro",
            temperature=0.5,
        )
        assert service.is_minimax_configured()
        assert service.minimax_provider.config.model == "MiniMax-M2.7-Pro"
        assert service.minimax_provider.config.temperature == 0.5


class TestEnhancedQuizGeneration:
    """Test enhanced quiz generation with MiniMax"""

    @pytest.mark.asyncio
    async def test_generate_enhanced_quiz_uses_minimax(self):
        """Enhanced quiz generation uses MiniMax when configured"""
        from app.services.section_base_question import SectionBaseQuestionService
        from app.models.chapter import Chapter

        # Create mock chapter
        chapter = Chapter(
            id=1,
            course_id=1,
            title="变量与数据类型",
            description="学习C语言中的变量和数据类型",
            order_index=1,
        )

        # Create service instance
        service = SectionBaseQuestionService()

        # Mock MiniMax response with valid JSON
        mock_response = '''```json
[
  {
    "id": "eq_001",
    "type": "choice",
    "difficulty": 2,
    "text": "以下哪个是合法的变量名？",
    "options": ["1var", "var_name", "var-name", "var name"],
    "correct_answer": "B",
    "explanation": "变量名可以包含字母、数字和下划线，但不能以数字开头",
    "knowledge_points": ["变量命名规则"]
  }
]
```'''

        # Mock the internal provider instance
        mock_provider = AsyncMock()
        mock_provider.generate_explanation = AsyncMock(return_value=mock_response)

        with patch.object(ai_service, 'is_minimax_configured', return_value=True):
            with patch.object(ai_service, '_minimax_provider', mock_provider):
                result = await service._generate_enhanced_questions_with_ai(
                    chapter=chapter,
                    weak_points=["变量命名规则"],
                    question_count=1,
                    question_types=["choice"],
                )

        assert len(result) == 1
        assert result[0].type == "choice"
        assert result[0].text == "以下哪个是合法的变量名？"
        assert result[0].options == ["1var", "var_name", "var-name", "var name"]

    @pytest.mark.asyncio
    async def test_generate_enhanced_quiz_fallback_to_main_provider(self):
        """Enhanced quiz generation falls back to main provider when MiniMax not configured"""
        from app.services.section_base_question import SectionBaseQuestionService
        from app.models.chapter import Chapter

        chapter = Chapter(
            id=1,
            course_id=1,
            title="变量与数据类型",
            description="学习C语言中的变量和数据类型",
            order_index=1,
        )

        service = SectionBaseQuestionService()

        mock_response = '''[
          {
            "id": "eq_001",
            "type": "choice",
            "difficulty": 2,
            "text": "测试题目",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "解释",
            "knowledge_points": ["知识点"]
          }
        ]'''

        mock_provider = AsyncMock()
        mock_provider.generate_explanation = AsyncMock(return_value=mock_response)

        with patch.object(ai_service, 'is_minimax_configured', return_value=False):
            with patch.object(ai_service, 'is_configured', return_value=True):
                with patch.object(ai_service, '_provider', mock_provider):
                    result = await service._generate_enhanced_questions_with_ai(
                        chapter=chapter,
                        weak_points=[],
                        question_count=1,
                        question_types=["choice"],
                    )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_generate_enhanced_quiz_no_provider(self):
        """Enhanced quiz generation returns empty when no provider configured"""
        from app.services.section_base_question import SectionBaseQuestionService
        from app.models.chapter import Chapter

        chapter = Chapter(
            id=1,
            course_id=1,
            title="变量与数据类型",
            description="学习C语言中的变量和数据类型",
            order_index=1,
        )

        service = SectionBaseQuestionService()

        with patch.object(ai_service, 'is_minimax_configured', return_value=False):
            with patch.object(ai_service, 'is_configured', return_value=False):
                result = await service._generate_enhanced_questions_with_ai(
                    chapter=chapter,
                    weak_points=[],
                    question_count=1,
                    question_types=["choice"],
                )

        assert result == []


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
