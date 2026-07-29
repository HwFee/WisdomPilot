# ──────────────────────────────────────────────────────────────────
# 训练舱种子数据模块（seed.py）
# ──────────────────────────────────────────────────────────────────
# 本文件负责在数据库首次初始化时灌入训练舱的种子数据（seed data）。
#
# 种子数据是"硬编码在代码中的基础内容"——不需要管理后台，直接由代码
# 定义并导入数据库。适合场景：核心内容相对稳定、数量不多、与代码逻辑
# 紧密耦合。
#
# 种子内容包括四个部分：
#   1. 知识点（KNOWLEDGE_POINTS）       —— 13 个核心知识点 + 费曼评分要点
#   2. 代码审查关卡（REVIEW_SESSIONS）  —— 2 个关卡 + 注入缺陷
#   3. 调试竞技场挑战（ARENA_CHALLENGES）—— 1 个挑战
#   4. 认证考试（CERT_EXAMS + CERT_QUESTIONS）—— 2 场考试 + 11 道题目
#
# 幂等性设计：
#   seed_deck() 函数在执行前会检查知识点表是否已有数据——如果有则跳过。
#   这意味着可以安全地重复调用（如多次启动服务），不会产生重复数据。
#   添加新种子数据后，需要清空旧数据或手动 INSERT 才能生效。
#
# 注意事项：
#   - SQLite 在每条语句执行时即时检查外键约束（不同于 MySQL 在事务提交
#     时检查），所以父表必须先于子表插入，中途需要 await db.flush()。
#   - 注入缺陷（DeckInjectedDefect）是"服务端秘密"——前端可以看到
#     defect_count（告诉用户有 N 个 bug），但不会收到具体行号和解释。
# ──────────────────────────────────────────────────────────────────

"""训练舱种子数据：知识点、审查关卡、竞技场挑战、认证考试。

幂等：knowledge_points 非空则跳过（可重复执行）。
"""

# func：SQL 聚合函数（如 count），用于幂等性检查
# select：构建 SELECT 语句
from sqlalchemy import func, select
# AsyncSession：SQLAlchemy 的异步数据库会话，seed_deck 需要通过它操作数据库
from sqlalchemy.ext.asyncio import AsyncSession

# 导入需要灌入数据的模型类
from app.training.models import (
    DeckArenaChallenge,   # 调试竞技场挑战
    DeckCertExam,         # 认证考试定义
    DeckCertQuestion,     # 认证考试题目
    DeckInjectedDefect,   # 注入缺陷（子表，依赖于 DeckReviewSession）
    DeckKnowledgePoint,   # 知识点（首先检查幂等）
    DeckReviewSession,    # 代码审查关卡（父表，DeckInjectedDefect 依赖它）
)

# ──────────────────────────────────────────────────────────────────
# 知识点列表（13 个核心知识点）
# ──────────────────────────────────────────────────────────────────
# 数据结构：(name, category, axis, key_points)
#   name:       知识点名称（全局唯一）
#   category:   分类标签（如"数据结构 · 排序"），用于前端分组展示
#   axis:       能力轴（review=代码审查 / debug=调试排错 / implement=编码实现）
#   key_points: 费曼检验评分要点列表，每项为 {"keys": [同义词], "label": 要点名}
#               用户讲述时命中任一同义词即算覆盖该要点
#
# 知识点覆盖三个轴的均衡分布：
#   review 轴（4 个）：边界条件、并发审阅、坏味道识别、安全漏洞
#   debug 轴（4 个）：指针内存、调用帧、断点策略、日志定位
#   implement 轴（5 个）：递归出口、DP 状态设计、链表操作、排序实现、字符串处理
# ──────────────────────────────────────────────────────────────────

