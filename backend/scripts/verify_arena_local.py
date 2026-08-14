"""本地实测竞技场挑战：缺陷代码在测试用例上的真实表现 + 修复版全过验证。

用途：题库质量终审。对 language == "python" 的挑战：
1. 用缺陷代码 + 判题驱动跑全部 test_cases，记录每用例 通过/失败/超时/异常
2. 用 REFERENCE_FIXES 里的参考修复实现跑全部 test_cases，必须 100% 通过
   （同时验证 expected_output 逐字符正确）

C 语言挑战（0093/0102/0109）若本机有 gcc 则同样实测，否则跳过并提示。

运行：cd backend && .venv/Scripts/python -m scripts.verify_arena_local
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.training.seed import ARENA_CHALLENGES  # noqa: E402
from app.training.service import ARENA_DRIVERS  # noqa: E402

TIMEOUT_SEC = 8

# 每个挑战的参考修复实现（函数体替换缺陷代码中的对应函数）
REFERENCE_FIXES: dict[str, str] = {
    "DEBUG-0091": '''def median(nums):
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    lo = mid - 1
    return (nums[lo] + nums[mid]) / 2''',
    "DEBUG-0092": '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1''',
    "DEBUG-0094": '''def count_unique(words):
    seen = set()
    count = 0
    for w in words:
        if w not in seen:
            seen.add(w)
            count += 1
    return count''',
    "DEBUG-0095": '''def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)''',
    "DEBUG-0096": '''def rotate(nums, k):
    n = len(nums)
    k = k % n
    return nums[-k:] + nums[:-k]''',
    "DEBUG-0097": '''def most_frequent(s):
    counts = {}
    for ch in s:
        if ch in counts:
            counts[ch] += 1
        else:
            counts[ch] = 1
    return max(counts, key=counts.get)''',
    "DEBUG-0098": '''def is_balanced(s):
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack:
                return False
            if stack.pop() == pairs[ch]:
                continue
            return False
    return len(stack) == 0''',
    "DEBUG-0099": '''def max_subarray(nums):
    cur = nums[0]
    best = nums[0]
    for x in nums[1:]:
        cur = max(cur + x, x)
        if cur > best:
            best = cur
    return best''',
    "DEBUG-0100": '''def compress(s):
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(s[i - 1] + str(count))
            count = 1
    result.append(s[len(s) - 1] + str(count))
    return "".join(result)''',
    "DEBUG-0101": '''def is_palindrome(s):
    cleaned = "".join(ch.lower() for ch in s if ch.isalnum())
    return cleaned == cleaned[::-1]''',
    "DEBUG-0103": '''def move_zeros(nums):
    n = len(nums)
    idx = 0
    for i in range(n):
        if nums[i] != 0:
            nums[idx] = nums[i]
            idx += 1
    while idx < n:
        nums[idx] = 0
        idx += 1
    return nums''',
    "DEBUG-0104": '''def str_to_int(s):
    s = s.strip()
    if not s:
        return 0
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
    elif s[0] == "+":
        s = s[1:]
    num = 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        else:
            break
    return sign * num''',
    "DEBUG-0105": '''def transpose(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    result = [[0] * rows for _ in range(cols)]
    for i in range(rows):
        for j in range(cols):
            result[j][i] = matrix[i][j]
    return result''',
    "DEBUG-0106": '''def josephus(n, k):
    people = list(range(1, n + 1))
    idx = 0
    while len(people) > 1:
        idx = (idx + k - 1) % len(people)
        people.pop(idx)
    return people[0]''',
    "DEBUG-0107": '''def first_missing_positive(nums):
    n = len(nums)
    present = [False] * (n + 1)
    for x in nums:
        if 1 <= x <= n:
            present[x] = True
    for i in range(1, n + 1):
        if not present[i]:
            return i
    return n + 1''',
    "DEBUG-0108": '''def is_happy(n):
    seen = set()
    while n != 1:
        if n in seen:
            return False
        seen.add(n)
        n = sum(int(d) ** 2 for d in str(n))
    return True''',
    "DEBUG-0110": '''def reverse_words(s):
    words = s.split()
    return " ".join(reversed(words))''',
}

# C 挑战的参考修复（完整函数替换）
C_FIXES: dict[str, str] = {
    "DEBUG-0093": '''#include <stdlib.h>
#include <string.h>

char* reverse_str(char *s) {
    int len = strlen(s);
    char *result = malloc(len + 1);
    char *dest = result;
    char *src = s + len - 1;
    while (src >= s) {
        *dest++ = *src--;
    }
    *dest = '\\0';
    return result;
}''',
    "DEBUG-0102": '''#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* reverse(Node *head) {
    Node *prev = NULL;
    Node *cur = head;
    while (cur) {
        Node *next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}''',
    "DEBUG-0109": '''#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* middle_node(Node *head) {
    Node *slow = head;
    Node *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}''',
}


def run_python(code: str, stdin_text: str) -> tuple[str, str]:
    """跑一段完整 python 程序，返回 (stdout_stripped, status)。

    status: ok / wrong / timeout / error:<msg>
    """
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
            encoding="utf-8",
            errors="replace",
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
    tmp = Path(tempfile.mkdtemp(prefix="arena_verify_"))

    for ch in ARENA_CHALLENGES:
        cid = ch["id"]
        lang = ch["language"]
        cases = ch["test_cases"]
        driver = ARENA_DRIVERS.get(cid, "")
        print(f"\n=== {cid} {ch['title']} ({lang}, {len(cases)} 用例) ===")

        if lang == "c" and not gcc:
            print("  [跳过] 本机无 gcc，C 挑战未实测")
            continue

        for label, code in (("缺陷", ch["code"]), ("修复", None)):
            if label == "修复":
                code = REFERENCE_FIXES.get(cid) if lang == "python" else C_FIXES.get(cid)
                if code is None:
                    continue
            full = code + driver
            results = []
            for case in cases:
                if lang == "python":
                    actual, status = run_python(full, case["input"])
                else:
                    actual, status = run_c(full, case["input"], tmp)
                expected = case["expected_output"]
                ok = status == "ok" and actual == expected
                results.append((ok, status, case["input"], expected, actual))
            passed = sum(1 for r in results if r[0])
            print(f"  [{label}版] {passed}/{len(cases)} 通过")
            for ok, status, inp, exp, act in results:
                mark = "PASS" if ok else "FAIL"
                print(f"    {mark} [{status}] input={inp!r} expected={exp!r} actual={act!r}")
            if label == "修复" and passed != len(cases):
                problems.append(f"{cid} 修复版未全过 ({passed}/{len(cases)})")
            if label == "缺陷" and passed == len(cases):
                problems.append(f"{cid} 缺陷版竟然全过")

    print("\n" + "=" * 50)
    if problems:
        print("发现问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("全部符合预期：缺陷版均失败、修复版均全过、期望输出逐字符一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
