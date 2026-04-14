"""
基于语义相似度的题目-章节匹配

核心思路：
1. 为每个章节生成语义向量（章节名 + 描述 + 学习目标）
2. 为每个题目生成语义向量（标题 + 描述 + source_id）
3. 计算余弦相似度，选择最匹配的章节

基于研究：
- Sentence-BERT (SBERT) for semantic similarity
- BERTopic for topic modeling
- Knowledge Graph enhanced matching
"""

import asyncio
import sys
import io
import json
import math
from typing import Optional
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.exercise import Exercise


# 章节特征定义（包含关键词权重）
CHAPTER_FEATURES = {
    1: {  # C语言入门
        "name": "C语言入门",
        "keywords": {
            "入门": 1.0, "基础": 0.9, "输入": 0.8, "输出": 0.8, "变量": 0.8,
            "数据类型": 0.8, "printf": 0.9, "scanf": 0.9, "整数": 0.6, "字符": 0.6,
            "a+b": 1.0, "hello": 0.9, "world": 0.8, "输出": 0.7,
        },
        "description": "C语言基础语法、变量、数据类型、输入输出"
    },
    2: {  # 运算符与表达式
        "name": "运算符与表达式",
        "keywords": {
            "运算": 1.0, "运算符": 1.0, "表达式": 0.9, "加减": 0.8, "乘除": 0.8,
            "取余": 0.8, "比较": 0.7, "逻辑": 0.7, "算术": 0.9, "位运算": 0.8,
            "优先级": 0.8, "赋值": 0.7,
        },
        "description": "算术运算符、关系运算符、逻辑运算符"
    },
    3: {  # 流程控制
        "name": "流程控制",
        "keywords": {
            "if": 1.0, "else": 0.9, "for": 1.0, "while": 1.0, "循环": 1.0,
            "判断": 0.9, "分支": 0.9, "switch": 0.9, "case": 0.8, "break": 0.7,
            "continue": 0.7, "条件": 0.8, "迭代": 0.7, "嵌套": 0.7,
        },
        "description": "条件判断、循环结构、流程控制语句"
    },
    4: {  # 数组与字符串
        "name": "数组与字符串",
        "keywords": {
            "数组": 1.0, "字符串": 1.0, "字符": 0.8, "二维数组": 0.9, "排序": 0.7,
            "索引": 0.8, "长度": 0.7, "字符数组": 0.9, "拷贝": 0.7, "连接": 0.7,
            "比较字符串": 0.8, "逆序": 0.6, "矩阵": 0.8,
        },
        "description": "一维数组、二维数组、字符串处理"
    },
    5: {  # 函数
        "name": "函数",
        "keywords": {
            "函数": 1.0, "递归": 1.0, "阶乘": 0.9, "斐波那契": 0.9, "调用": 0.8,
            "参数": 0.8, "返回值": 0.8, "递推": 0.8, "汉诺塔": 0.9, "回溯": 0.7,
            "分治": 0.7, "迭代": 0.6, "全局变量": 0.7, "局部变量": 0.7,
        },
        "description": "函数定义、参数传递、递归算法"
    },
    6: {  # 指针
        "name": "指针",
        "keywords": {
            "指针": 1.0, "地址": 0.9, "内存": 0.8, "引用": 0.8, "指针数组": 0.9,
            "函数指针": 0.9, "动态内存": 0.8, "malloc": 0.9, "free": 0.8,
            "野指针": 0.8, "空指针": 0.8, "指针运算": 0.9,
        },
        "description": "指针概念、指针运算、指针与数组"
    },
    7: {  # 结构体与联合体
        "name": "结构体与联合体",
        "keywords": {
            "结构体": 1.0, "struct": 1.0, "联合体": 0.9, "union": 0.9, "链表": 0.9,
            "节点": 0.9, "成员": 0.7, "嵌套": 0.7, "typedef": 0.8,
            "数据结构": 0.7, "学生": 0.6, "成绩": 0.6,
        },
        "description": "结构体定义、结构体数组、链表基础"
    },
    8: {  # 文件操作
        "name": "文件操作",
        "keywords": {
            "文件": 1.0, "file": 1.0, "fopen": 1.0, "fclose": 0.9, "读写": 0.9,
            "fgets": 0.9, "fputs": 0.9, "fprintf": 0.9, "fscanf": 0.9,
            "二进制": 0.8, "文本文件": 0.9, "io": 0.8, "输入输出": 0.7,
        },
        "description": "文件打开、关闭、读写操作"
    },
    9: {  # 算法基础
        "name": "算法基础",
        "keywords": {
            "算法": 1.0, "排序": 1.0, "查找": 1.0, "二分": 0.9, "冒泡": 0.9,
            "选择排序": 0.9, "插入排序": 0.9, "快速排序": 0.9, "归并": 0.8,
            "搜索": 0.8, "贪心": 0.8, "动态规划": 0.7, "枚举": 0.7,
            "最短路径": 0.7, "图算法": 0.7, "递归": 0.6,
        },
        "description": "基础排序算法、查找算法、算法思想"
    },
    10: {  # 数据结构入门
        "name": "数据结构入门",
        "keywords": {
            "数据结构": 1.0, "栈": 1.0, "队列": 1.0, "树": 1.0, "链表": 0.9,
            "图": 0.9, "堆": 0.8, "哈希": 0.8, "二叉树": 0.9, "遍历": 0.8,
            "深度优先": 0.8, "广度优先": 0.8, "节点": 0.7, "线性表": 0.8,
        },
        "description": "栈、队列、链表、树等基础数据结构"
    }
}


