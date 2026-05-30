"""
Tests for FPS import script
"""

import pytest
from pathlib import Path
from app.scripts.import_fps import (
    parse_fps_xml,
    estimate_difficulty,
    detect_course,
    extract_knowledge_points,
    convert_to_exercise,
)


# Sample problem data for testing
SAMPLE_PROBLEM = {
    "title": "A+B Problem",
    "time_limit": 1,
    "memory_limit": 128,
    "description": "输入两个整数，输出它们的和。",
    "input_spec": "两个整数a和b",
    "output_spec": "一个整数",
    "sample_input": "1 2",
    "sample_output": "3",
    "hint": "这是一道入门题",
    "source": "入门题",
    "test_cases": [{"input": "1 2", "output": "3", "name": "sample"}],
}


class TestFPSParser:
    """Tests for FPS XML parsing"""

    def test_parse_sample_file(self):
        """Test parsing sample problems file"""
        sample_path = Path(__file__).parent.parent / "data" / "sample_problems.xml"
        if not sample_path.exists():
            pytest.skip("Sample file not found")

        problems = parse_fps_xml(sample_path)

        assert len(problems) == 6
        assert problems[0]["title"] == "A+B Problem"
        assert problems[0]["time_limit"] == 1
        assert problems[0]["memory_limit"] == 128

    def test_parse_handles_missing_fields(self):
        """Test parsing handles missing optional fields gracefully"""
        # Create minimal problem
        problems = parse_fps_xml(Path(__file__).parent / "fixtures" / "minimal.xml")
        # Should not raise error even with missing fields


class TestDifficultyEstimation:
    """Tests for difficulty estimation"""

    def test_beginner_problem(self):
        """Test beginner level detection"""
        problem = {"title": "A+B Problem 入门题", "description": "简单基础题"}
        assert estimate_difficulty(problem) == 1

    def test_intermediate_problem(self):
        """Test intermediate level detection"""
        problem = {"title": "中等难度问题", "description": "中等级别"}
        assert estimate_difficulty(problem) == 3

    def test_expert_problem(self):
        """Test expert level detection"""
        problem = {"title": "专家级挑战", "description": "竞赛题目"}
        assert estimate_difficulty(problem) == 5

    def test_default_difficulty(self):
        """Test default difficulty when no keywords match"""
        problem = {"title": "Some Problem", "description": "Some description"}
        # Should return default based on time limit or 2
        assert estimate_difficulty(problem) in [1, 2, 3, 4, 5]


class TestCourseDetection:
    """Tests for course detection"""

    def test_detect_python(self):
        """Test Python course detection"""
        problem = {
            "title": "Python入门",
            "description": "使用input()和print()函数",
            "source": "",
        }
        assert detect_course(problem) == "Python"

    def test_detect_dsa(self):
        """Test DSA course detection"""
        problem = {
            "title": "链表操作",
            "description": "实现一个链表数据结构",
            "source": "",
        }
        assert detect_course(problem) == "DSA"

    def test_detect_algorithm(self):
        """Test ADA course detection"""
        problem = {
            "title": "动态规划问题",
            "description": "使用贪心算法求解",
            "source": "",
        }
        course = detect_course(problem)
        assert course in ["DSA", "ADA"]

    def test_no_match(self):
        """Test when no course matches"""
        problem = {
            "title": "Generic Problem",
            "description": "Some generic description",
            "source": "",
        }
        # May or may not match, should not raise error
        result = detect_course(problem)
        assert result is None or result in [
            "C", "CPP", "Python", "Java", "Rust", "DSA", "ADA", "DiscreteMath"
        ]


class TestKnowledgePoints:
    """Tests for knowledge point extraction"""

    def test_extract_loop(self):
        """Test loop knowledge point extraction"""
        problem = {"title": "循环练习", "description": "使用for循环"}
        points = extract_knowledge_points(problem)
        assert "循环" in points

    def test_extract_array(self):
        """Test array knowledge point extraction"""
        problem = {"title": "数组操作", "description": "使用数组存储数据"}
        points = extract_knowledge_points(problem)
        assert "数组" in points

    def test_extract_multiple(self):
        """Test multiple knowledge points extraction"""
        problem = {
            "title": "排序算法",
            "description": "使用动态规划和递归方法",
        }
        points = extract_knowledge_points(problem)
        # Should find at least some points
        assert isinstance(points, list)


class TestExerciseConversion:
    """Tests for converting FPS problem to Exercise model"""

    def test_convert_basic_problem(self):
        """Test basic problem conversion"""
        exercise = convert_to_exercise(SAMPLE_PROBLEM)

        assert exercise.source == "tk"
        assert exercise.type == "programming"
        assert exercise.difficulty in [1, 2, 3, 4, 5]
        assert exercise.content["title"] == "A+B Problem"
        assert exercise.content["description"] == "输入两个整数，输出它们的和。"
        assert len(exercise.test_cases) == 1
        assert exercise.is_verified is True

    def test_convert_with_course(self):
        """Test conversion with course assignment"""
        # Course assignment is done separately, but we can test the structure
        exercise = convert_to_exercise(SAMPLE_PROBLEM, course_id=1)
        # Note: course_id is not stored in Exercise model directly
        # It's associated via chapter or stage

    def test_convert_preserves_test_cases(self):
        """Test that test cases are preserved"""
        problem = {
            **SAMPLE_PROBLEM,
            "test_cases": [
                {"input": "1 2", "output": "3", "name": "test1"},
                {"input": "5 6", "output": "11", "name": "test2"},
            ],
        }
        exercise = convert_to_exercise(problem)
        assert len(exercise.test_cases) == 2
