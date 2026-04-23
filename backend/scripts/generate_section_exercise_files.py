"""
Generate exercise count files for each section
根据BKT模型为每个小节生成独立的习题数量文件
"""

import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any
import math


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
    difficulty: int
    importance: int


def get_bkt_params(difficulty: int, importance: int) -> BKTParams:
    """根据知识点难度和重要程度估算BKT参数"""
    base_p_l0 = 0.3
    base_p_t = 0.15
    difficulty_factor = (difficulty - 1) / 4

    p_l0 = base_p_l0 * (1 - difficulty_factor * 0.6)
    p_t = base_p_t * (1 - difficulty_factor * 0.5)

    return BKTParams(
        p_l0=max(0.1, p_l0),
        p_t=max(0.05, p_t),
        p_g=0.20,
        p_s=0.05
    )


def calculate_correct_prob(p_l: float, params: BKTParams) -> float:
    """计算答对概率"""
    return p_l * (1 - params.p_s) + (1 - p_l) * params.p_g


def update_mastery(p_l: float, is_correct: bool, params: BKTParams) -> float:
    """BKT更新公式"""
    p_c = calculate_correct_prob(p_l, params)

    if is_correct:
        if p_c > 0:
            p_l_given_correct = p_l * (1 - params.p_s) / p_c
        else:
            p_l_given_correct = p_l
        p_l_new = p_l_given_correct
    else:
        if 1 - p_c > 0:
            p_l_given_wrong = p_l * params.p_s / (1 - p_c)
        else:
            p_l_given_wrong = p_l
        p_l_new = p_l_given_wrong

    p_l_new = p_l_new + (1 - p_l_new) * params.p_t
    return min(0.99, max(0.01, p_l_new))


def calculate_exercises_needed(
    params: BKTParams,
    target_mastery: float = 0.80,
    max_exercises: int = 20,
    min_exercises: int = 2
) -> Dict[str, Any]:
    """计算达到目标掌握概率所需的练习题数量"""
    p_l = params.p_l0
    exercises_needed = 0
    history = []

    history.append({
        "exercise": 0,
        "mastery": p_l,
        "correct_prob": calculate_correct_prob(p_l, params)
    })

    while p_l < target_mastery and exercises_needed < max_exercises:
        exercises_needed += 1
        p_l = update_mastery(p_l, True, params)
        correct_prob = calculate_correct_prob(p_l, params)
        history.append({
            "exercise": exercises_needed,
            "mastery": p_l,
            "correct_prob": correct_prob
        })

    exercises_needed = max(min_exercises, exercises_needed)

    return {
        "exercises_needed": exercises_needed,
        "initial_mastery": params.p_l0,
        "final_mastery": p_l,
        "target_mastery": target_mastery,
        "history": history
    }


def calculate_section_exercises(
    knowledge_points: List[KnowledgePoint],
    target_mastery: float = 0.80,
    coverage_ratio: float = 0.8
) -> Dict[str, Any]:
    """计算一个小节需要的练习题数量"""
    kp_details = []
    total_exercises = 0

    for kp in knowledge_points:
        params = get_bkt_params(kp.difficulty, kp.importance)
        result = calculate_exercises_needed(params, target_mastery)

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

    if len(knowledge_points) > 1:
        avg_exercises = total_exercises / len(knowledge_points)
        adjusted_exercises = math.ceil(avg_exercises * len(knowledge_points) * coverage_ratio)
    else:
        adjusted_exercises = total_exercises

    min_section_exercises = max(3, len(knowledge_points) * 2)
    adjusted_exercises = max(min_section_exercises, adjusted_exercises)

    return {
        "kp_count": len(knowledge_points),
        "kp_details": kp_details,
        "raw_total_exercises": total_exercises,
        "adjusted_exercises": adjusted_exercises,
        "min_exercises": min_section_exercises
    }