KNOWLEDGE_POINTS = [
    # (name, category, axis, key_points) —— key_points 是费曼检验评分要点：
    # {"keys": [同义词...], "label": 要点名}，讲述命中任一同义词即算覆盖
    ("边界条件处理", "数据结构 · 排序", "review", [
        {"keys": ["空", "空列表", "空数组"], "label": "空输入"},
        {"keys": ["单个", "一个元素", "单元素"], "label": "单元素"},
        {"keys": ["重复", "相同元素", "相等"], "label": "重复元素"},
        {"keys": ["越界", "arr[n]", "i < n", "边界"], "label": "循环边界"},
        {"keys": ["最大", "最小", "溢出", "极端值"], "label": "极值输入"},
    ]),
    ("并发代码审阅", "通用 · 并发", "review", [
        {"keys": ["竞态", "race", "竞争"], "label": "竞态条件"},
        {"keys": ["锁", "互斥", "mutex"], "label": "互斥保护"},
        {"keys": ["死锁", "deadlock"], "label": "死锁"},
        {"keys": ["原子", "atomic"], "label": "原子性"},
        {"keys": ["共享", "共享变量", "共享状态"], "label": "共享状态"},
    ]),
    ("坏味道识别", "工程 · 重构", "review", [
        {"keys": ["重复代码", "复制粘贴", "重复"], "label": "重复代码"},
        {"keys": ["过长", "太长", "大函数"], "label": "过长函数"},
        {"keys": ["魔法数", "magic", "硬编码"], "label": "魔法数字"},
        {"keys": ["命名", "名字", "含义不清"], "label": "糟糕命名"},
        {"keys": ["嵌套", "缩进太深"], "label": "深层嵌套"},
    ]),
    ("安全漏洞模式", "安全 · 注入", "review", [
        {"keys": ["注入", "injection", "SQL"], "label": "注入攻击"},
        {"keys": ["拼接", "字符串拼接"], "label": "字符串拼接 SQL"},
        {"keys": ["参数化", "预编译", "占位符"], "label": "参数化查询"},
        {"keys": ["转义", "过滤", "校验输入"], "label": "输入校验"},
        {"keys": ["权限", "越权", "最小权限"], "label": "权限控制"},
    ]),
    ("指针的内存布局", "C 程序设计 · 指针", "debug", [
        {"keys": ["地址", "取地址", "&"], "label": "地址与取地址"},
        {"keys": ["解引用", "*p", "指向的值"], "label": "解引用"},
        {"keys": ["悬空", "野指针", "free"], "label": "悬空指针"},
        {"keys": ["指针运算", "p++", "步长", "字节"], "label": "指针运算步长"},
        {"keys": ["NULL", "空指针"], "label": "空指针"},
    ]),
    ("栈与调用帧", "通用 · 运行时", "debug", [
        {"keys": ["调用栈", "栈帧", "call stack"], "label": "调用栈结构"},
        {"keys": ["返回地址", "压栈", "入栈"], "label": "压栈与返回"},
        {"keys": ["局部变量", "局部"], "label": "局部变量存储"},
        {"keys": ["栈溢出", "overflow", "爆栈"], "label": "栈溢出"},
        {"keys": ["递归", "层数"], "label": "递归深度"},
    ]),
    ("断点与单步策略", "工具 · 调试器", "debug", [
        {"keys": ["断点", "breakpoint"], "label": "断点设置"},
        {"keys": ["条件断点", "条件"], "label": "条件断点"},
        {"keys": ["单步", "step", "步入", "步过"], "label": "单步执行"},
        {"keys": ["观察", "watch", "监视变量"], "label": "变量观察"},
        {"keys": ["二分", "缩小范围", "定位"], "label": "二分定位"},
    ]),
    ("日志定位法", "工具 · 日志", "debug", [
        {"keys": ["日志级别", "级别", "level", "INFO", "ERROR"], "label": "日志级别"},
        {"keys": ["上下文", "关键变量", "现场"], "label": "上下文信息"},
        {"keys": ["时间戳", "时间"], "label": "时间戳"},
        {"keys": ["关联", "trace", "请求 id", "串联"], "label": "日志关联"},
        {"keys": ["复现", "重现"], "label": "复现路径"},
    ]),
    ("递归出口设计", "通用 · 递归", "implement", [
        {"keys": ["基例", "base case", "出口", "终止条件"], "label": "终止条件"},
        {"keys": ["缩小", "规模", "子问题"], "label": "问题规模缩小"},
        {"keys": ["返回值", "合并", "组合"], "label": "结果合并"},
        {"keys": ["栈", "层数", "深度"], "label": "递归深度"},
        {"keys": ["重复计算", "记忆化", "缓存"], "label": "重复子问题"},
    ]),
    ("动态规划状态设计", "算法 · DP", "implement", [
        {"keys": ["状态", "dp[i]", "定义"], "label": "状态定义"},
        {"keys": ["转移", "递推", "转移方程"], "label": "状态转移"},
        {"keys": ["初始", "边界", "base"], "label": "初始条件"},
        {"keys": ["遍历顺序", "顺序"], "label": "计算顺序"},
        {"keys": ["最优子结构", "重叠子问题"], "label": "最优子结构"},
    ]),
    ("链表操作", "数据结构 · 链表", "implement", [
        {"keys": ["头指针", "head", "新头"], "label": "头指针维护"},
        {"keys": ["临时变量", "next", "保存后继"], "label": "后继暂存"},
        {"keys": ["断链", "丢失节点", "顺序"], "label": "断链顺序"},
        {"keys": ["空表", "单节点", "NULL"], "label": "边界情形"},
        {"keys": ["释放", "free", "泄漏"], "label": "内存释放"},
    ]),
    ("排序算法实现", "算法 · 排序", "implement", [
        {"keys": ["基准", "pivot", "分区"], "label": "基准与分区"},
        {"keys": ["相等元素", "重复", "稳定"], "label": "相等元素处理"},
        {"keys": ["递归", "分治"], "label": "分治递归"},
        {"keys": ["复杂度", "O(n log n)", "最坏"], "label": "时间复杂度"},
        {"keys": ["原地", "额外空间", "空间"], "label": "空间开销"},
    ]),
    ("字符串处理", "通用 · 字符串", "implement", [
        {"keys": ["下标", "索引", "遍历"], "label": "下标遍历"},
        {"keys": ["计数", "哈希", "字典", "频次"], "label": "字符计数"},
        {"keys": ["空串", "空字符串"], "label": "空串处理"},
        {"keys": ["编码", "Unicode", "中文"], "label": "字符编码"},
        {"keys": ["切片", "截取", "边界"], "label": "切片边界"},
    ]),
]

