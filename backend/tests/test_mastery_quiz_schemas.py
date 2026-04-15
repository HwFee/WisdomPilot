"""
Tests for Mastery Quiz Schemas

TDD: Testing the new mastery quiz schemas for the refactored learning path system.
"""

import pytest
from pydantic import ValidationError


class TestKnowledgePointSchema:
    """Tests for KnowledgePoint schema"""

    def test_create_knowledge_point_with_all_fields(self):
        """Should create a valid knowledge point with all fields"""
        from app.schemas.mastery_quiz import KnowledgePoint

        kp = KnowledgePoint(
            id="kp_001",
            title="变量与数据类型",
            content="变量是存储数据的容器...",
            examples=["int x = 10;", "float y = 3.14;"],
            difficulty=1,
            related_points=["kp_002", "kp_003"]
        )

        assert kp.id == "kp_001"
        assert kp.title == "变量与数据类型"
        assert kp.content == "变量是存储数据的容器..."
        assert len(kp.examples) == 2
        assert kp.difficulty == 1
        assert len(kp.related_points) == 2

    def test_create_knowledge_point_with_minimal_fields(self):
        """Should create knowledge point with only required fields"""
        from app.schemas.mastery_quiz import KnowledgePoint

        kp = KnowledgePoint(
            id="kp_002",
            title="条件语句",
            content="if-else 语句用于条件判断"
        )

        assert kp.id == "kp_002"
        assert kp.title == "条件语句"
        assert kp.examples is None
        assert kp.related_points is None


class TestMasteryQuizQuestionSchema:
    """Tests for MasteryQuizQuestion schema"""

    def test_create_choice_question(self):
        """Should create a valid choice question"""
        from app.schemas.mastery_quiz import MasteryQuizQuestion

        question = MasteryQuizQuestion(
            id="q_001",
            type="choice",
            difficulty=2,
            content={
                "text": "以下哪个是正确的变量声明？",
                "options": [
                    "A. int 1x = 10;",
                    "B. int x = 10;",
                    "C. int x =;",
                    "D. 10 = x;"
                ]
            },
            solution={"answer": "B", "explanation": "变量名不能以数字开头"},
            knowledge_points=["变量命名规则"],
            hints=["变量名必须以字母或下划线开头"]
        )

        assert question.id == "q_001"
        assert question.type == "choice"
        assert question.difficulty == 2
        assert len(question.content["options"]) == 4

    def test_create_programming_question(self):
        """Should create a valid programming question"""
        from app.schemas.mastery_quiz import MasteryQuizQuestion

        question = MasteryQuizQuestion(
            id="q_002",
            type="programming",
            difficulty=3,
            content={
                "title": "计算两数之和",
                "description": "编写一个函数，计算两个整数的和",
                "code_template": "int add(int a, int b) {\n    // 你的代码\n}",
                "input_format": "两个整数 a 和 b",
                "output_format": "两数之和",
                "sample_input": "3 5",
                "sample_output": "8"
            },
            solution={"answer": "return a + b;", "explanation": "直接返回两数之和"},
            knowledge_points=["函数定义", "返回值"],
            test_cases=[
                {"input": "1 2", "output": "3"},
                {"input": "10 20", "output": "30"}
            ]
        )

        assert question.id == "q_002"
        assert question.type == "programming"
        assert question.test_cases is not None
        assert len(question.test_cases) == 2

    def test_create_fill_blank_question(self):
        """Should create a valid fill-in-the-blank question"""
        from app.schemas.mastery_quiz import MasteryQuizQuestion

        question = MasteryQuizQuestion(
            id="q_003",
            type="fill_blank",
            difficulty=2,
            content={
                "text": "在C语言中，使用 ___ 关键字定义整型变量。",
                "blanks": ["int"]
            },
            solution={"answer": ["int"], "explanation": "int 是整型变量的关键字"},
            knowledge_points=["数据类型", "变量定义"]
        )

        assert question.id == "q_003"
        assert question.type == "fill_blank"
        assert len(question.content["blanks"]) == 1


