"""
Generate exercise configuration files for C++ and Python courses
Based on BKT model with dynamic exercise count calculation
"""

import json
import os
import math
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class BKTParams:
    p_l0: float
    p_t: float
    p_g: float
    p_s: float


@dataclass
class KnowledgePoint:
    name: str
    difficulty: int
    importance: int


def get_bkt_params(difficulty: int, importance: int) -> BKTParams:
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
    return p_l * (1 - params.p_s) + (1 - p_l) * params.p_g


def update_mastery(p_l: float, is_correct: bool, params: BKTParams) -> float:
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
    target_mastery: float = 0.90,
    max_exercises: int = 20,
    min_exercises: int = 2
) -> Dict[str, Any]:
    p_l = params.p_l0
    exercises_needed = 0

    while p_l < target_mastery and exercises_needed < max_exercises:
        exercises_needed += 1
        p_l = update_mastery(p_l, True, params)

    exercises_needed = max(min_exercises, exercises_needed)

    return {
        "exercises_needed": exercises_needed,
        "initial_mastery": params.p_l0,
        "final_mastery": p_l,
        "target_mastery": target_mastery
    }


def calculate_section_exercises(
    knowledge_points: List[KnowledgePoint],
    target_mastery: float = 0.90,
    coverage_ratio: float = 0.8
) -> Dict[str, Any]:
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


def generate_exercise_config(course_data: Dict, output_dir: str):
    """Generate exercise configuration files for a course"""

    total_sections = 0
    total_questions = 0
    kp_id_counter = 1

    all_kps = []

    for chapter_data in course_data["chapters"]:
        chapter_order = chapter_data["order_index"]
        chapter_title = chapter_data["title"]

        for section_data in chapter_data["sections"]:
            total_sections += 1
            section_order = section_data["order_index"]
            section_title = section_data["title"]

            kps = [
                KnowledgePoint(
                    name=kp["name"],
                    difficulty=kp["difficulty"],
                    importance=kp["importance"]
                )
                for kp in section_data["knowledge_points"]
            ]

            result = calculate_section_exercises(kps)
            total_questions += result["adjusted_exercises"]

            section_kp_list = []
            for kp_detail in result["kp_details"]:
                kp_id = kp_id_counter
                kp_id_counter += 1
                all_kps.append({
                    "chapter_id": chapter_order,
                    "chapter_title": chapter_title,
                    "section_id": section_order,
                    "section_title": section_title,
                    "kp_id": kp_id,
                    "kp_name": kp_detail["name"]
                })
                section_kp_list.append({
                    "id": kp_id,
                    "name": kp_detail["name"]
                })

            exercises = generate_exercises_for_section(
                section_kp_list,
                result["adjusted_exercises"]
            )

            kp_coverage = {}
            for ex in exercises:
                for kp_id in ex["knowledge_points"]:
                    kp_coverage[str(kp_id)] = kp_coverage.get(str(kp_id), 0) + 1

            config = {
                "chapter_id": chapter_order,
                "chapter_title": chapter_title,
                "section_id": section_order,
                "section_title": section_title,
                "total_knowledge_points": len(section_kp_list),
                "total_exercises": len(exercises),
                "knowledge_point_coverage": kp_coverage,
                "knowledge_points": section_kp_list,
                "exercises": exercises
            }

            filename = f"第{chapter_order}章第{section_order}节_{section_title}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print(f"已生成: {filename} - {len(section_kp_list)}个知识点, {len(exercises)}道题")

    return total_sections, total_questions, kp_id_counter - 1


