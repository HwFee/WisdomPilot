"""
BKT (Bayesian Knowledge Tracing) Based Exercise Count Calculator

基于BKT模型和知识点数量，动态计算每个小节需要的基础题数量。

BKT模型参数：
- P(L0): 初始掌握概率（根据知识点难度估算）
- P(T): 学习转移概率（从不会到会的概率）
- P(G): 猜测概率（不会但答对的概率）
- P(S): 滑落概率（会但答错的概率）

通关条件：掌握概率 P(L) >= 0.95
"""

import json
import math
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class BKTParams:
    """BKT模型参数"""
    p_l0: float  # 初始掌握概率
    p_t: float   # 学习转移概率
    p_g: float   # 猜测概率
    p_s: float   # 滑落概率


@dataclass
class KnowledgePoint:
    """知识点"""
    name: str
    difficulty: int  # 1-5 难度等级
    importance: int  # 1-5 重要程度


@dataclass
class Section:
    """小节"""
    title: str
    order_index: int
    knowledge_points: List[KnowledgePoint]


@dataclass
class Chapter:
    """章节"""
    title: str
    order_index: int
    sections: List[Section]


def get_bkt_params(difficulty: int, importance: int) -> BKTParams:
    """
    根据知识点难度和重要程度估算BKT参数

    难度越高：
    - 初始掌握概率越低
    - 学习转移概率越低（需要更多练习）

    重要程度越高：
    - 需要更高的置信度
    """
    # 基础参数
    base_p_l0 = 0.3  # 基础初始掌握概率
    base_p_t = 0.15  # 基础学习转移概率

    # 根据难度调整
    # difficulty: 1-5, 越高越难
    difficulty_factor = (difficulty - 1) / 4  # 0-1

    p_l0 = base_p_l0 * (1 - difficulty_factor * 0.6)  # 0.12 - 0.30
    p_t = base_p_t * (1 - difficulty_factor * 0.5)    # 0.075 - 0.15

    # 猜测概率（选择题约25%，填空题约10%）
    p_g = 0.20
    # 滑落概率（通常较低）
    p_s = 0.05

    return BKTParams(p_l0=max(0.1, p_l0), p_t=max(0.05, p_t), p_g=p_g, p_s=p_s)


def calculate_correct_prob(p_l: float, params: BKTParams) -> float:
    """
    计算答对概率 P(C) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
    """
    return p_l * (1 - params.p_s) + (1 - p_l) * params.p_g


def update_mastery(p_l: float, is_correct: bool, params: BKTParams) -> float:
    """
    BKT更新公式：根据答题结果更新掌握概率

    如果答对：
    P(L|correct) = P(L) * (1 - P(S)) / P(C)
    然后应用学习：P(L)' = P(L|correct) + (1 - P(L|correct)) * P(T)

    如果答错：
    P(L|wrong) = P(L) * P(S) / (1 - P(C))
    然后应用学习：P(L)' = P(L|wrong) + (1 - P(L|wrong)) * P(T)
    """
    p_c = calculate_correct_prob(p_l, params)

    if is_correct:
        # 答对时的后验概率
        if p_c > 0:
            p_l_given_correct = p_l * (1 - params.p_s) / p_c
        else:
            p_l_given_correct = p_l
        p_l_new = p_l_given_correct
    else:
        # 答错时的后验概率
        if 1 - p_c > 0:
            p_l_given_wrong = p_l * params.p_s / (1 - p_c)
        else:
            p_l_given_wrong = p_l
        p_l_new = p_l_given_wrong

    # 应用学习转移
    p_l_new = p_l_new + (1 - p_l_new) * params.p_t

    return min(0.99, max(0.01, p_l_new))