# ──────────────────────────────────────────────────────────────────
# 代码审查室关卡（Review Gym Sessions）
# ──────────────────────────────────────────────────────────────────
# 每个关卡的 code 字段是 AI 生成的"看似正确但有 bug"的代码，
# defects 列表是注入缺陷的详情（行号/类型/解释），为服务端秘密。
# 前端只看到 defect_count（告知有几个 bug），看不到具体位置。
# ──────────────────────────────────────────────────────────────────

REVIEW_SESSIONS = [
    {
        "id": "REVIEW-0247",
        "title": "快速排序实现",
        "language": "python",
        "code": '''def quicksort(arr):
    """快速排序 —— AI 生成，待审查"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    rest = arr[:len(arr) // 2] + arr[len(arr) // 2:]
    left = [x for x in rest if x < pivot]
    right = [x for x in rest if x > pivot]
    return quicksort(left) + [pivot] + quicksort(right)''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 8,
        "related_weakness": "边界条件处理",
        "defects": [
            (6, "boundary", "右半切片 arr[len(arr)//2:] 把 pivot 本体又算了进去——pivot 会在结果里出现两次。应为 arr[len(arr)//2 + 1:]。"),
            (7, "logic", "left/right 都用严格比较，与 pivot 相等的元素会被整体丢弃：quicksort([2,2,1]) 只剩 [1,2]。一侧应使用 <=。"),
        ],
    },
    {
        "id": "REVIEW-0248",
        "title": "链表反转",
        "language": "c",
        "code": '''#include <stdio.h>
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
        cur = next->next;
    }
    return head;
}