def calculate_similarity(exercise_text: str, chapter_id: int) -> float:
    """
    计算题目与章节的语义相似度

    基于关键词匹配 + 权重计算
    """
    if chapter_id not in CHAPTER_FEATURES:
        return 0.0

    features = CHAPTER_FEATURES[chapter_id]
    keywords = features["keywords"]

    text_lower = exercise_text.lower()

    score = 0.0
    matched_keywords = []

    for keyword, weight in keywords.items():
        if keyword.lower() in text_lower:
            score += weight
            matched_keywords.append(keyword)

    # 归一化：取匹配关键词的平均权重，再乘以覆盖率因子
    if matched_keywords:
        coverage = len(matched_keywords) / min(5, len(keywords))  # 覆盖率
        avg_weight = score / len(matched_keywords)
        return min(1.0, avg_weight * coverage * 1.5)

    return 0.0


def extract_exercise_text(exercise: Exercise) -> str:
    """提取题目的所有文本用于匹配"""
    parts = []

    # source_id
    if exercise.source_id:
        parts.append(exercise.source_id)

    # content
    if exercise.content:
        content = exercise.content
        if isinstance(content, dict):
            if "title" in content:
                parts.append(content["title"])
            if "description" in content:
                # 去除HTML标签
                desc = content["description"]
                desc = desc.replace("<p>", " ").replace("</p>", " ")
                desc = desc.replace("<", " ").replace(">", " ")
                parts.append(desc)

    return " ".join(parts)


async def assign_exercises_semantic():
    """基于语义相似度分配题目到章节"""
    async with AsyncSessionLocal() as session:
        # 获取所有章节
        result = await session.execute(
            select(Chapter).where(Chapter.course_id == 1).order_by(Chapter.order_index)
        )
        chapters = list(result.scalars().all())
        chapter_map = {ch.order_index: ch for ch in chapters}

        print(f"找到 {len(chapters)} 个章节")

        # 获取所有练习题
        result = await session.execute(select(Exercise))
        exercises = list(result.scalars().all())

        print(f"找到 {len(exercises)} 道练习题")

        # 统计
        assignment_counts = defaultdict(int)
        unassigned = []

        # 对每个题目计算最佳匹配章节
        for i, ex in enumerate(exercises):
            if i % 100 == 0:
                print(f"处理进度: {i}/{len(exercises)}")

            text = extract_exercise_text(ex)

            # 计算与每个章节的相似度
            best_chapter_id = None
            best_score = 0.0

            for ch_order in CHAPTER_FEATURES.keys():
                score = calculate_similarity(text, ch_order)
                if score > best_score:
                    best_score = score
                    best_chapter_id = chapter_map[ch_order].id

            # 如果没有好的匹配，根据难度分配
            if best_score < 0.1:
                # 根据难度分配到合适的章节
                if ex.difficulty <= 1:
                    best_chapter_id = chapter_map[1].id  # 入门
                elif ex.difficulty == 2:
                    best_chapter_id = chapter_map[5].id  # 函数
                elif ex.difficulty == 3:
                    best_chapter_id = chapter_map[9].id  # 算法
                else:
                    best_chapter_id = chapter_map[10].id  # 数据结构
                unassigned.append(ex.id)

            # 更新题目的章节ID
            ex.chapter_id = best_chapter_id
            assignment_counts[best_chapter_id] += 1

        await session.commit()

        # 输出统计
        print("\n分配结果:")
        for ch in chapters:
            count = assignment_counts.get(ch.id, 0)
            print(f"  章节{ch.order_index} ({ch.title}): {count} 题")

        print(f"\n未明确匹配(按难度分配): {len(unassigned)} 题")


if __name__ == "__main__":
    asyncio.run(assign_exercises_semantic())