# C语言课程完整数据
C_COURSE_DATA = {
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
                    "estimated_minutes": 20,
                    "knowledge_points": [
                        {"name": "C程序的基本结构", "difficulty": 1, "importance": 5},
                        {"name": "main函数", "difficulty": 1, "importance": 5},
                        {"name": "语句与注释", "difficulty": 1, "importance": 4}
                    ]
                },
                {
                    "title": "基本数据类型与变量",
                    "order_index": 2,
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 20,
                    "knowledge_points": [
                        {"name": "关系运算符", "difficulty": 1, "importance": 5},
                        {"name": "逻辑运算符", "difficulty": 1, "importance": 5},
                        {"name": "if语句基本形式", "difficulty": 1, "importance": 5}
                    ]
                },
                {
                    "title": "if语句嵌套与应用",
                    "order_index": 2,
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "if语句嵌套", "difficulty": 2, "importance": 5},
                        {"name": "条件运算符", "difficulty": 1, "importance": 4}
                    ]
                },
                {
                    "title": "switch语句",
                    "order_index": 3,
                    "estimated_minutes": 20,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "for循环基本结构", "difficulty": 1, "importance": 5},
                        {"name": "for循环变体", "difficulty": 2, "importance": 4}
                    ]
                },
                {
                    "title": "while循环",
                    "order_index": 2,
                    "estimated_minutes": 20,
                    "knowledge_points": [
                        {"name": "while循环", "difficulty": 1, "importance": 5},
                        {"name": "do-while循环", "difficulty": 1, "importance": 4}
                    ]
                },
                {
                    "title": "循环嵌套与控制",
                    "order_index": 3,
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 30,
                    "knowledge_points": [
                        {"name": "函数定义", "difficulty": 1, "importance": 5},
                        {"name": "函数声明", "difficulty": 1, "importance": 4},
                        {"name": "函数调用", "difficulty": 1, "importance": 5}
                    ]
                },
                {
                    "title": "预处理指令",
                    "order_index": 2,
                    "estimated_minutes": 20,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "一维数组基础", "difficulty": 1, "importance": 5},
                        {"name": "数组遍历与操作", "difficulty": 1, "importance": 5}
                    ]
                },
                {
                    "title": "二维数组",
                    "order_index": 2,
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "二维数组基础", "difficulty": 2, "importance": 5},
                        {"name": "二维数组应用", "difficulty": 2, "importance": 4}
                    ]
                },
                {
                    "title": "字符串与字符数组",
                    "order_index": 3,
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "指针变量", "difficulty": 3, "importance": 5},
                        {"name": "指针运算", "difficulty": 3, "importance": 5}
                    ]
                },
                {
                    "title": "指针与数组",
                    "order_index": 2,
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "指针与一维数组", "difficulty": 3, "importance": 5},
                        {"name": "指针与字符串", "difficulty": 3, "importance": 4}
                    ]
                },
                {
                    "title": "指针与函数",
                    "order_index": 3,
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "结构体定义", "difficulty": 2, "importance": 5},
                        {"name": "结构体变量", "difficulty": 2, "importance": 5}
                    ]
                },
                {
                    "title": "结构体应用",
                    "order_index": 2,
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "结构体数组", "difficulty": 2, "importance": 4},
                        {"name": "结构体指针", "difficulty": 3, "importance": 5}
                    ]
                },
                {
                    "title": "联合体与枚举",
                    "order_index": 3,
                    "estimated_minutes": 20,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "文件打开与关闭", "difficulty": 2, "importance": 5},
                        {"name": "文件读写", "difficulty": 2, "importance": 5}
                    ]
                },
                {
                    "title": "文件应用",
                    "order_index": 2,
                    "estimated_minutes": 25,
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
                    "estimated_minutes": 25,
                    "knowledge_points": [
                        {"name": "程序设计流程", "difficulty": 2, "importance": 4},
                        {"name": "模块化设计", "difficulty": 3, "importance": 5}
                    ]
                },
                {
                    "title": "综合案例",
                    "order_index": 2,
                    "estimated_minutes": 30,
                    "knowledge_points": [
                        {"name": "学生管理系统", "difficulty": 4, "importance": 5},
                        {"name": "文件处理案例", "difficulty": 3, "importance": 4}
                    ]
                }
            ]
        }
    ]
}


