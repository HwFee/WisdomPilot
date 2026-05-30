"""
Tests for Mastery Quiz Service

TDD: Testing the mastery quiz service for knowledge content and quiz generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestMasteryQuizServiceGenerateKnowledge:
    """Tests for knowledge content generation"""

    @pytest.mark.asyncio
    async def test_get_chapter_knowledge_content_success(self):
        """Should get chapter knowledge content successfully"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()

        # Mock database and AI service
        mock_db = AsyncMock()
        mock_chapter = MagicMock()
        mock_chapter.id = 1
        mock_chapter.title = "C语言基础"
        mock_chapter.description = "学习C语言的基本概念"
        mock_chapter.order_index = 1

        mock_course = MagicMock()
        mock_course.name = "C语言程序设计"

        with patch.object(service, '_get_chapter_with_course', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (mock_chapter, mock_course)

            with patch.object(service, '_generate_or_get_knowledge', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = {
                    "knowledge_points": [
                        {
                            "id": "kp_001",
                            "title": "变量与数据类型",
                            "content": "变量是存储数据的容器...",
                            "examples": ["int x = 10;"],
                            "difficulty": 1
                        }
                    ],
                    "cached": False
                }

                result = await service.get_chapter_knowledge_content(
                    db=mock_db,
                    chapter_id=1,
                    user_id="user_001"
                )

                assert result is not None
                assert "knowledge_points" in result
                assert result["chapter_title"] == "C语言基础"

    @pytest.mark.asyncio
    async def test_get_chapter_knowledge_content_not_found(self):
        """Should return None when chapter not found"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()
        mock_db = AsyncMock()

        with patch.object(service, '_get_chapter_with_course', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (None, None)

            result = await service.get_chapter_knowledge_content(
                db=mock_db,
                chapter_id=999,
                user_id="user_001"
            )

            assert result is None


class TestMasteryQuizServiceUpdateProgress:
    """Tests for user progress update"""

    @pytest.mark.asyncio
    async def test_update_user_progress_new_mastery(self):
        """Should create new mastery record when none exists"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()
        mock_db = AsyncMock()

        # Mock no existing mastery
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        await service._update_user_progress(
            db=mock_db,
            user_id="user_001",
            chapter_id=1,
            correct_count=8,
            total_count=10
        )

        # Should add new mastery record
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_progress_existing_mastery(self):
        """Should update existing mastery record"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()
        mock_db = AsyncMock()

        # Mock existing mastery
        mock_mastery = MagicMock()
        mock_mastery.total_exercises = 10
        mock_mastery.correct_exercises = 8
        mock_mastery.mastery_score = 50
        mock_mastery.accuracy_score = 80

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mastery
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        await service._update_user_progress(
            db=mock_db,
            user_id="user_001",
            chapter_id=1,
            correct_count=9,
            total_count=10
        )

        # Should update totals
        assert mock_mastery.total_exercises == 20
        assert mock_mastery.correct_exercises == 17
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mastery_level(self):
        """Should return correct mastery level for score"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()

        assert service._get_mastery_level(95) == "精通"
        assert service._get_mastery_level(80) == "熟练"
        assert service._get_mastery_level(65) == "练习"
        assert service._get_mastery_level(45) == "学习"
        assert service._get_mastery_level(20) == "入门"


class TestMasteryQuizServiceGenerateQuiz:
    """Tests for quiz generation"""

    @pytest.mark.asyncio
    async def test_generate_quiz_with_user_profile(self):
        """Should generate quiz based on user profile"""
        from app.services.mastery_quiz import MasteryQuizService
        from app.schemas.mastery_quiz import MasteryQuizGenerateRequest

        service = MasteryQuizService()
        mock_db = AsyncMock()

        request = MasteryQuizGenerateRequest(
            course_id=1,
            chapter_id=1,
            question_count=5,
            question_types=["choice"]
        )

        # Mock chapter
        mock_chapter = MagicMock()
        mock_chapter.id = 1
        mock_chapter.title = "指针基础"
        mock_chapter.description = "学习指针的概念"

        # Mock user profile
        mock_profile = {
            "user_id": "user_001",
            "current_level": 2.5,
            "weak_knowledge_points": ["指针运算"],
            "recent_accuracy": 0.65
        }

        with patch.object(service, '_get_chapter', new_callable=AsyncMock) as mock_get_chapter:
            mock_get_chapter.return_value = mock_chapter

            with patch.object(service, '_get_user_profile', new_callable=AsyncMock) as mock_get_profile:
                mock_get_profile.return_value = mock_profile

                with patch.object(service, '_generate_quiz_questions', new_callable=AsyncMock) as mock_gen:
                    mock_gen.return_value = [
                        {
                            "id": "q_001",
                            "type": "choice",
                            "difficulty": 2,
                            "content": {"text": "测试题", "options": ["A", "B", "C", "D"]},
                            "solution": {"answer": "A"},
                            "knowledge_points": ["指针运算"]
                        }
                    ]

                    with patch.object(service, '_create_quiz_session', new_callable=AsyncMock) as mock_session:
                        mock_session.return_value = "session_001"

                        result = await service.generate_quiz(
                            db=mock_db,
                            user_id="user_001",
                            request=request
                        )

                        assert result is not None
                        assert result["success"] is True
                        assert len(result["questions"]) == 1

    @pytest.mark.asyncio
    async def test_generate_quiz_chapter_not_found(self):
        """Should return failure when chapter not found"""
        from app.services.mastery_quiz import MasteryQuizService
        from app.schemas.mastery_quiz import MasteryQuizGenerateRequest

        service = MasteryQuizService()
        mock_db = AsyncMock()

        request = MasteryQuizGenerateRequest(
            course_id=1,
            chapter_id=999
        )

        with patch.object(service, '_get_chapter', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.generate_quiz(
                db=mock_db,
                user_id="user_001",
                request=request
            )

            assert result["success"] is False
            assert "未找到章节" in result["message"]


class TestMasteryQuizServiceSubmitQuiz:
    """Tests for quiz submission"""

    @pytest.mark.asyncio
    async def test_submit_quiz_success(self):
        """Should submit quiz and return results"""
        from app.services.mastery_quiz import MasteryQuizService
        from app.schemas.mastery_quiz import MasteryQuizSubmitRequest, QuizAnswer

        service = MasteryQuizService()
        mock_db = AsyncMock()

        request = MasteryQuizSubmitRequest(
            session_id="session_001",
            answers=[
                QuizAnswer(question_id="q_001", answer="A", time_spent=30),
                QuizAnswer(question_id="q_002", answer="B", time_spent=45)
            ],
            total_time=75
        )

        # Mock session
        mock_session = MagicMock()
        mock_session.id = "session_001"
        mock_session.user_id = "user_001"
        mock_session.chapter_id = 1
        mock_session.questions = [
            {"id": "q_001", "solution": {"answer": "A"}, "knowledge_points": ["变量"]},
            {"id": "q_002", "solution": {"answer": "B"}, "knowledge_points": ["指针"]}
        ]

        with patch.object(service, '_get_quiz_session', new_callable=AsyncMock) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch.object(service, '_evaluate_answers', new_callable=AsyncMock) as mock_eval:
                mock_eval.return_value = {
                    "correct_count": 2,
                    "total_count": 2,
                    "results": [
                        {"question_id": "q_001", "is_correct": True},
                        {"question_id": "q_002", "is_correct": True}
                    ]
                }

                with patch.object(service, '_update_user_progress', new_callable=AsyncMock) as mock_update:
                    mock_update.return_value = None

                    result = await service.submit_quiz(
                        db=mock_db,
                        user_id="user_001",
                        request=request
                    )

                    assert result is not None
                    assert result["accuracy"] == 1.0
                    assert result["correct_answers"] == 2

    @pytest.mark.asyncio
    async def test_submit_quiz_session_not_found(self):
        """Should return failure when session not found"""
        from app.services.mastery_quiz import MasteryQuizService
        from app.schemas.mastery_quiz import MasteryQuizSubmitRequest

        service = MasteryQuizService()
        mock_db = AsyncMock()

        request = MasteryQuizSubmitRequest(
            session_id="invalid_session",
            answers=[]
        )

        with patch.object(service, '_get_quiz_session', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.submit_quiz(
                db=mock_db,
                user_id="user_001",
                request=request
            )

            assert result["success"] is False
            assert "会话不存在" in result.get("message", "")


class TestMasteryQuizServiceUserProfile:
    """Tests for user profile retrieval"""

    @pytest.mark.asyncio
    async def test_get_user_profile_with_data(self):
        """Should get user profile with existing data"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()
        mock_db = AsyncMock()

        # Mock mastery data
        mock_masteries = [
            MagicMock(
                user_id="user_001",
                course_id=1,
                mastery_score=85,
                objectives_status=["变量", "运算符"],
                total_exercises=10,
                correct_exercises=8
            ),
            MagicMock(
                user_id="user_001",
                course_id=1,
                mastery_score=45,
                objectives_status=["指针", "数组"],
                total_exercises=5,
                correct_exercises=2
            )
        ]

        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_masteries

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._get_user_profile(
            db=mock_db,
            user_id="user_001",
            course_id=1
        )

        assert result is not None
        assert result["current_level"] > 0
        # Weak points should include objectives from chapters with low mastery
        assert "指针" in result["weak_knowledge_points"]

    @pytest.mark.asyncio
    async def test_get_user_profile_no_data(self):
        """Should return None when no data"""
        from app.services.mastery_quiz import MasteryQuizService

        service = MasteryQuizService()
        mock_db = AsyncMock()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._get_user_profile(
            db=mock_db,
            user_id="new_user",
            course_id=1
        )

        assert result is None
