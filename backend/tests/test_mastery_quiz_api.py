"""
Tests for Mastery Quiz API Endpoints

TDD: Testing the mastery quiz API endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestKnowledgeContentEndpoint:
    """Tests for GET /api/learning-path/mastery/{course_id}/chapter/{chapter_id}/knowledge"""

    @pytest.mark.asyncio
    async def test_get_knowledge_content_success(self, client: AsyncClient, auth_headers: dict):
        """Should return knowledge content successfully"""
        mock_response = {
            "chapter_id": 1,
            "chapter_title": "C语言基础",
            "knowledge_points": [
                {
                    "id": "kp_001",
                    "title": "变量与数据类型",
                    "content": "变量是存储数据的容器...",
                    "examples": ["int x = 10;"],
                    "difficulty": 1,
                    "related_points": None
                }
            ],
            "total_points": 1,
            "estimated_time": 15,
            "prerequisites": None,
            "next_chapters": None
        }

        with patch('app.services.mastery_quiz.mastery_quiz_service.get_chapter_knowledge_content', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            response = await client.get(
                "/api/learning-path/mastery/1/chapter/1/knowledge",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["chapter_id"] == 1
            assert len(data["knowledge_points"]) == 1

    @pytest.mark.asyncio
    async def test_get_knowledge_content_not_found(self, client: AsyncClient, auth_headers: dict):
        """Should return 404 when chapter not found"""
        with patch('app.services.mastery_quiz.mastery_quiz_service.get_chapter_knowledge_content', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = await client.get(
                "/api/learning-path/mastery/1/chapter/999/knowledge",
                headers=auth_headers
            )

            assert response.status_code == 404


class TestGenerateQuizEndpoint:
    """Tests for POST /api/learning-path/mastery/{course_id}/generate-quiz"""

    @pytest.mark.asyncio
    async def test_generate_quiz_success(self, client: AsyncClient, auth_headers: dict):
        """Should generate quiz successfully"""
        mock_response = {
            "success": True,
            "session_id": "test-session-123",
            "questions": [
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
            ],
            "user_profile_used": True,
            "weak_points_addressed": ["指针"],
            "message": "成功生成 1 道测试题"
        }

        with patch('app.services.mastery_quiz.mastery_quiz_service.generate_quiz', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response

            response = await client.post(
                "/api/learning-path/mastery/1/generate-quiz",
                headers=auth_headers,
                json={
                    "course_id": 1,
                    "chapter_id": 1,
                    "question_count": 5,
                    "question_types": ["choice"]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["questions"]) == 1


class TestSubmitQuizEndpoint:
    """Tests for POST /api/learning-path/mastery/{course_id}/submit-quiz"""

    @pytest.mark.asyncio
    async def test_submit_quiz_success(self, client: AsyncClient, auth_headers: dict):
        """Should submit quiz and return results"""
        mock_response = {
            "success": True,
            "session_id": "test-session-123",
            "total_questions": 2,
            "correct_answers": 2,
            "accuracy": 1.0,
            "xp_earned": 50,
            "mastery_points_earned": 20,
            "results": [
                {"question_id": "q_001", "is_correct": True, "user_answer": "A"},
                {"question_id": "q_002", "is_correct": True, "user_answer": "B"}
            ],
            "recommendations": ["表现优秀！"],
            "passed": True,
            "message": "提交成功，恭喜通过！"
        }

        with patch('app.services.mastery_quiz.mastery_quiz_service.submit_quiz', new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = mock_response

            response = await client.post(
                "/api/learning-path/mastery/1/submit-quiz",
                headers=auth_headers,
                json={
                    "session_id": "test-session-123",
                    "answers": [
                        {"question_id": "q_001", "answer": "A", "time_spent": 30},
                        {"question_id": "q_002", "answer": "B", "time_spent": 45}
                    ],
                    "total_time": 75
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["accuracy"] == 1.0

    @pytest.mark.asyncio
    async def test_submit_quiz_session_not_found(self, client: AsyncClient, auth_headers: dict):
        """Should return error when session not found"""
        mock_response = {
            "success": False,
            "session_id": "invalid-session",
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy": 0,
            "xp_earned": 0,
            "mastery_points_earned": 0,
            "results": [],
            "recommendations": [],
            "passed": False,
            "message": "会话不存在或已过期"
        }

        with patch('app.services.mastery_quiz.mastery_quiz_service.submit_quiz', new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = mock_response

            response = await client.post(
                "/api/learning-path/mastery/1/submit-quiz",
                headers=auth_headers,
                json={
                    "session_id": "invalid-session",
                    "answers": []
                }
            )

            # Even if service returns failure, API returns 200 with success=False
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


class TestUnauthenticatedAccess:
    """Tests for unauthenticated access"""

    @pytest.mark.asyncio
    async def test_knowledge_content_requires_auth(self, client: AsyncClient):
        """Should return 401 when not authenticated"""
        response = await client.get(
            "/api/learning-path/mastery/1/chapter/1/knowledge"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_quiz_requires_auth(self, client: AsyncClient):
        """Should return 401 when not authenticated"""
        response = await client.post(
            "/api/learning-path/mastery/1/generate-quiz",
            json={"chapter_id": 1}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_quiz_requires_auth(self, client: AsyncClient):
        """Should return 401 when not authenticated"""
        response = await client.post(
            "/api/learning-path/mastery/1/submit-quiz",
            json={"session_id": "test", "answers": []}
        )
        assert response.status_code == 401
