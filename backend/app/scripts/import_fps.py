"""
FPS (Free Problem Set) Format Import Script

This script imports exercises from FPS XML files downloaded from tk.hustoj.com

Usage:
    # Import a single FPS file
    python -m app.scripts.import_fps --file path/to/problems.xml

    # Import all FPS files from a directory
    python -m app.scripts.import_fps --dir path/to/fps_files/

    # Import with course assignment
    python -m app.scripts.import_fps --file problems.xml --course Python --auto-assign

FPS Format Reference:
    http://code.google.com/p/freeproblemset/
"""

import argparse
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from xml.etree import ElementTree as ET

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, init_db
from app.models.exercise import Exercise
from app.models.course import Course


# Course code mapping based on problem tags/content
COURSE_KEYWORDS = {
    "C": ["c语言", "c程序", "stdio", "scanf", "printf", "malloc", "指针", "pointer"],
    "CPP": ["c++", "cpp", "iostream", "cin", "cout", "vector", "class", "stl", "模板"],
    "Python": ["python", "input()", "print(", "def ", "import ", "list(", "dict("],
    "Java": ["java", "public class", "system.out", "scanner", "import java"],
    "Rust": ["rust", "fn main", "let mut", "println!", "cargo"],
    "DSA": ["数据结构", "算法", "链表", "栈", "队列", "树", "图", "排序", "查找",
            "linked list", "stack", "queue", "tree", "graph", "sort", "search",
            "递归", "recursion", "动态规划", "dynamic programming"],
    "ADA": ["算法设计", "贪心", "分治", "回溯", "分支限界", "greedy", "divide conquer",
            "backtracking", "branch and bound", "复杂度", "complexity"],
    "DiscreteMath": ["离散", "集合", "逻辑", "命题", "谓词", "关系", "函数", "图论",
                     "set", "logic", "proposition", "predicate", "relation", "function"]
}

# Difficulty estimation keywords
DIFFICULTY_KEYWORDS = {
    1: ["入门", "基础", "简单", "beginner", "basic", "easy", "a+b", "hello"],
    2: ["初级", "初级算法", "elementary"],
    3: ["中等", "中级", "medium", "intermediate"],
    4: ["困难", "高级", "hard", "advanced", "困难"],
    5: ["挑战", "专家", "expert", "challenge", "竞赛", "competition"]
}