class TestMasteryQuizGenerateRequest:
    """Tests for MasteryQuizGenerateRequest schema"""

    def test_create_request_with_required_fields(self):
        """Should create request with required fields only"""
        from app.schemas.mastery_quiz import MasteryQuizGenerateRequest

        request = MasteryQuizGenerateRequest(
            course_id=1,
            chapter_id=1
        )

        assert request.course_id == 1
        assert request.chapter_id == 1
        assert request.question_count == 5  # default
        assert request.question_types == ["choice", "programming"]  # default

    def test_create_request_with_all_fields(self):
        """Should create request with all fields"""
        from app.schemas.mastery_quiz import MasteryQuizGenerateRequest

        request = MasteryQuizGenerateRequest(
            course_id=1,
            chapter_id=1,
            question_count=10,
            question_types=["choice", "fill_blank"],
            difficulty_range=(1, 3),
            focus_weak_points=True,
            custom_instructions="重点考查循环结构"
        )

        assert request.question_count == 10
        assert "fill_blank" in request.question_types
        assert request.difficulty_range == (1, 3)
        assert request.focus_weak_points is True

    def test_invalid_question_count(self):
        """Should reject invalid question count"""
        from app.schemas.mastery_quiz import MasteryQuizGenerateRequest

        with pytest.raises(ValidationError):
            MasteryQuizGenerateRequest(
                course_id=1,
                chapter_id=1,
                question_count=0  # Must be >= 1
            )

        with pytest.raises(ValidationError):
            MasteryQuizGenerateRequest(
                course_id=1,
                chapter_id=1,
                question_count=25  # Must be <= 20
            )


class TestMasteryQuizGenerateResponse:
    """Tests for MasteryQuizGenerateResponse schema"""

    def test_create_successful_response(self):
        """Should create a successful response"""
        from app.schemas.mastery_quiz import (
            MasteryQuizGenerateResponse,
            MasteryQuizQuestion
        )

        question = MasteryQuizQuestion(
            id="q_001",
            type="choice",
            difficulty=2,
            content={"text": "问题", "options": ["A", "B", "C", "D"]},
            solution={"answer": "A"},
            knowledge_points=["测试"]
        )

        response = MasteryQuizGenerateResponse(
            success=True,
            session_id="session_001",
            questions=[question],
            user_profile_used=True,
            weak_points_addressed=["变量定义"],
            message="成功生成 1 道测试题"
        )

        assert response.success is True
        assert response.session_id == "session_001"
        assert len(response.questions) == 1
        assert response.user_profile_used is True

    def test_create_failed_response(self):
        """Should create a failed response"""
        from app.schemas.mastery_quiz import MasteryQuizGenerateResponse

        response = MasteryQuizGenerateResponse(
            success=False,
            session_id="",
            questions=[],
            user_profile_used=False,
            weak_points_addressed=[],
            message="AI 服务未配置"
        )

        assert response.success is False
        assert len(response.questions) == 0


class TestMasteryQuizSubmitRequest:
    """Tests for MasteryQuizSubmitRequest schema"""

    def test_create_submit_request(self):
        """Should create a valid submit request"""
        from app.schemas.mastery_quiz import MasteryQuizSubmitRequest

        request = MasteryQuizSubmitRequest(
            session_id="session_001",
            answers=[
                {"question_id": "q_001", "answer": "B", "time_spent": 30},
                {"question_id": "q_002", "answer": "return a + b;", "time_spent": 120}
            ]
        )

        assert request.session_id == "session_001"
        assert len(request.answers) == 2
        assert request.answers[0].question_id == "q_001"


class TestMasteryQuizSubmitResponse:
    """Tests for MasteryQuizSubmitResponse schema"""

    def test_create_submit_response(self):
        """Should create a valid submit response"""
        from app.schemas.mastery_quiz import MasteryQuizSubmitResponse

        response = MasteryQuizSubmitResponse(
            session_id="session_001",
            total_questions=5,
            correct_answers=4,
            accuracy=0.8,
            xp_earned=50,
            mastery_points_earned=10,
            results=[
                {"question_id": "q_001", "is_correct": True, "user_answer": "B"},
                {"question_id": "q_002", "is_correct": False, "user_answer": "A"}
            ],
            recommendations=[
                "建议复习变量命名规则",
                "继续练习条件语句"
            ],
            passed=True
        )

        assert response.session_id == "session_001"
        assert response.accuracy == 0.8
        assert response.passed is True
        assert len(response.recommendations) == 2


class TestKnowledgeContentResponse:
    """Tests for KnowledgeContentResponse schema"""

    def test_create_knowledge_content_response(self):
        """Should create a valid knowledge content response"""
        from app.schemas.mastery_quiz import (
            KnowledgeContentResponse,
            KnowledgePoint
        )

        kp = KnowledgePoint(
            id="kp_001",
            title="变量与数据类型",
            content="变量是存储数据的容器..."
        )

        response = KnowledgeContentResponse(
            chapter_id=1,
            chapter_title="第一章：C语言基础",
            knowledge_points=[kp],
            total_points=1,
            estimated_time=15,
            prerequisites=["无"],
            next_chapters=["第二章：运算符"]
        )

        assert response.chapter_id == 1
        assert response.chapter_title == "第一章：C语言基础"
        assert len(response.knowledge_points) == 1
        assert response.estimated_time == 15