def generate_exercises_for_section(kp_list: List[Dict], target_count: int) -> List[Dict]:
    """Generate exercise configurations for a section based on BKT strategy"""

    num_kps = len(kp_list)
    exercises = []

    if num_kps <= 3:
        for i, kp in enumerate(kp_list):
            exercises.append({
                "exercise_number": i + 1,
                "knowledge_points": [kp["id"]],
                "knowledge_point_names": [kp["name"]],
                "description": f"考察知识点：{kp['name']}",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })
        for i, kp in enumerate(kp_list):
            exercises.append({
                "exercise_number": len(exercises) + 1,
                "knowledge_points": [kp["id"]],
                "knowledge_point_names": [kp["name"]],
                "description": f"考察知识点：{kp['name']}（进阶）",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })

    elif num_kps <= 6:
        group_size = 2
        ex_num = 1
        for i in range(0, num_kps, group_size):
            group = kp_list[i:i+group_size]
            kp_ids = [g["id"] for g in group]
            kp_names = [g["name"] for g in group]
            exercises.append({
                "exercise_number": ex_num,
                "knowledge_points": kp_ids,
                "knowledge_point_names": kp_names,
                "description": f"考察知识点：{'、'.join(kp_names)}",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })
            ex_num += 1

        for i in range(0, num_kps, group_size):
            group = kp_list[i:i+group_size]
            kp_ids = [g["id"] for g in group]
            kp_names = [g["name"] for g in group]
            exercises.append({
                "exercise_number": ex_num,
                "knowledge_points": kp_ids,
                "knowledge_point_names": kp_names,
                "description": f"考察知识点：{'、'.join(kp_names)}（进阶）",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })
            ex_num += 1

    else:
        group_size = 3
        ex_num = 1

        for i in range(0, num_kps, group_size):
            group = kp_list[i:i+group_size]
            kp_ids = [g["id"] for g in group]
            kp_names = [g["name"] for g in group]
            exercises.append({
                "exercise_number": ex_num,
                "knowledge_points": kp_ids,
                "knowledge_point_names": kp_names,
                "description": f"考察知识点：{'、'.join(kp_names)}",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })
            ex_num += 1

        offset = group_size // 2 + 1
        for i in range(0, num_kps, group_size):
            start = (i + offset) % num_kps
            end = start + group_size
            if end <= num_kps:
                group = kp_list[start:end]
            else:
                indices = list(range(start, num_kps)) + list(range(0, end - num_kps))
                group = [kp_list[j] for j in indices]

            kp_ids = [g["id"] for g in group]
            kp_names = [g["name"] for g in group]
            exercises.append({
                "exercise_number": ex_num,
                "knowledge_points": kp_ids,
                "knowledge_point_names": kp_names,
                "description": f"考察知识点：{'、'.join(kp_names)}（进阶）",
                "bkt_params": {
                    "p_l0": 0.3,
                    "p_t": 0.15,
                    "p_g": 0.2,
                    "p_s": 0.05
                }
            })
            ex_num += 1

    exercises = exercises[:10]

    return exercises


def generate_summary(course_data: Dict, output_dir: str, total_sections: int, total_questions: int, total_kps: int):
    """Generate summary file for the course"""

    summary = {
        "course_name": course_data["course_name"],
        "course_code": course_data["course_code"],
        "generated_time": "2026-04-22",
        "total_chapters": len(course_data["chapters"]),
        "total_sections": total_sections,
        "total_knowledge_points": total_kps,
        "total_base_questions": total_questions,
        "average_per_section": round(total_questions / total_sections, 1),
        "chapter_summary": [],
        "bkt_model_info": {
            "model": "Bayesian Knowledge Tracing (BKT)",
            "target_mastery": 0.90,
            "通关规则": "每小节所有基础题全部答对，即判定通关"
        }
    }

    for chapter_data in course_data["chapters"]:
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

    summary_path = os.path.join(output_dir, "_汇总表.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n汇总文件已生成: {summary_path}")


def main():
    base_dir = r"C:\Users\17445\Desktop\AIcodiingT eachdemo"

    courses = [
        ("C++程序设计习题配置", "C++程序设计习题配置\\course_data.json", "C++程序设计习题配置"),
        ("Python程序设计习题配置", "Python程序设计习题配置\\course_data.json", "Python程序设计习题配置")
    ]

    for course_name, course_data_path, output_dir in courses:
        print(f"\n{'='*60}")
        print(f"正在生成: {course_name}")
        print(f"{'='*60}")

        course_data_file = os.path.join(base_dir, course_data_path)
        with open(course_data_file, 'r', encoding='utf-8') as f:
            course_data = json.load(f)

        output_path = os.path.join(base_dir, output_dir)
        os.makedirs(output_path, exist_ok=True)

        total_sections, total_questions, total_kps = generate_exercise_config(
            course_data,
            output_path
        )

        generate_summary(course_data, output_path, total_sections, total_questions, total_kps)

        print(f"\n{course_name} 完成!")
        print(f"  总章节数: {len(course_data['chapters'])}")
        print(f"  总小节数: {total_sections}")
        print(f"  总知识点数: {total_kps}")
        print(f"  基础题总数: {total_questions}")
        print(f"  平均每小节: {round(total_questions / total_sections, 1)} 题")

    print(f"\n{'='*60}")
    print("所有课程习题配置生成完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()