def calculate_exercises_needed(
    params: BKTParams,
    target_mastery: float = 0.95,
    max_exercises: int = 20,
    min_exercises: int = 3,
    confidence_threshold: float = 0.90
) -> Dict[str, Any]:
    """
    计算达到目标掌握概率所需的练习题数量

    使用连续答对的策略来计算（通关模式：需要全部正确）

    Args:
        params: BKT模型参数
        target_mastery: 目标掌握概率（通关阈值）
        max_exercises: 最大练习题数
        min_exercises: 最小练习题数
        confidence_threshold: 置信度阈值

    Returns:
        dict: 包含所需题数和详细过程
    """
    p_l = params.p_l0
    exercises_needed = 0
    history = []

    # 记录初始状态
    history.append({
        "exercise": 0,
        "mastery": p_l,
        "correct_prob": calculate_correct_prob(p_l, params)
    })

    # 模拟连续答对的情况（通关要求全部正确）
    while p_l < target_mastery and exercises_needed < max_exercises:
        exercises_needed += 1

        # 假设答对
        p_l = update_mastery(p_l, True, params)

        correct_prob = calculate_correct_prob(p_l, params)

        history.append({
            "exercise": exercises_needed,
            "mastery": p_l,
            "correct_prob": correct_prob
        })

        # 如果已经达到目标掌握概率，再检查置信度
        if p_l >= target_mastery:
            # 计算置信度：连续答对这么多题的概率
            # 这个概率越高，说明学生真正掌握的可能性越大
            break

    # 确保最小练习量
    exercises_needed = max(min_exercises, exercises_needed)

    # 如果知识点难度高或重要程度高，增加额外题目
    # 这里通过参数间接体现

    return {
        "exercises_needed": exercises_needed,
        "initial_mastery": params.p_l0,
        "final_mastery": p_l,
        "target_mastery": target_mastery,
        "history": history
    }


def calculate_section_exercises(
    knowledge_points: List[KnowledgePoint],
    target_mastery: float = 0.95,
    coverage_ratio: float = 0.8  # 题目覆盖知识点的比例
) -> Dict[str, Any]:
    """
    计算一个小节需要的练习题数量

    Args:
        knowledge_points: 知识点列表
        target_mastery: 目标掌握概率
        coverage_ratio: 每道题平均覆盖的知识点比例

    Returns:
        dict: 包含总题数、每个知识点详情等
    """
    kp_details = []
    total_exercises = 0

    for kp in knowledge_points:
        params = get_bkt_params(kp.difficulty, kp.importance)
        result = calculate_exercises_needed(
            params,
            target_mastery=target_mastery
        )

        kp_detail = {
            "name": kp.name,
            "difficulty": kp.difficulty,
            "importance": kp.importance,
            "bkt_params": {
                "p_l0": round(params.p_l0, 3),
                "p_t": round(params.p_t, 3),
                "p_g": params.p_g,
                "p_s": params.p_s
            },
            "exercises_needed": result["exercises_needed"],
            "initial_mastery": round(result["initial_mastery"], 3),
            "final_mastery": round(result["final_mastery"], 3)
        }
        kp_details.append(kp_detail)
        total_exercises += result["exercises_needed"]

    # 考虑题目覆盖多个知识点的情况，可以适当减少总题数
    # 使用加权平均，因为一道题可能覆盖多个知识点
    if len(knowledge_points) > 1:
        # 计算平均每道题需要的练习次数
        avg_exercises = total_exercises / len(knowledge_points)

        # 由于题目可能覆盖多个知识点，实际需要的题目数可以少一些
        # 但为了保证每个知识点都有足够的覆盖，我们取一个平衡值
        # 基础题数量 = 知识点平均题数 * 知识点数量 * 覆盖系数
        adjusted_exercises = math.ceil(avg_exercises * len(knowledge_points) * coverage_ratio)
    else:
        adjusted_exercises = total_exercises

    # 确保最小题目数（每个知识点至少2题）
    min_section_exercises = max(3, len(knowledge_points) * 2)
    adjusted_exercises = max(min_section_exercises, adjusted_exercises)

    return {
        "kp_count": len(knowledge_points),
        "kp_details": kp_details,
        "raw_total_exercises": total_exercises,
        "adjusted_exercises": adjusted_exercises,
        "min_exercises": min_section_exercises
    }