def generate_section_files():
    """为每个小节生成独立的习题数量文件"""
    # 创建输出目录
    output_dir = "习题数量配置"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_sections = 0
    total_questions = 0

    for chapter_data in C_COURSE_DATA["chapters"]:
        chapter_order = chapter_data["order_index"]
        chapter_title = chapter_data["title"]

        for section_data in chapter_data["sections"]:
            total_sections += 1
            section_order = section_data["order_index"]

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
            result = calculate_section_exercises(kps)
            total_questions += result["adjusted_exercises"]

            # 构建小节配置数据
            section_config = {
                "course_name": C_COURSE_DATA["course_name"],
                "course_code": C_COURSE_DATA["course_code"],
                "chapter_index": chapter_order,
                "chapter_title": chapter_title,
                "section_index": section_order,
                "section_title": section_data["title"],
                "estimated_minutes": section_data.get("estimated_minutes", 20),
                "knowledge_point_count": len(kps),
                "base_questions_count": result["adjusted_exercises"],

                "knowledge_points": result["kp_details"],

                "bkt_model": {
                    "description": "Bayesian Knowledge Tracing 模型",
                    "parameters": {
                        "P(L0)": "初始掌握概率（根据知识点难度估算）",
                        "P(T)": "学习转移概率（从不会到会的概率）",
                        "P(G)": "猜测概率 = 0.20",
                        "P(S)": "滑落概率 = 0.05"
                    },
                    "mastery_threshold": 0.80
                },

                "通关条件": {
                    "description": "学生需要将本小节所有基础题全部答对",
                    "mastery_target": "知识点掌握概率 >= 80%",
                    "题数计算": f"基于{len(kps)}个知识点，使用BKT模型计算需要{result['adjusted_exercises']}道基础题"
                },

                "calculation_detail": {
                    "raw_total": result["raw_total_exercises"],
                    "adjusted": result["adjusted_exercises"],
                    "min_required": result["min_exercises"],
                    "formula": "基础题数 = max(min_required, ceil(平均题数 * 知识点数 * 覆盖系数))"
                }
            }

            # 生成文件名
            filename = f"第{chapter_order}章第{section_order}节_{section_data['title']}.json"
            filepath = os.path.join(output_dir, filename)

            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(section_config, f, ensure_ascii=False, indent=2)

            print(f"已生成: {filename}")

    # 生成汇总文件
    summary = {
        "course_name": C_COURSE_DATA["course_name"],
        "course_code": C_COURSE_DATA["course_code"],
        "generated_time": "2026-04-21",
        "total_chapters": len(C_COURSE_DATA["chapters"]),
        "total_sections": total_sections,
        "total_knowledge_points": sum(
            len(s["knowledge_points"])
            for ch in C_COURSE_DATA["chapters"]
            for s in ch["sections"]
        ),
        "total_base_questions": total_questions,
        "average_per_section": round(total_questions / total_sections, 1),

        "chapter_summary": [],

        "bkt_model_info": {
            "model": "Bayesian Knowledge Tracing (BKT)",
            "target_mastery": 0.80,
            "通关规则": "每小节所有基础题全部答对，即判定通关"
        }
    }

    # 添加章节汇总
    for chapter_data in C_COURSE_DATA["chapters"]:
        chapter_questions = 0
        section_list = []

        for section_data in chapter_data["sections"]:
            kps = [KnowledgePoint(
                name=kp["name"],
                difficulty=kp["difficulty"],
                importance=kp["importance"]
            ) for kp in section_data["knowledge_points"]]
            result = calculate_section_exercises(kps)
            chapter_questions += result["adjusted_exercises"]

            section_list.append({
                "section_index": section_data["order_index"],
                "section_title": section_data["title"],
                "kp_count": len(kps),
                "base_questions": result["adjusted_exercises"]
            })

        summary["chapter_summary"].append({
            "chapter_index": chapter_data["order_index"],
            "chapter_title": chapter_data["title"],
            "section_count": len(chapter_data["sections"]),
            "total_base_questions": chapter_questions,
            "sections": section_list
        })

    # 保存汇总文件
    summary_path = os.path.join(output_dir, "_汇总表.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("生成完成!")
    print(f"{'='*60}")
    print(f"输出目录: {output_dir}/")
    print(f"总章节数: {len(C_COURSE_DATA['chapters'])}")
    print(f"总小节数: {total_sections}")
    print(f"基础题总数: {total_questions}")
    print(f"平均每小节: {round(total_questions / total_sections, 1)} 题")
    print(f"\n汇总文件: {summary_path}")


if __name__ == "__main__":
    generate_section_files()