def parse_fps_xml(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse FPS XML file and extract problem data

    Args:
        file_path: Path to the FPS XML file

    Returns:
        List of problem dictionaries
    """
    problems = []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file {file_path}: {e}")
        return problems

    # FPS format: root is <fps>, items are <item>
    for item in root.findall('.//item'):
        problem = {}

        # Title
        title_elem = item.find('title')
        if title_elem is not None and title_elem.text:
            problem['title'] = title_elem.text.strip()
        else:
            problem['title'] = f"Problem {len(problems) + 1}"

        # Time limit (seconds)
        time_limit = item.find('time_limit')
        if time_limit is not None and time_limit.text:
            try:
                problem['time_limit'] = int(float(time_limit.text.strip()))
            except ValueError:
                problem['time_limit'] = 1
        else:
            problem['time_limit'] = 1

        # Memory limit (MB)
        memory_limit = item.find('memory_limit')
        if memory_limit is not None and memory_limit.text:
            try:
                problem['memory_limit'] = int(float(memory_limit.text.strip()))
            except ValueError:
                problem['memory_limit'] = 128
        else:
            problem['memory_limit'] = 128

        # Description
        desc_elem = item.find('description')
        if desc_elem is not None and desc_elem.text:
            problem['description'] = desc_elem.text.strip()
        else:
            problem['description'] = ""

        # Input specification
        input_elem = item.find('input')
        if input_elem is not None and input_elem.text:
            problem['input_spec'] = input_elem.text.strip()
        else:
            problem['input_spec'] = ""

        # Output specification
        output_elem = item.find('output')
        if output_elem is not None and output_elem.text:
            problem['output_spec'] = output_elem.text.strip()
        else:
            problem['output_spec'] = ""

        # Sample input
        sample_in = item.find('sample_input')
        if sample_in is not None and sample_in.text:
            problem['sample_input'] = sample_in.text.strip()
        else:
            problem['sample_input'] = ""

        # Sample output
        sample_out = item.find('sample_output')
        if sample_out is not None and sample_out.text:
            problem['sample_output'] = sample_out.text.strip()
        else:
            problem['sample_output'] = ""

        # Hint
        hint_elem = item.find('hint')
        if hint_elem is not None and hint_elem.text:
            problem['hint'] = hint_elem.text.strip()
        else:
            problem['hint'] = ""

        # Source
        source_elem = item.find('source')
        if source_elem is not None and source_elem.text:
            problem['source'] = source_elem.text.strip()
        else:
            problem['source'] = ""

        # Test cases (may have multiple)
        test_cases = []
        test_inputs = item.findall('test_input')
        test_outputs = item.findall('test_output')

        # Match test inputs with outputs by name attribute
        input_map = {}
        for ti in test_inputs:
            name = ti.get('name', f'test{len(input_map)}')
            if ti.text:
                input_map[name] = ti.text.strip()

        output_map = {}
        for to in test_outputs:
            name = to.get('name', f'test{len(output_map)}')
            if to.text:
                output_map[name] = to.text.strip()

        # Create test case pairs
        for name in input_map:
            if name in output_map:
                test_cases.append({
                    'input': input_map[name],
                    'output': output_map[name],
                    'name': name
                })

        # If no named test cases, try to use sample as test case
        if not test_cases and problem['sample_input'] and problem['sample_output']:
            test_cases.append({
                'input': problem['sample_input'],
                'output': problem['sample_output'],
                'name': 'sample'
            })

        problem['test_cases'] = test_cases

        # Images (base64 encoded)
        images = []
        for img in item.findall('img'):
            if img.text:
                images.append({
                    'src': img.get('src', ''),
                    'data': img.text.strip()
                })
        problem['images'] = images

        problems.append(problem)

    return problems


def estimate_difficulty(problem: Dict[str, Any]) -> int:
    """
    Estimate problem difficulty based on content analysis

    Args:
        problem: Problem dictionary

    Returns:
        Difficulty level (1-5)
    """
    text = f"{problem.get('title', '')} {problem.get('description', '')}".lower()

    for level, keywords in DIFFICULTY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return level

    # Default based on time/memory limits
    time_limit = problem.get('time_limit', 1)
    if time_limit >= 5:
        return 4
    elif time_limit >= 2:
        return 3
    elif time_limit >= 1:
        return 2

    return 2  # Default medium-easy


def detect_course(problem: Dict[str, Any]) -> Optional[str]:
    """
    Detect which course a problem belongs to based on content

    Args:
        problem: Problem dictionary

    Returns:
        Course code or None
    """
    text = f"{problem.get('title', '')} {problem.get('description', '')} {problem.get('source', '')}".lower()

    # Check source first (often contains course info)
    source = problem.get('source', '').lower()
    for course_code, keywords in COURSE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in source:
                return course_code

    # Then check full text
    matches = {}
    for course_code, keywords in COURSE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            matches[course_code] = score

    if matches:
        return max(matches, key=matches.get)

    return None


def extract_knowledge_points(problem: Dict[str, Any]) -> List[str]:
    """
    Extract knowledge points from problem content

    Args:
        problem: Problem dictionary

    Returns:
        List of knowledge point tags
    """
    points = []
    text = f"{problem.get('title', '')} {problem.get('description', '')}".lower()

    # Common knowledge point patterns
    patterns = {
        "循环": ["循环", "loop", "for", "while"],
        "条件判断": ["条件", "if", "else", "判断"],
        "数组": ["数组", "array", "列表", "list"],
        "字符串": ["字符串", "string", "字符"],
        "函数": ["函数", "function", "方法", "method"],
        "递归": ["递归", "recursion", "recursive"],
        "排序": ["排序", "sort", "排列"],
        "查找": ["查找", "search", "搜索"],
        "链表": ["链表", "linked list", "list node"],
        "树": ["树", "tree", "二叉", "binary"],
        "图": ["图", "graph", "顶点", "vertex", "边", "edge"],
        "动态规划": ["动态规划", "dynamic programming", "dp", "状态转移"],
        "贪心": ["贪心", "greedy", "最优"],
        "分治": ["分治", "divide", "conquer"],
        "回溯": ["回溯", "backtrack", "回溯"],
        "输入输出": ["输入", "输出", "input", "output", "scanf", "printf"],
        "数学": ["数学", "数学运算", "计算", "calculate", "运算"],
        "位运算": ["位运算", "bit", "位操作"],
    }

    for point, keywords in patterns.items():
        for kw in keywords:
            if kw.lower() in text:
                points.append(point)
                break

    return list(set(points))


def convert_to_exercise(
    problem: Dict[str, Any],
    course_id: Optional[int] = None,
    chapter_id: Optional[int] = None
) -> Exercise:
    """
    Convert FPS problem to Exercise model

    Args:
        problem: Parsed problem dictionary
        course_id: Optional course ID to assign
        chapter_id: Optional chapter ID to assign

    Returns:
        Exercise model instance
    """
    # Build content for programming exercise
    content = {
        "title": problem.get('title', 'Untitled'),
        "description": problem.get('description', ''),
        "input_format": problem.get('input_spec', ''),
        "output_format": problem.get('output_spec', ''),
        "sample_input": problem.get('sample_input', ''),
        "sample_output": problem.get('sample_output', ''),
        "time_limit": problem.get('time_limit', 1),
        "memory_limit": problem.get('memory_limit', 128),
        "source": problem.get('source', ''),
    }

    # Add images if present
    if problem.get('images'):
        content['images'] = problem['images']

    # Build solution with hint
    solution = None
    if problem.get('hint'):
        solution = {
            "explanation": problem.get('hint', ''),
            "hint": problem.get('hint', '')
        }

    # Build test cases
    test_cases = problem.get('test_cases', [])

    # Determine difficulty
    difficulty = estimate_difficulty(problem)

    # Extract knowledge points
    knowledge_points = extract_knowledge_points(problem)

    # Create exercise
    exercise = Exercise(
        chapter_id=chapter_id,
        source="tk",
        source_id=problem.get('source', ''),
        type="programming",  # FPS format is typically programming problems
        difficulty=difficulty,
        difficulty_weight=1.0 + (difficulty - 3) * 0.2,  # Weight based on difficulty
        knowledge_points=knowledge_points,
        content=content,
        solution=solution,
        test_cases=test_cases if test_cases else None,
        hints=[problem.get('hint')] if problem.get('hint') else None,
        is_verified=True,  # FPS problems are pre-verified
    )

    return exercise


async def import_problems(
    problems: List[Dict[str, Any]],
    session: AsyncSession,
    course_code: Optional[str] = None,
    auto_assign_course: bool = False
) -> Dict[str, int]:
    """
    Import problems into database

    Args:
        problems: List of parsed problem dictionaries
        session: Database session
        course_code: Optional course code to assign all problems
        auto_assign_course: Whether to auto-detect course for each problem

    Returns:
        Statistics dictionary
    """
    stats = {
        "total": len(problems),
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "by_course": {}
    }

    # Get all courses for reference
    result = await session.execute(select(Course))
    courses = {c.code: c for c in result.scalars().all()}

    for problem in problems:
        try:
            # Determine course assignment
            target_course = None

            if course_code:
                target_course = courses.get(course_code)
            elif auto_assign_course:
                detected_code = detect_course(problem)
                if detected_code and detected_code in courses:
                    target_course = courses[detected_code]

            # Convert to Exercise
            exercise = convert_to_exercise(
                problem,
                course_id=target_course.id if target_course else None
            )

            session.add(exercise)
            stats["imported"] += 1

            # Track by course
            course_key = target_course.code if target_course else "unassigned"
            stats["by_course"][course_key] = stats["by_course"].get(course_key, 0) + 1

        except Exception as e:
            print(f"Error importing problem '{problem.get('title', 'Unknown')}': {e}")
            stats["errors"] += 1

    await session.commit()

    return stats


async def import_fps_file(
    file_path: Path,
    course_code: Optional[str] = None,
    auto_assign_course: bool = False
) -> Dict[str, int]:
    """
    Import problems from a single FPS file

    Args:
        file_path: Path to FPS XML file
        course_code: Optional course code to assign
        auto_assign_course: Whether to auto-detect course

    Returns:
        Statistics dictionary
    """
    print(f"Parsing FPS file: {file_path}")
    problems = parse_fps_xml(file_path)

    if not problems:
        print(f"No problems found in {file_path}")
        return {"total": 0, "imported": 0, "skipped": 0, "errors": 1}

    print(f"Found {len(problems)} problems")

    async with AsyncSessionLocal() as session:
        stats = await import_problems(
            problems,
            session,
            course_code,
            auto_assign_course
        )

    return stats


async def import_fps_directory(
    directory: Path,
    course_code: Optional[str] = None,
    auto_assign_course: bool = False
) -> Dict[str, int]:
    """
    Import problems from all FPS files in a directory

    Args:
        directory: Directory containing FPS XML files
        course_code: Optional course code to assign
        auto_assign_course: Whether to auto-detect course

    Returns:
        Combined statistics dictionary
    """
    total_stats = {
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "by_course": {},
        "files_processed": 0
    }

    # Find all XML files
    xml_files = list(directory.glob("*.xml"))

    if not xml_files:
        print(f"No XML files found in {directory}")
        return total_stats

    print(f"Found {len(xml_files)} XML files in {directory}")

    async with AsyncSessionLocal() as session:
        for xml_file in xml_files:
            print(f"\nProcessing: {xml_file.name}")
            problems = parse_fps_xml(xml_file)

            if problems:
                stats = await import_problems(
                    problems,
                    session,
                    course_code,
                    auto_assign_course
                )

                # Aggregate stats
                total_stats["total"] += stats["total"]
                total_stats["imported"] += stats["imported"]
                total_stats["skipped"] += stats["skipped"]
                total_stats["errors"] += stats["errors"]
                total_stats["files_processed"] += 1

                for course, count in stats.get("by_course", {}).items():
                    total_stats["by_course"][course] = \
                        total_stats["by_course"].get(course, 0) + count

    return total_stats


def print_stats(stats: Dict[str, int]):
    """Print import statistics"""
    print("\n" + "=" * 50)
    print("Import Statistics")
    print("=" * 50)
    print(f"Total problems:  {stats['total']}")
    print(f"Imported:        {stats['imported']}")
    print(f"Skipped:         {stats['skipped']}")
    print(f"Errors:          {stats['errors']}")

    if stats.get('files_processed'):
        print(f"Files processed: {stats['files_processed']}")

    if stats.get('by_course'):
        print("\nBy Course:")
        for course, count in sorted(stats['by_course'].items()):
            print(f"  {course}: {count}")

    print("=" * 50)


async def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Import FPS format problems from tk.hustoj.com"
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Path to a single FPS XML file"
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        help="Path to directory containing FPS XML files"
    )
    parser.add_argument(
        "--course", "-c",
        type=str,
        choices=["C", "CPP", "Python", "Java", "Rust", "DSA", "ADA", "DiscreteMath"],
        help="Assign all problems to this course"
    )
    parser.add_argument(
        "--auto-assign", "-a",
        action="store_true",
        help="Auto-detect course for each problem based on content"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database before import"
    )

    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.print_help()
        print("\nError: Please specify either --file or --dir")
        return

    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        await init_db()

    # Import from file or directory
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            return
        stats = await import_fps_file(args.file, args.course, args.auto_assign)
    else:
        if not args.dir.exists():
            print(f"Error: Directory not found: {args.dir}")
            return
        stats = await import_fps_directory(args.dir, args.course, args.auto_assign)

    print_stats(stats)


if __name__ == "__main__":
    asyncio.run(main())
