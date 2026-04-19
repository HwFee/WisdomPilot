#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BKT 模型验证脚本

运行方式：
    cd backend
    python scripts/verify_bkt.py

输出：
    1. 模拟学习过程
    2. 比较不同参数
    3. 验证防刷分机制（适配 AI 生成题目）
    4. 展示四层聚合：知识点 → 小节 → 章节 → 课程
"""

import asyncio
import sys
import os

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.bkt import BKTModel, BKTParams, BKTCalculator


def print_header(title: str):
    """打印标题"""
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)


def simulate_learning():
    """模拟学习过程"""
    print_header("模拟学习过程（10道题，80%正确率）")

    model = BKTModel()
    p_l = 0.15

    answers = [True, True, False, True, True, True, True, False, True, True]

    for i, is_correct in enumerate(answers):
        p_l_before = p_l
        p_l, mastered = model.update(p_l, is_correct)

        status = "✓ 正确" if is_correct else "✗ 错误"
        mastered_str = " [掌握!]" if mastered else ""

        print(f"题目 {i+1:2d}: {status} | P(L): {p_l_before:.3f} → {p_l:.3f}{mastered_str}")

    print()
    print(f"最终掌握概率: {p_l:.3f}")
    print(f"答对概率预测: {model.predict_correct_probability(p_l):.3f}")

    return p_l


def compare_params():
    """比较不同 BKT 参数的效果"""
    print_header("比较不同 BKT 参数的效果")

    configs = [
        ("默认参数", BKTParams()),
        ("高学习率 P(T)=0.2", BKTParams(p_t=0.2)),
        ("低学习率 P(T)=0.05", BKTParams(p_t=0.05)),
        ("低猜测率 P(G)=0.1", BKTParams(p_g=0.1)),
        ("高猜测率 P(G)=0.3", BKTParams(p_g=0.3)),
    ]

    print(f"{'配置名称':<25} {'达到掌握所需步数':<15} {'说明'}")
    print("-" * 60)

    for name, params in configs:
        model = BKTModel(params)
        steps = BKTCalculator.estimate_learning_steps(model, 0.15, 0.95)

        if name == "默认参数":
            note = "基准"
        elif "高学习率" in name:
            note = "更快掌握"
        elif "低学习率" in name:
            note = "更慢掌握"
        elif "低猜测率" in name:
            note = "答对更可信"
        else:
            note = "答对可信度低"

        print(f"{name:<25} {steps:<15} {note}")


def verify_anti_gaming():
    """验证防刷分机制"""
    print_header("验证防刷分机制")

    model = BKTModel()
    p_l = 0.15

    print("场景：重复做同一道题10次（无防刷分时的情况）")
    print("-" * 40)

    p_l_values = []
    for i in range(10):
        p_l_before = p_l
        p_l, _ = model.update(p_l, True)
        p_l_values.append((p_l_before, p_l))
        print(f"第 {i+1:2d} 次: P(L) = {p_l_before:.3f} → {p_l:.3f}")

    print()
    print(f"⚠️  警告：如果不防刷分，P(L) 会达到 {p_l:.3f}")
    print("✓  解决方案：每道题只有首次作答计入掌握度")
    print()

    # 演示边际递减效应
    print("增长趋势分析：")
    print("-" * 40)
    for i in range(1, 10):
        gain = p_l_values[i][1] - p_l_values[i-1][1]
        print(f"第 {i} → {i+1} 次: 增长 {gain:.4f}")

    print()
    print("结论：虽然增长在减缓，但仍会无限接近 1.0")
    print("因此必须实现防刷分逻辑（在 BKTMasteryService 中）")


def simulate_realistic_learning():
    """模拟真实学习场景"""
    print_header("模拟真实学习场景")

    # 场景1：新手学习
    print("场景1：新手学习（初始 P(L)=0.1，90%正确率）")
    model = BKTModel()
    p_l = 0.1
    for i in range(10):
        p_l, mastered = model.update(p_l, True if i % 10 != 2 else False)  # 90% 正确率
        if mastered:
            print(f"  第 {i+1} 题达到掌握！P(L) = {p_l:.3f}")
            break
    print(f"  最终 P(L) = {p_l:.3f}")

    # 场景2：有一定基础
    print("\n场景2：有基础的学生（初始 P(L)=0.4，80%正确率）")
    model = BKTModel()
    p_l = 0.4
    pattern = [True, True, False, True, True, True, True, False, True, True]  # 80%
    for i, correct in enumerate(pattern):
        p_l, mastered = model.update(p_l, correct)
        if mastered:
            print(f"  第 {i+1} 题达到掌握！P(L) = {p_l:.3f}")
            break
    print(f"  最终 P(L) = {p_l:.3f}")

    # 场景3：遇到困难
    print("\n场景3：遇到困难（连续答错）")
    model = BKTModel()
    p_l = 0.6  # 已经有一定掌握度
    print(f"  初始 P(L) = {p_l:.3f}")
    for i in range(5):
        p_l, _ = model.update(p_l, False)
        print(f"  答错第 {i+1} 题: P(L) = {p_l:.3f}")
    print(f"  之后答对恢复:")
    for i in range(3):
        p_l, _ = model.update(p_l, True)
        print(f"  答对第 {i+1} 题: P(L) = {p_l:.3f}")


def analyze_question_types():
    """分析不同题型的影响"""
    print_header("不同题型的 BKT 参数（适配实际系统）")

    types = [
        ("选择题 (choice)", "choice"),
        ("填空题 (fill_blank)", "fill_blank"),
        ("填空题别名 (fill)", "fill"),
    ]

    model = BKTModel()

    print(f"{'题型':<25} {'猜测率 P(G)':<15} {'说明'}")
    print("-" * 60)

    for name, q_type in types:
        params = model.get_question_type_params(q_type)
        note = "猜测率高，需要更多答对来确认掌握" if params.p_g > 0.2 else "猜测率低，答对更可信"
        print(f"{name:<25} {params.p_g:<15.2f} {note}")


def analyze_difficulty():
    """分析难度影响"""
    print_header("难度对 BKT 参数的影响（1-3 级）")

    model = BKTModel()

    print(f"{'难度等级':<10} {'猜测率 P(G)':<15} {'学习率 P(T)':<15}")
    print("-" * 50)

    for diff in range(1, 4):  # 实际系统是 1-3 级
        params = model.get_difficulty_adjusted_params(diff)
        print(f"{diff:<10} {params.p_g:<15.3f} {params.p_t:<15.3f}")

    print()
    print("说明：")
    print("- 难题：猜测率更高（可能碰运气），学习率更高（做对学到更多）")
    print("- 简单题：猜测率更低，学习率更低")


def demonstrate_four_layer_aggregation():
    """演示四层聚合：知识点 → 小节 → 章节 → 课程"""
    print_header("四层聚合演示（知识点 → 小节 → 章节 → 课程）")

    model = BKTModel()

    print("假设场景：")
    print("- 课程：C语言程序设计")
    print("- 章节1：基本语法（3个小节）")
    print("- 小节1.1：变量与数据类型（3个知识点）")
    print()

    # 模拟知识点掌握度
    knowledge_points = {
        "int类型": 0.85,
        "float类型": 0.70,
        "char类型": 0.95,
    }

    print("【第一层：知识点掌握度】")
    print("-" * 40)
    for kp, p_l in knowledge_points.items():
        status = "✓ 已掌握" if p_l >= 0.95 else "学习中"
        print(f"  {kp}: P(L) = {p_l:.2f} {status}")

    # 计算小节掌握度
    section_p_l = sum(knowledge_points.values()) / len(knowledge_points)
    mastered_count = sum(1 for p_l in knowledge_points.values() if p_l >= 0.95)

    print()
    print("【第二层：小节掌握度】")
    print("-" * 40)
    print(f"  小节1.1 掌握度 = AVG(知识点) = {section_p_l:.2f}")
    print(f"  已掌握知识点: {mastered_count}/{len(knowledge_points)}")
    print(f"  小节状态: {'✓ 已完成' if mastered_count == len(knowledge_points) else '学习中'}")

    # 假设其他小节
    sections = [section_p_l, 0.60, 0.45]
    chapter_p_l = sum(sections) / len(sections)
    completed_sections = sum(1 for s in sections if s >= 0.95)

    print()
    print("【第三层：章节掌握度】")
    print("-" * 40)
    print(f"  小节1.1: P(L) = {sections[0]:.2f}")
    print(f"  小节1.2: P(L) = {sections[1]:.2f}")
    print(f"  小节1.3: P(L) = {sections[2]:.2f}")
    print(f"  章节掌握度 = AVG(小节) = {chapter_p_l:.2f}")
    print(f"  已完成小节: {completed_sections}/{len(sections)}")

    # 假设其他章节
    chapters = [chapter_p_l, 0.30, 0.15, 0.10, 0.10]
    course_p_l = sum(chapters) / len(chapters)
    completed_chapters = sum(1 for c in chapters if c >= 0.95)

    print()
    print("【第四层：课程掌握度】")
    print("-" * 40)
    print(f"  章节1 掌握度: {chapters[0]:.2f}")
    print(f"  章节2 掌握度: {chapters[1]:.2f}")
    print(f"  章节3-5 掌握度: {chapters[2]:.2f}, {chapters[3]:.2f}, {chapters[4]:.2f}")
    print(f"  课程掌握度 = AVG(章节) = {course_p_l:.2f}")
    print(f"  已完成章节: {completed_chapters}/{len(chapters)}")
    print()
    print("聚合公式：")
    print("  知识点: BKT实时计算 P(L)")
    print("  小节: AVG(知识点 P(L))")
    print("  章节: AVG(小节 P(L))")
    print("  课程: AVG(章节 P(L))")


def main():
    """主函数"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " BKT (Bayesian Knowledge Tracing) 模型验证 ".center(58) + "║")
    print("║" + " 四层聚合：知识点 → 小节 → 章节 → 课程 ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    simulate_learning()
    compare_params()
    verify_anti_gaming()
    simulate_realistic_learning()
    analyze_question_types()
    analyze_difficulty()
    demonstrate_four_layer_aggregation()

    print()
    print("=" * 60)
    print(" 验证完成")
    print("=" * 60)
    print()
    print("关键发现：")
    print("1. BKT 模型能有效追踪学习过程，答对增加掌握概率，答错降低")
    print("2. 题型参数：选择题 P(G)=0.25，填空题 P(G)=0.15")
    print("3. 难度 1-3 级，影响猜测率和学习率")
    print("4. 防刷分机制：答题时间检测 + 小节/小时限制")
    print("5. 四层聚合：知识点 → 小节 → 章节 → 课程")
    print("6. 掌握阈值 P(L) >= 0.95")
    print()


if __name__ == "__main__":
    main()