void free_list(Node *head) {
    while (head) {
        Node *tmp = head;
        head = head->next;
    }
}''',
        "defect_count": 3,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "指针的内存布局",
        "defects": [
            (16, "logic", "cur = next->next 每轮跳过一个节点，链表一半节点丢失。应为 cur = next。"),
            (18, "logic", "返回的是旧头指针 head（反转后它是尾节点），新头应是 prev。"),
            (22, "performance", "free_list 只移动指针从不 free(tmp)，每个节点都泄漏。"),
        ],
    },
]

# ──────────────────────────────────────────────────────────────────
# 调试竞技场挑战（Arena Challenges）
# ──────────────────────────────────────────────────────────────────
# 每个挑战包含一段有 bug 的代码和它触发的测试失败输出。
# 用户在限时内修复代码，通过全部测试即视为过关。
# id 使用业务可读短 ID（非 UUID），如 DEBUG-0091。
# ──────────────────────────────────────────────────────────────────

ARENA_CHALLENGES = [
    {
        "id": "DEBUG-0091",
        "title": "中位数统计 · 测试全挂",
        "language": "python",
        "code": '''def median(nums):
    """返回列表中位数 —— AI 生成，测试全挂，待修复"""
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    # 偶数个：找中间两个数
    lo = mid
    while lo > mid - 1:
        lo -= 1
        # 没有退出条件 —— lo 会一直减下去
    return (nums[lo] + nums[mid + 1]) / 2''',
        "failing_output": """$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           TIMEOUT  [ 60%] 执行超过 5s（疑似死循环）
test_median.py::test_even_negative  TIMEOUT  [ 80%] 执行超过 5s（疑似死循环）
test_median.py::test_even_unsorted  TIMEOUT  [100%] 执行超过 5s（疑似死循环）

=================== 2 passed, 3 timeout in 15.42s ===================""",
        "time_limit_sec": 600,
        "difficulty": 3,
    },
]

# ──────────────────────────────────────────────────────────────────
# 认证考试定义 (CERT_EXAMS)
# ──────────────────────────────────────────────────────────────────
# 数据结构：(exam_id, topic, time_limit_min, pass_score)
#   exam_id:       考试 ID（业务可读短 ID）
#   topic:         考试主题
#   time_limit_min: 时间限制（分钟）
#   pass_score:    及格分数（placement 为 0 表示不定及格线）
#
# 两场考试：
#   cert-pointer: 指针能力认证（15 分钟，80 分及格）
#   placement:    定级测试（5 分钟，不设及格线，用于评估新用户水平）
# ──────────────────────────────────────────────────────────────────

# (exam_id, topic, time_limit_min, pass_score)
CERT_EXAMS = [
    ("cert-pointer", "指针", 15, 80),
    ("placement", "定级测试", 5, 0),
]

# ──────────────────────────────────────────────────────────────────
# 认证考试题目 (CERT_QUESTIONS)
# ──────────────────────────────────────────────────────────────────
# 数据结构：(exam_id, qid, kind, prompt, options, starter_code,
#            answer_correct, answer_includes, sort)
#   exam_id:         所属考试 ID
#   qid:            题目编号（q1/q2... 认证考试 / p1/p2... 定级测试）
#   kind:           题型（mcq=选择题 / code=编程题）
#   prompt:         题干文本
#   options:        选择题选项列表（编程题为 None）
#   starter_code:   编程题起始代码模板（选择题为 None）
#   answer_correct: 选择题正确答案（服务端比对，绝不下发）
#   answer_includes:编程题关键片段（用户代码含此即算正确）
#   sort:           显示排序（最后一个字段，省略字段名）
#
# 答案安全策略：answer_correct 和 answer_includes 仅存在于服务端，
# 前端 API 响应绝不包含这些字段，防止作弊。
# ──────────────────────────────────────────────────────────────────

# (exam_id, qid, kind, prompt, options, starter_code, answer_correct, answer_includes, sort)
CERT_QUESTIONS = [
    ("cert-pointer", "q1", "mcq", "int a = 5; int *p = &a; *p = 10; 之后 a 的值是？",
     ["5", "10", "未定义", "编译错误"], None, "10", None, 1),
    ("cert-pointer", "q2", "mcq", "free(p) 之后，指针 p 本身变成什么？",
     ["NULL", "悬空指针（值不变但目标已释放）", "自动销毁", "指向堆顶"], None,
     "悬空指针（值不变但目标已释放）", None, 2),
    ("cert-pointer", "q3", "mcq", "对 int arr[10]，arr 与 &arr[0] 的关系是？",
     ["值相等", "类型完全相同", "arr 多一级间接", "毫无关系"], None, "值相等", None, 3),
    ("cert-pointer", "q4", "mcq", "32 位系统下 int *p; p++ 让 p 前进多少字节？",
     ["1", "2", "4", "8"], None, "4", None, 4),
    ("cert-pointer", "q5", "code", "手写 swap：通过指针交换两个 int 的值。",
     None, "void swap(int *a, int *b) {\n    \n}", None, ["*a=*b", "*b="], 5),
    ("cert-pointer", "q6", "code", "写一个函数 find，接收 int* 数组首地址和长度，返回最大值所在位置的指针；空数组返回 NULL。",
     None, "int* find(int *arr, int n) {\n    \n}", None, ["NULL"], 6),
    ("placement", "p1", "mcq", "读代码找 bug：for (i = 0; i <= n; i++) sum += arr[i]; 问题在哪？",
     ["越界访问 arr[n]", "sum 类型不对", "循环方向错了", "没有 bug"], None, "越界访问 arr[n]", None, 1),
    ("placement", "p2", "mcq", "下面哪段代码会死循环？",
     ["while (x > 0) { x -= 2; }（x 为奇数正数）", "for (i = 0; i < 10; i++)",
      "while (x != 0) { x = x / 2; }", "do { x--; } while (x > 0);"], None,
     "while (x > 0) { x -= 2; }（x 为奇数正数）", None, 2),
    ("placement", "p3", "mcq", "测试发现 quicksort([2,2,1]) 返回 [1,2]，最可能丢了什么？",
     ["与 pivot 相等的元素", "最小值", "第一个元素", "什么都不缺"], None, "与 pivot 相等的元素", None, 3),
    ("placement", "p4", "code", "手写：返回字符串中第一个不重复的字符下标，没有则返回 -1。",
     None, "def first_unique(s):\n    ", None, ["return"], 4),
    ("placement", "p5", "code", "手写：判断一个整数是否为 2 的幂。",
     None, "def is_power_of_two(n):\n    ", None, ["n>0"], 5),
]


async def seed_deck(db: AsyncSession) -> None:
    """灌入种子数据（幂等）。

    执行流程：
    1. 幂等检查：如果知识点表已有数据 → 跳过所有插入（安全可重复执行）
    2. 插入知识点（13 个）
    3. 插入审查关卡（2 个），然后 await db.flush() 确保外键可用
    4. 插入注入缺陷（子表，依赖审查关卡的外键）
    5. 插入竞技场挑战（1 个）
    6. 插入认证考试（2 个），然后 await db.flush() 确保外键可用
    7. 插入认证题目（11 道，依赖考试的外键）
    8. 提交事务（await db.commit()）

    注意：funcalchemy 的 db.add() 只是将对象加入会话（staging），
    实际 SQL 在 flush 或 commit 时才发送到数据库。由于 SQLite
    在每条语句执行时即时检查外键约束，我们必须先 flush 父表再插入子表。

    Args:
        db: SQLAlchemy 异步数据库会话，由调用方（lifespan）传入。
    """
    # ── 步骤 1：幂等检查 ──
    # 如果知识点表已有数据，说明种子已导入，直接返回
    count = await db.scalar(select(func.count()).select_from(DeckKnowledgePoint))
    if count and count > 0:
        return

    # ── 步骤 2：插入知识点（父表，最先插入） ──
    for name, category, axis, key_points in KNOWLEDGE_POINTS:
        db.add(DeckKnowledgePoint(name=name, category=category, axis=axis,
                                  key_points=key_points))

    # ── 步骤 3：插入审查关卡（父表） ──
    # 先用字典推导排除 defects 字段（它是子表数据，不是 DeckReviewSession 的字段）
    # 先落父表再落子表：SQLite 按语句即时检查外键
    for s in REVIEW_SESSIONS:
        session_data = {k: v for k, v in s.items() if k != "defects"}
        db.add(DeckReviewSession(**session_data))
    # flush 将审查关卡 INSERT 发送到数据库，确保外键对子表可用
    await db.flush()

    # ── 步骤 4：插入注入缺陷（子表，依赖审查关卡外键） ──
    for s in REVIEW_SESSIONS:
        for line, dtype, explanation in s["defects"]:
            db.add(
                DeckInjectedDefect(
                    session_id=s["id"], line=line, type=dtype, explanation=explanation
                )
            )

    # ── 步骤 5：插入竞技场挑战（无子表，直接插入） ──
    for c in ARENA_CHALLENGES:
        db.add(DeckArenaChallenge(**c))

    # ── 步骤 6：插入认证考试（父表） ──
    for exam_id, topic, limit_min, pass_score in CERT_EXAMS:
        db.add(
            DeckCertExam(id=exam_id, topic=topic, time_limit_min=limit_min, pass_score=pass_score)
        )
    # flush 确保考试记录的 ID 对题目子表可用
    await db.flush()

    # ── 步骤 7：插入认证题目（子表，依赖考试外键） ──
    for row in CERT_QUESTIONS:
        # 解包元组：每个题目有 9 个字段
        (
            exam_id,
            qid,
            kind,
            prompt,
            options,
            starter_code,
            answer_correct,
            answer_includes,
            sort_order,
        ) = row
        db.add(
            DeckCertQuestion(
                exam_id=exam_id,
                qid=qid,
                kind=kind,
                prompt=prompt,
                options=options,
                starter_code=starter_code,
                answer_correct=answer_correct,
                answer_includes=answer_includes,
                sort_order=sort_order,
            )
        )

    # ── 步骤 8：提交事务 ──
    # 所有数据一次性提交，保证原子性——要么全部成功，要么全部回滚
    await db.commit()
