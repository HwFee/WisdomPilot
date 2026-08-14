"""审查关卡机械校验：defect_count 一致性、行号范围、缺陷行内容非空。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.training.seed import REVIEW_SESSIONS, ARENA_CHALLENGES, CERT_QUESTIONS, KNOWLEDGE_POINTS

problems = []
kp_names = {name for name, *_ in KNOWLEDGE_POINTS}

for s in REVIEW_SESSIONS:
    lines = s["code"].splitlines()
    n = len(lines)
    if s["defect_count"] != len(s["defects"]):
        problems.append(f"{s['id']}: defect_count={s['defect_count']} != len(defects)={len(s['defects'])}")
    if s["related_weakness"] not in kp_names:
        problems.append(f"{s['id']}: related_weakness {s['related_weakness']!r} 不在 KNOWLEDGE_POINTS")
    seen_lines = set()
    for line, dtype, expl in s["defects"]:
        if not (1 <= line <= n):
            problems.append(f"{s['id']}: 缺陷行号 {line} 超出代码范围 1..{n}")
        elif not lines[line - 1].strip():
            problems.append(f"{s['id']}: 缺陷行 {line} 是空行")
        if line in seen_lines:
            problems.append(f"{s['id']}: 缺陷行号 {line} 重复")
        seen_lines.add(line)
        if dtype not in ("boundary", "logic", "security", "performance", "style"):
            problems.append(f"{s['id']}:{line} 未知缺陷类型 {dtype!r}")
        if not expl.strip():
            problems.append(f"{s['id']}:{line} 缺陷解释为空")

for c in ARENA_CHALLENGES:
    if c.get("related_weakness") not in kp_names:
        problems.append(f"{c['id']}: related_weakness {c.get('related_weakness')!r} 不在 KNOWLEDGE_POINTS")
    if not c["test_cases"]:
        problems.append(f"{c['id']}: 无测试用例")
    if not (1 <= c["difficulty"] <= 5):
        problems.append(f"{c['id']}: 难度 {c['difficulty']} 超范围")

mcq_ids = [(e, q) for e, q, k, *_ in CERT_QUESTIONS if k == "mcq"]
for exam_id, qid, kind, prompt, options, starter, correct, includes, cases, sort_order in CERT_QUESTIONS:
    if kind == "mcq":
        if correct not in options:
            problems.append(f"{exam_id}:{qid} 正确答案不在选项中: {correct!r}")
        if len(set(options)) != len(options):
            problems.append(f"{exam_id}:{qid} 选项有重复")
    else:
        if not cases:
            problems.append(f"{exam_id}:{qid} code 题无测试用例")
        if not includes:
            problems.append(f"{exam_id}:{qid} code 题无 answer_includes")

print(f"审查关卡 {len(REVIEW_SESSIONS)} 个，缺陷 {sum(len(s['defects']) for s in REVIEW_SESSIONS)} 处")
print(f"竞技场挑战 {len(ARENA_CHALLENGES)} 个，认证题 {len(CERT_QUESTIONS)} 道"
      f"（MCQ {len(mcq_ids)} / code {len(CERT_QUESTIONS) - len(mcq_ids)}）")
if problems:
    print("\n发现问题：")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print("机械校验全部通过")
