"""本地实测认证考试 code 题：参考实现全过测试用例 + 降级 includes 判定双向校验。

用途：题库质量终审。对每道 code 题：
1. 参考实现 + CERT_CODE_DRIVERS 跑全部 test_cases，必须 100% 通过
   （验证 expected_output 逐字符正确、驱动可运行）
2. 参考实现必须命中 answer_includes 全部片段（降级判定不误杀正确解）
3. 垃圾提交（空 / return 原样 / 固定值）不得命中（降级判定有判别力）

C 题（cert-pointer q5/q6）需要本机 gcc；无 gcc 时跳过实测但仍校验 includes。

运行：cd backend && .venv/Scripts/python -m scripts.verify_cert_local
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.training.seed import CERT_QUESTIONS  # noqa: E402
from app.training.service import CERT_CODE_DRIVERS, judge_cert_answer  # noqa: E402

TIMEOUT_SEC = 8

# 每道 code 题的参考实现（（exam_id, qid) -> 代码）
REFERENCE_SOLUTIONS: dict[tuple[str, str], str] = {
    ("cert-pointer", "q5"): '''void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}''',
    ("cert-pointer", "q6"): '''#include <stdlib.h>
int* find(int *arr, int n) {
    if (arr == NULL || n <= 0) return NULL;
    int *best = arr;
    for (int i = 1; i < n; i++) {
        if (arr[i] > *best) best = &arr[i];
    }
    return best;
}''',
    ("placement", "p4"): '''def first_unique(s):
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    for i, ch in enumerate(s):
        if counts[ch] == 1:
            return i
    return -1''',
    ("placement", "p5"): '''def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0''',
    ("cert-recursion", "q5"): '''def reverse_str(s):
    if len(s) <= 1:
        return s
    return reverse_str(s[1:]) + s[0]''',
    ("cert-recursion", "q6"): '''def power(base, exp):
    if exp == 0:
        return 1
    return base * power(base, exp - 1)''',
    ("cert-sorting", "q5"): '''def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr''',
    ("cert-sorting", "q6"): '''def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr[1:] if x > pivot]
    return quicksort(left) + mid + quicksort(right)''',
    ("cert-linkedlist", "q5"): '''def remove_nth_from_end(arr, n):
    idx = len(arr) - n
    return arr[:idx] + arr[idx + 1:]''',
    ("cert-linkedlist", "q6"): '''def merge_two_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result''',
}

# 垃圾提交：判分必须拒绝
GARBAGE_SUBMISSIONS = [
    "",
    "pass",
    "return None",
]


def run_python(code: str, stdin_text: str) -> tuple[str, str]:
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            input=stdin_text, capture_output=True, text=True,
            timeout=TIMEOUT_SEC, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            err = (proc.stderr or "").strip().splitlines()
            return "", f"error:{err[-1] if err else '非零退出'}"
        return proc.stdout.rstrip("\n"), "ok"
    except subprocess.TimeoutExpired:
        return "", "timeout"
    finally:
        Path(path).unlink(missing_ok=True)


def run_c(code: str, stdin_text: str, workdir: Path) -> tuple[str, str]:
    src = workdir / "prog.c"
    exe = workdir / "prog.exe"
    src.write_text(code, encoding="utf-8")
    comp = subprocess.run(
        ["gcc", "-O1", "-o", str(exe), str(src)],
        capture_output=True, text=True, timeout=60,
    )
    if comp.returncode != 0:
        return "", f"error:编译失败:{(comp.stderr or '').strip().splitlines()[-1]}"
    try:
        proc = subprocess.run(
            [str(exe)], input=stdin_text, capture_output=True, text=True,
            timeout=TIMEOUT_SEC, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            return "", f"error:退出码{proc.returncode}"
        return proc.stdout.rstrip("\n"), "ok"
    except subprocess.TimeoutExpired:
        return "", "timeout"


def main() -> int:
    gcc = shutil.which("gcc")
    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="cert_verify_"))

    code_questions = [q for q in CERT_QUESTIONS if q[2] == "code"]
    for exam_id, qid, _kind, prompt, _opts, _starter, _correct, includes, cases, _s in code_questions:
        key = f"{exam_id}:{qid}"
        print(f"\n=== {key} {prompt[:30]}... ({len(cases)} 用例) ===")
        driver = CERT_CODE_DRIVERS.get(key)
        solution = REFERENCE_SOLUTIONS.get((exam_id, qid))
        if driver is None:
            problems.append(f"{key} 缺少判题驱动")
            continue
        if solution is None:
            problems.append(f"{key} 缺少参考实现")
            continue

        lang = "c" if "#include" in solution or solution.lstrip().startswith("void") else "python"
        if lang == "c" and not gcc:
            print("  [跳过实测] 本机无 gcc")
        else:
            for case in cases:
                full = solution + driver
                if lang == "c":
                    actual, status = run_c(full, case["input"], tmp)
                else:
                    actual, status = run_python(full, case["input"])
                if status != "ok" or actual != case["expected_output"]:
                    problems.append(
                        f"{key} 用例失败: input={case['input']!r} "
                        f"expected={case['expected_output']!r} actual={actual!r} ({status})"
                    )
                    print(f"  FAIL [{status}] input={case['input']!r} actual={actual!r}")
            else:
                print(f"  [参考实现] {len(cases)}/{len(cases)} 通过")

        if not judge_cert_answer("code", solution, None, includes):
            problems.append(f"{key} 参考实现未命中 answer_includes: {includes}")
            print(f"  [includes] 参考实现被误杀: {includes}")
        for garbage in GARBAGE_SUBMISSIONS + ["def f():\n    return 0"]:
            if judge_cert_answer("code", garbage, None, includes):
                problems.append(f"{key} 垃圾提交被判对: {garbage!r}")
                print(f"  [includes] 垃圾提交误判对: {garbage!r}")

    print("\n" + "=" * 50)
    if problems:
        print("发现问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("全部符合预期：参考实现全过、includes 不误杀、垃圾提交被拒")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