def generate_c_course_exercise_count():
    """
    为C语言程序设计课程生成各章节习题数量表
    """
    # C语言课程章节和知识点数据（基于generate_all_chapters.py）
    course_data = {
        "course_name": "C语言程序设计",
        "course_code": "C",
        "chapters": [
            {
                "title": "简单C程序设计",
                "order_index": 1,
                "sections": [
                    {
                        "title": "C程序入门",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "C程序的基本结构", "difficulty": 1, "importance": 5},
                            {"name": "main函数", "difficulty": 1, "importance": 5},
                            {"name": "语句与注释", "difficulty": 1, "importance": 4}
                        ]
                    },
                    {
                        "title": "基本数据类型与变量",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "基本数据类型", "difficulty": 1, "importance": 5},
                            {"name": "标识符", "difficulty": 1, "importance": 4},
                            {"name": "变量与常量", "difficulty": 1, "importance": 5},
                            {"name": "printf格式化输出", "difficulty": 1, "importance": 5}
                        ]
                    },
                    {
                        "title": "程序设计基础",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "算法与流程图", "difficulty": 2, "importance": 4},
                            {"name": "程序设计描述方法", "difficulty": 2, "importance": 4},
                            {"name": "常见错误分析", "difficulty": 2, "importance": 5},
                            {"name": "编程风格", "difficulty": 1, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "选择控制结构与应用",
                "order_index": 2,
                "sections": [
                    {
                        "title": "关系运算与逻辑运算",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "关系运算符", "difficulty": 1, "importance": 5},
                            {"name": "逻辑运算符", "difficulty": 1, "importance": 5},
                            {"name": "if语句基本形式", "difficulty": 1, "importance": 5}
                        ]
                    },
                    {
                        "title": "if语句嵌套与应用",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "if语句嵌套", "difficulty": 2, "importance": 5},
                            {"name": "条件运算符", "difficulty": 1, "importance": 4}
                        ]
                    },
                    {
                        "title": "switch语句",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "switch语句基础", "difficulty": 1, "importance": 5},
                            {"name": "switch语句深入", "difficulty": 2, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "循环结构及应用",
                "order_index": 3,
                "sections": [
                    {
                        "title": "for循环",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "for循环基本结构", "difficulty": 1, "importance": 5},
                            {"name": "for循环变体", "difficulty": 2, "importance": 4}
                        ]
                    },
                    {
                        "title": "while循环",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "while循环", "difficulty": 1, "importance": 5},
                            {"name": "do-while循环", "difficulty": 1, "importance": 4}
                        ]
                    },
                    {
                        "title": "循环嵌套与控制",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "循环嵌套", "difficulty": 2, "importance": 5},
                            {"name": "break与continue", "difficulty": 1, "importance": 5}
                        ]
                    }
                ]
            },
            {
                "title": "模块化设计与应用",
                "order_index": 4,
                "sections": [
                    {
                        "title": "函数基础",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "函数定义", "difficulty": 1, "importance": 5},
                            {"name": "函数声明", "difficulty": 1, "importance": 4},
                            {"name": "函数调用", "difficulty": 1, "importance": 5}
                        ]
                    },
                    {
                        "title": "预处理指令",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "宏定义", "difficulty": 1, "importance": 5},
                            {"name": "条件编译", "difficulty": 1, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "相同数据类型集合",
                "order_index": 5,
                "sections": [
                    {
                        "title": "一维数组",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "一维数组基础", "difficulty": 1, "importance": 5},
                            {"name": "数组遍历与操作", "difficulty": 1, "importance": 5}
                        ]
                    },
                    {
                        "title": "二维数组",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "二维数组基础", "difficulty": 2, "importance": 5},
                            {"name": "二维数组应用", "difficulty": 2, "importance": 4}
                        ]
                    },
                    {
                        "title": "字符串与字符数组",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "字符串基础", "difficulty": 1, "importance": 5},
                            {"name": "字符串函数", "difficulty": 2, "importance": 5}
                        ]
                    }
                ]
            },
            {
                "title": "指针基础",
                "order_index": 6,
                "sections": [
                    {
                        "title": "指针概念",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "指针变量", "difficulty": 3, "importance": 5},
                            {"name": "指针运算", "difficulty": 3, "importance": 5}
                        ]
                    },
                    {
                        "title": "指针与数组",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "指针与一维数组", "difficulty": 3, "importance": 5},
                            {"name": "指针与字符串", "difficulty": 3, "importance": 4}
                        ]
                    },
                    {
                        "title": "指针与函数",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "指针作为参数", "difficulty": 3, "importance": 5},
                            {"name": "指针作为返回值", "difficulty": 3, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "结构体与联合体",
                "order_index": 7,
                "sections": [
                    {
                        "title": "结构体基础",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "结构体定义", "difficulty": 2, "importance": 5},
                            {"name": "结构体变量", "difficulty": 2, "importance": 5}
                        ]
                    },
                    {
                        "title": "结构体应用",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "结构体数组", "difficulty": 2, "importance": 4},
                            {"name": "结构体指针", "difficulty": 3, "importance": 5}
                        ]
                    },
                    {
                        "title": "联合体与枚举",
                        "order_index": 3,
                        "knowledge_points": [
                            {"name": "联合体", "difficulty": 2, "importance": 3},
                            {"name": "枚举类型", "difficulty": 2, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "文件操作",
                "order_index": 8,
                "sections": [
                    {
                        "title": "文件基础",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "文件打开与关闭", "difficulty": 2, "importance": 5},
                            {"name": "文件读写", "difficulty": 2, "importance": 5}
                        ]
                    },
                    {
                        "title": "文件应用",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "文件定位", "difficulty": 2, "importance": 4},
                            {"name": "文件错误处理", "difficulty": 2, "importance": 4}
                        ]
                    }
                ]
            },
            {
                "title": "综合应用",
                "order_index": 9,
                "sections": [
                    {
                        "title": "程序设计方法",
                        "order_index": 1,
                        "knowledge_points": [
                            {"name": "程序设计流程", "difficulty": 2, "importance": 4},
                            {"name": "模块化设计", "difficulty": 3, "importance": 5}
                        ]
                    },
                    {
                        "title": "综合案例",
                        "order_index": 2,
                        "knowledge_points": [
                            {"name": "学生管理系统", "difficulty": 4, "importance": 5},
                            {"name": "文件处理案例", "difficulty": 3, "importance": 4}
                        ]
                    }
                ]
            }
        ]
    }

    # 计算每个章节、小节的习题数量
    result = {
        "course_name": course_data["course_name"],
        "course_code": course_data["course_code"],
        "description": "基于BKT模型的习题数量计算结果",
        "bkt_model": {
            "description": "Bayesian Knowledge Tracing 模型参数说明",
            "parameters": {
                "P(L0)": "初始掌握概率，根据知识点难度估算",
                "P(T)": "学习转移概率，从不会到会的概率",
                "P(G)": "猜测概率，不会但答对的概率（默认0.20）",
                "P(S)": "滑落概率，会但答错的概率（默认0.05）"
            },
            "mastery_threshold": 0.95,
            "通关条件": "所有基础题全部答对后，知识点掌握概率达到95%"
        },
        "chapters": [],
        "summary": {}
    }

    total_exercises = 0
    total_kp = 0

    for chapter_data in course_data["chapters"]:
        chapter_result = {
            "title": chapter_data["title"],
            "order_index": chapter_data["order_index"],
            "sections": [],
            "chapter_total": 0
        }

        for section_data in chapter_data["sections"]:
            # 创建知识点对象列表
            kps = [
                KnowledgePoint(
                    name=kp["name"],
                    difficulty=kp["difficulty"],
                    importance=kp["importance"]
                )
                for kp in section_data["knowledge_points"]
            ]

            # 计算小节习题数量
            section_result = calculate_section_exercises(kps)

            section_output = {
                "title": section_data["title"],
                "order_index": section_data["order_index"],
                "knowledge_point_count": len(kps),
                "base_questions_count": section_result["adjusted_exercises"],
                "knowledge_points": section_result["kp_details"],
                "calculation_detail": {
                    "raw_total": section_result["raw_total_exercises"],
                    "adjusted": section_result["adjusted_exercises"],
                    "min_required": section_result["min_exercises"]
                }
            }

            chapter_result["sections"].append(section_output)
            chapter_result["chapter_total"] += section_result["adjusted_exercises"]
            total_exercises += section_result["adjusted_exercises"]
            total_kp += len(kps)

        result["chapters"].append(chapter_result)

    result["summary"] = {
        "total_chapters": len(course_data["chapters"]),
        "total_sections": sum(len(ch["sections"]) for ch in course_data["chapters"]),
        "total_knowledge_points": total_kp,
        "total_base_questions": total_exercises,
        "average_questions_per_section": round(total_exercises / sum(len(ch["sections"]) for ch in course_data["chapters"]), 1),
        "通关说明": "学生需要将每小节的所有基础题全部答对，即可通过该小节。系统会根据BKT模型追踪学生对每个知识点的掌握程度。"
    }

    return result


def main():
    """主函数：生成并保存习题数量表"""
    # 生成结果
    result = generate_c_course_exercise_count()

    # 保存到文件
    output_path = "C语言程序设计_习题数量表.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"习题数量表已生成: {output_path}")
    print(f"\n{'='*60}")
    print(f"C语言程序设计 - 基础题数量统计")
    print(f"{'='*60}")
    print(f"总章节数: {result['summary']['total_chapters']}")
    print(f"总小节数: {result['summary']['total_sections']}")
    print(f"总知识点数: {result['summary']['total_knowledge_points']}")
    print(f"基础题总数: {result['summary']['total_base_questions']}")
    print(f"平均每小节: {result['summary']['average_questions_per_section']} 题")
    print(f"\n{'='*60}")
    print("各章节详情:")
    print(f"{'='*60}")

    for chapter in result['chapters']:
        print(f"\n第{chapter['order_index']}章: {chapter['title']}")
        print(f"  本章基础题总数: {chapter['chapter_total']} 题")
        for section in chapter['sections']:
            print(f"  - {section['title']}: {section['base_questions_count']} 题 ({section['knowledge_point_count']}个知识点)")

    return result


if __name__ == "__main__":
    main()
