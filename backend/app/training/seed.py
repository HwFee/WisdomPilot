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
#   2. 代码审查关卡（REVIEW_SESSIONS）  —— 30 个关卡 + 注入缺陷
#   3. 调试竞技场挑战（ARENA_CHALLENGES）—— 20 个挑战
#   4. 认证考试（CERT_EXAMS + CERT_QUESTIONS）—— 5 场考试 + 29 道题目
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
#
# 字段说明：
#   defect_count:     注入缺陷数量（前端据此提示"有 N 个 bug"，不泄露细节）
#   difficulty:       难度等级（1-5，供难度自适应与个性化推荐使用）
#   eta_minutes:      预计完成时间（分钟）
#   related_weakness: 关联的薄弱知识点（名称与 KNOWLEDGE_POINTS 一一对应）
#   defects:          注入缺陷详情列表，每项为 (行号, 缺陷类型, 解释) 三元组；
#                     类型取值 boundary=边界 / logic=逻辑 / security=安全 /
#                     style=风格 / performance=性能；整个列表为服务端秘密
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
    rest = arr[:len(arr) // 2] + arr[len(arr) // 2 + 1:]
    left = [x for x in rest if x < pivot]
    right = [x for x in rest if x > pivot]
    return quicksort(left) + [pivot] + quicksort(right)''',
        "defect_count": 1,
        "difficulty": 3,
        "eta_minutes": 8,
        "related_weakness": "边界条件处理",
        "defects": [
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
            (16, "logic", "cur = next->next 每轮跳过一个节点：偶数长度时约一半节点被跳过丢失，奇数长度时 next 为 NULL 再解引用 next->next 直接段错误。应为 cur = next。"),
            (18, "logic", "返回的是旧头指针 head（反转后它是尾节点），新头应是 prev。"),
            (24, "performance", "free_list 只移动指针从不 free(tmp)，每个节点都泄漏。"),
        ],
    },
    {
        "id": "REVIEW-0249",
        "title": "二分查找",
        "language": "python",
        "code": '''def binary_search(arr, target):
    """二分查找 -- AI 生成，待审查"""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return -1''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "边界条件处理",
        "defects": [
            (3, "boundary", "right = len(arr) 越界：当 target 大于所有元素时，mid 会等于 len(arr)，arr[mid] 抛 IndexError。应为 len(arr) - 1。"),
            (11, "logic", "right = mid 会导致死循环：当 target < arr[mid] 时 right 不收缩到 mid-1，区间永远无法缩小到空。应为 right = mid - 1。"),
        ],
    },
    {
        "id": "REVIEW-0250",
        "title": "用户注册函数",
        "language": "python",
        "code": '''def register(username, password, db):
    """用户注册 -- AI 生成，待审查"""
    if len(password) < 8:
        return False
    query = "INSERT INTO users (name, pwd) VALUES ('" + username + "', '" + password + "')"
    db.execute(query)
    if db.rowcount > 0:
        return True
    else:
        return False''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "安全漏洞模式",
        "defects": [
            (5, "security", "字符串拼接 SQL 存在注入风险：用户名输入 ' OR 1=1 -- 即可绕过注册。应使用参数化查询 db.execute(\"INSERT ... VALUES (?, ?)\", username, password)。"),
            (3, "style", "魔法数字 8 直接硬编码，含义不明。应定义为命名常量 MIN_PASSWORD_LENGTH = 8。"),
        ],
    },
    {
        "id": "REVIEW-0251",
        "title": "日志分析器",
        "language": "python",
        "code": '''def analyze_logs(logs):
    """日志分析器 -- AI 生成，待审查"""
    errors = []
    warnings = []
    info = []
    for line in logs:
        if "ERROR" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            errors.append({"time": timestamp, "msg": message})
        if "WARN" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            warnings.append({"time": timestamp, "msg": message})
        if "INFO" in line:
            parts = line.split(" ")
            timestamp = parts[0]
            message = " ".join(parts[1:])
            info.append({"time": timestamp, "msg": message})
    return errors, warnings, info''',
        "defect_count": 3,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "坏味道识别",
        "defects": [
            (7, "style", "三个 if 分支重复了完全相同的解析逻辑（split + join + append），应抽取为 _parse_line(line) 公共函数。"),
            (12, "style", "三个独立 if 应改为 elif 链：已匹配 ERROR 的行无需再检查 WARN 和 INFO，当前每行都被检查三次。"),
            (8, "performance", "line.split(\" \") 会分割整行产生多余字符串，应使用 line.split(\" \", 1) 只分割一次。"),
        ],
    },
    {
        "id": "REVIEW-0252",
        "title": "字符串拷贝",
        "language": "c",
        "code": '''#include <string.h>

char* copy_str(char *src, char *dst) {
    /* 字符串拷贝 -- AI 生成，待审查 */
    int i = 0;
    while (src[i] != '\\0') {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\\0';
    return dst;
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "安全漏洞模式",
        "defects": [
            (6, "security", "循环没有检查 dst 缓冲区大小：当 src 比 dst 长时，dst[i] = src[i] 会越界写入，导致缓冲区溢出。应传入 dst 大小并做边界检查。"),
            (3, "boundary", "没有检查 src 或 dst 是否为 NULL，传入空指针会直接段错误。应在函数入口加 if (src == NULL || dst == NULL) return NULL。"),
        ],
    },
    {
        "id": "REVIEW-0253",
        "title": "缓存装饰器",
        "language": "python",
        "code": '''import time

def memoize(func):
    """缓存装饰器 -- AI 生成，待审查"""
    cache = {}
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "并发代码审阅",
        "defects": [
            (8, "logic", "多线程下 check-then-set 存在竞态条件：两个线程同时通过 key not in cache 检查后都执行 func，缓存失效。应加 threading.Lock 保护。"),
            (7, "performance", "str(args) + str(kwargs) 每次调用都做字符串拼接，对于高频调用的热路径函数开销显著。应使用 args + tuple(sorted(kwargs.items())) 作为 key。"),
        ],
    },
    {
        "id": "REVIEW-0254",
        "title": "冒泡排序",
        "language": "python",
        "code": '''def b(a):
    """冒泡排序（升序） -- AI 生成，待审查"""
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] < a[j + 1]:
                t = a[j]
                a[j] = a[j + 1]
                a[j + 1] = t
    return a''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "坏味道识别",
        "defects": [
            (1, "style", "函数名 b 和参数名 a 完全无法自解释，应改为 bubble_sort(arr)。命名是文档的一部分。"),
            (6, "logic", "比较方向错误：a[j] < a[j+1] 会把大元素冒泡到前面（降序），而函数声明的是升序。应为 a[j] > a[j + 1]。"),
        ],
    },
    {
        "id": "REVIEW-0255",
        "title": "两数之和",
        "language": "python",
        "code": '''def two_sum(nums, target):
    """两数之和 -- AI 生成，待审查"""
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return None''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "边界条件处理",
        "defects": [
            (4, "boundary", "内层循环 j 从 i 开始，单元素数组会自匹配：two_sum([3], 6) 返回 [0, 0]。内层应从 i + 1 开始。"),
            (7, "logic", "找不到配对时返回 None，调用方按索引列表解包会直接崩溃；空数组同样走这条路径。契约上应返回空列表 []。"),
        ],
    },
    {
        "id": "REVIEW-0256",
        "title": "并发计数器",
        "language": "python",
        "code": '''import threading

counter = 0

def increment():
    """线程安全计数器 -- AI 生成，待审查"""
    global counter
    temp = counter
    temp += 1
    counter = temp

def run_parallel(n):
    threads = []
    for _ in range(n):
        t = threading.Thread(target=increment)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return counter''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "并发代码审阅",
        "defects": [
            (8, "logic", "读改写（read-modify-write）不是原子操作：temp = counter 读取与 counter = temp 写回之间可能被调度切换，多线程并发时计数会丢失（CPython 的 GIL 让窗口很窄、难以稳定复现，但 GIL 并不保证读改写原子）。应加锁或改用原子计数。"),
            (10, "logic", "counter = temp 写回同样在锁外，且 temp 临时变量毫无必要；应直接在锁保护内 counter += 1，避免中间态被并发观测。"),
        ],
    },
    {
        "id": "REVIEW-0257",
        "title": "温度转换函数",
        "language": "python",
        "code": '''def celsius_to_fahrenheit(t):
    """温度转换 -- AI 生成，待审查"""
    result = t * 9 / 5 + 32
    return result


def celsius_to_kelvin(t):
    result = t + 273.15
    return result''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "坏味道识别",
        "defects": [
            (3, "style", "魔法数字 9、5、32 直接硬编码，含义不明且两处公式无法互相印证。应提取命名常量，如 C_TO_F_SCALE = 9 / 5、FAHRENHEIT_OFFSET = 32。"),
            (7, "style", "两处函数都先把结果赋给临时变量 result 再 return，这个中间变量毫无必要，让公式读起来绕了一层。应直接 return 表达式，代码更直白。"),
        ],
    },
    {
        "id": "REVIEW-0258",
        "title": "目录列举函数",
        "language": "python",
        "code": '''import os


def list_dir(path):
    """列出目录 -- AI 生成，待审查"""
    os.system("ls -la " + path)
    print("done")''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "安全漏洞模式",
        "defects": [
            (6, "security", "os.system 用字符串拼接把输入直接交给 shell 执行：path 传入分号加删除命令时发生命令注入，可执行任意系统命令。应改用 subprocess.run 传参数数组，不经过 shell。"),
            (5, "boundary", "函数入口对 path 未做任何校验：传 None 时下一行 'ls -la ' + None 直接抛 TypeError，空串或不存在的路径则把 shell 的报错当成功返回，行为与调用方预期不符。应在入口断言 path 为合法目录。"),
        ],
    },
    {
        "id": "REVIEW-0259",
        "title": "动态数组分配",
        "language": "c",
        "code": '''#include <stdlib.h>

int* make_array(int n) {
    int *arr = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }
    return arr;
}

void free_array(int *arr) {
    free(arr);
}

int main() {
    int *a = make_array(10);
    free_array(a);
    free_array(a);
    return 0;
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "指针的内存布局",
        "defects": [
            (18, "logic", "对同一指针 a 连续调用 free_array 两次：第二次 free 是 double free，堆管理器会崩溃或被利用。释放后应置 a = NULL 并在 free_array 里判空。"),
            (4, "boundary", "malloc 未检查返回值：内存不足或 n 异常大时 arr 为 NULL，随后 arr[i] = i 直接段错误。分配后应判断 arr == NULL 并返回失败。"),
        ],
    },
    {
        "id": "REVIEW-0260",
        "title": "字符串拼接问候",
        "language": "c",
        "code": '''#include <stdio.h>
#include <string.h>

void greet(const char *name) {
    char buffer[32];
    strcpy(buffer, "Hello, ");
    strcat(buffer, name);
    printf("%s\\n", buffer);
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "栈与调用帧",
        "defects": [
            (7, "security", "strcat 不检查目标缓冲区剩余空间：name 超过 24 字节就会越过 buffer 边界写入，覆盖栈帧中的返回地址，构成经典栈溢出。应改用 strncat 并传剩余空间。"),
            (5, "boundary", "buffer 固定 32 字节且前缀 Hello, 已占 7 字节，任何超长输入都会溢出；应先计算所需长度并动态分配。"),
        ],
    },
    {
        "id": "REVIEW-0261",
        "title": "极简调试器",
        "language": "python",
        "code": '''class MiniDebugger:
    """极简调试器 -- AI 生成，待审查"""
    def __init__(self, program):
        self.program = program
        self.pc = 0
        self.breakpoints = set()

    def add_breakpoint(self, line):
        self.breakpoints.add(line)

    def run(self):
        while self.pc < len(self.program):
            if self.pc in self.breakpoints:
                return self.pc
            self.pc += 1
        return None

    def step(self):
        self.pc += 1
        return self.pc''',
        "defect_count": 3,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "断点与单步策略",
        "defects": [
            (13, "logic", "run 命中断点即 return，pc 停在断点行；再次调用 run 会在同一断点重新断住（pc 未越过断点），断点之后的代码无法靠 run 继续执行。缺少'继续到下一断点'的语义——应在断点命中后支持从下一行恢复。"),
            (9, "boundary", "add_breakpoint 未校验行号范围：传入超出 program 长度的行号会被接受，运行时永不命中。应在添加时检查 0 <= line < len(self.program)。"),
            (19, "boundary", "step 不校验 pc 是否已到末尾：程序执行完后继续 step，pc 会越过 len(program) 越界推进（虽无下标访问不会崩溃，但 run 会因 pc 越过末尾而跳过剩余逻辑、语义错乱）。应在 pc >= len(self.program) 时返回 None。"),
        ],
    },
    {
        "id": "REVIEW-0262",
        "title": "日志时间戳提取",
        "language": "python",
        "code": '''def extract_timestamps(log_lines):
    """提取日志时间戳 -- AI 生成，待审查"""
    timestamps = []
    for line in log_lines:
        ts = line[:19]
        timestamps.append(ts)
    return timestamps''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "日志定位法",
        "defects": [
            (5, "boundary", "line[:19] 硬编码假设每行都以固定 19 字符的 ISO 时间戳开头：行首有缩进、BOM 或变长前缀时，会静默截出不是时间戳的内容。应先按分隔符解析首字段并用正则校验格式。"),
            (6, "logic", "对空行、纯空白行不加任何判断直接 append：它们被当成合法时间戳计入结果，统计被无效行稀释。应先跳过不匹配日志格式的行。"),
        ],
    },
    {
        "id": "REVIEW-0263",
        "title": "斐波那契递归",
        "language": "python",
        "code": '''def fib(n):
    """斐波那契 -- AI 生成，待审查"""
    if n == 0:
        return 0
    return fib(n - 1) + fib(n - 2)''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "递归出口设计",
        "defects": [
            (3, "logic", "基例只覆盖 n == 0：n 为 1 时递归到 fib(0) 与 fib(-1)，负数永达不到出口，最终 RecursionError 爆栈。应改为 if n <= 1: return n。"),
            (5, "performance", "无记忆化的朴素递归产生指数级重复计算，fib(35) 已明显卡顿。应加缓存（functools.lru_cache 或手写 memo）。"),
        ],
    },
    {
        "id": "REVIEW-0264",
        "title": "二分插入",
        "language": "python",
        "code": '''def insert_sorted(arr, x):
    """二分插入 -- AI 生成，待审查"""
    lo, hi = 0, len(arr)
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return arr[:lo] + [x] + arr[lo:]''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "边界条件处理",
        "defects": [
            (3, "boundary", "hi 初始化为 len(arr) 而不是 len(arr) - 1：x 大于所有元素时，mid 会取到 len(arr)，arr[mid] 抛 IndexError。"),
            (6, "boundary", "当 hi 越过上界时，arr[mid] 直接用越界下标访问数组；空数组 insert_sorted([], 5) 第一轮循环就在本行抛 IndexError。应特判空数组或改用左闭右开区间配合 lo < hi。"),
        ],
    },
    {
        "id": "REVIEW-0265",
        "title": "链表删除值",
        "language": "c",
        "code": '''#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node* remove_val(Node *head, int val) {
    Node *cur = head;
    while (cur && cur->next) {
        if (cur->next->val == val) {
            Node *tmp = cur->next;
            cur->next = cur->next->next;
            free(tmp);
        }
        cur = cur->next;
    }
    return head;
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "链表操作",
        "defects": [
            (9, "logic", "遍历从头节点之后的节点开始，头节点自身的值永远不被检查：remove_val(1 -> 2 -> 3, 1) 返回的链表仍含 1。应使用哨兵节点 dummy 或单独处理头节点。"),
            (16, "logic", "删除命中后 cur 仍前进到刚链接上来的新节点，跳过对它的检查：连续重复值 1 -> 2 -> 2 -> 3 删 2 会漏删一个。删除分支不应前进 cur。"),
        ],
    },
    {
        "id": "REVIEW-0266",
        "title": "归并排序",
        "language": "python",
        "code": '''def merge_sort(arr):
    """归并排序 -- AI 生成，待审查"""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(a, b):
    result = []
    i = j = 0
    while i < len(a) or j < len(b):
        if j == len(b) or a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    return result''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "排序算法实现",
        "defects": [
            (15, "boundary", "当 a 已耗尽（i == len(a)）而 b 仍有剩余时，条件短路 j == len(b) 为假，随即在本行求值 a[i] 越界崩溃。应先判断 i == len(a) 直接取 b[j]。"),
            (7, "performance", "merge 每次返回新列表，merge_sort 对每个子数组切片拷贝，总空间 O(n log n)。可改为在原数组上用辅助数组与下标区间合并。"),
        ],
    },
    {
        "id": "REVIEW-0267",
        "title": "账户转账",
        "language": "python",
        "code": '''import threading

class Account:
    def __init__(self, balance):
        self.balance = balance
        self.lock = threading.Lock()

    def transfer(self, other, amount):
        with self.lock:
            with other.lock:
                self.balance -= amount
                other.balance += amount


a = Account(100)
b = Account(100)

t1 = threading.Thread(target=a.transfer, args=(b, 50))
t2 = threading.Thread(target=b.transfer, args=(a, 50))
t1.start()
t2.start()
t1.join()
t2.join()''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "并发代码审阅",
        "defects": [
            (10, "logic", "两线程交叉持锁形成死锁：t1 持有 a.lock 等待 b.lock，t2 持有 b.lock 等待 a.lock，互相等待永不释放，程序挂死。应按固定顺序加锁（如 id 升序）或改用单一全局锁。"),
            (11, "boundary", "转账未校验余额是否充足：余额会被扣成负数（透支），账目失真。应在扣减前检查 self.balance >= amount。"),
        ],
    },
    {
        "id": "REVIEW-0268",
        "title": "数据处理函数",
        "language": "python",
        "code": '''def process(data):
    """处理数据 -- AI 生成，待审查"""
    total = 0
    for x in data:
        if x is not None:
            if x > 0:
                total += x
            else:
                total -= x
    avg = total / len(data) if data else 0
    max_val = data[0] if data else 0
    for x in data:
        if x is not None and x > max_val:
            max_val = x
    return {"sum": total, "avg": avg, "max": max_val}''',
        "defect_count": 3,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "坏味道识别",
        "defects": [
            (5, "style", "for 内再套两层 if/else 形成三层缩进，逻辑被埋进深处难以阅读。应抽取累加辅助函数，或用 continue 提前跳过 None 降低嵌套深度。"),
            (10, "logic", "avg 以 len(data) 作分母，但统计的只是非 None 元素的绝对值之和，口径不一致；且此后又遍历一次 data 求 max，重复遍历。应合并为一次循环并统一口径。"),
            (12, "boundary", "max_val 直接用 data[0] 初始化（上一行）：前半段对 None 有专门处理（说明 data 允许含 None），若首元素是 None，max_val 变 None，本行循环内 x > max_val 比较直接抛 TypeError 崩溃。应跳过 None 或初始化为负无穷。"),
        ],
    },
    {
        "id": "REVIEW-0269",
        "title": "用户主页渲染",
        "language": "python",
        "code": '''def render_user(name, bio):
    """渲染用户主页 -- AI 生成，待审查"""
    html = "<h1>Welcome, " + name + "!</h1>"
    html += "<p>" + bio + "</p>"
    return html''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 10,
        "related_weakness": "安全漏洞模式",
        "defects": [
            (3, "security", "name 未经转义直接拼接进 HTML：用户名含 script 标签即触发存储型 XSS。应使用 html.escape 转义后再插入。"),
            (4, "security", "bio 存在同样的注入面，且未限制长度与标签白名单，恶意 img 标签的 onerror 可执行任意脚本。除转义外还应校验长度。"),
        ],
    },
    {
        "id": "REVIEW-0270",
        "title": "条件返回指针",
        "language": "c",
        "code": '''#include <stdlib.h>

int* get_ptr(int flag) {
    int *p = malloc(sizeof(int));
    if (flag) {
        return p;
    }
    free(p);
    return p;
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "指针的内存布局",
        "defects": [
            (9, "logic", "free(p) 之后仍 return p：调用方拿到的指针已失效（use-after-free），解引用即未定义行为。释放后应返回 NULL。"),
            (4, "boundary", "malloc 未检查失败：内存不足时 p 为 NULL，函数仍把 NULL 当有效指针返回。应分配后判断 p == NULL 直接返回 NULL。"),
        ],
    },
    {
        "id": "REVIEW-0271",
        "title": "递归倒计时",
        "language": "python",
        "code": '''def countdown(n):
    """倒计时 -- AI 生成，待审查"""
    print(n)
    countdown(n - 1)''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "栈与调用帧",
        "defects": [
            (3, "logic", "递归缺少终止条件：countdown(5) 会一路递归到负数，最终达到 Python 递归上限抛 RecursionError 爆栈。应加 if n <= 0: return 作为出口。"),
            (4, "boundary", "即便补上出口，递归深度仍随 n 线性增长，超大输入会耗尽调用栈。应改为循环迭代，避免调用帧无限增长。"),
        ],
    },
    {
        "id": "REVIEW-0272",
        "title": "二叉树求和",
        "language": "python",
        "code": '''def tree_sum(node):
    """二叉树求和 -- AI 生成，待审查"""
    if node is None:
        return 0
    return node.val + tree_sum(node.left)''',
        "defect_count": 2,
        "difficulty": 3,
        "eta_minutes": 8,
        "related_weakness": "递归出口设计",
        "defects": [
            (5, "logic", "递归只访问 node.left，右子树被整体忽略：非左倾二叉树的求和结果偏小。应在返回式中补上 tree_sum(node.right)。"),
            (3, "boundary", "基例只处理空节点；当树退化为单链时递归深度达 O(n)，极易爆栈。深树场景应改用显式栈迭代遍历。"),
        ],
    },
    {
        "id": "REVIEW-0273",
        "title": "打家劫舍 DP",
        "language": "python",
        "code": '''def rob(nums):
    """打家劫舍 -- AI 生成，待审查"""
    prev, cur = 0, 0
    for x in nums:
        cur = max(cur, prev + x)
        prev = cur
    return cur''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "动态规划状态设计",
        "defects": [
            (6, "logic", "prev = cur 在 cur 更新之后执行，把本轮结果写回 prev；下一轮 prev + x 变成 cur + x，等于把相邻两家一起偷，[2,7,9,3,1] 应得 12 却得 22。应同步推进状态：prev, cur = cur, max(cur, prev + x)（旧 cur 成为新 prev，旧 prev 参与本轮转移）。"),
            (3, "style", "prev / cur 未表达 DP 状态含义（到上一间 / 当前间为止的最大金额），阅读转移方程时无法理解两个变量的角色。应命名 prev_max / cur_max 并注释状态。"),
        ],
    },
    {
        "id": "REVIEW-0274",
        "title": "链表环检测",
        "language": "c",
        "code": '''#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

int has_cycle(Node *head) {
    Node *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow == fast;
}''',
        "defect_count": 2,
        "difficulty": 4,
        "eta_minutes": 12,
        "related_weakness": "链表操作",
        "defects": [
            (14, "logic", "相遇检查放在循环结束后：有环时 fast 永远取不到 NULL（环内转圈），循环退不出，直接死循环——应在循环体内每步比较并在相遇时立即返回 1；无环时 fast 先到 NULL 退出、slow 才到中途，循环后的相等比较没有意义（除空/单节点会巧合误报）。"),
            (9, "boundary", "空链表或单节点链表时循环体不执行，直接比较 slow == fast：head 为空时两者都是 NULL，返回 1 误报有环。应先特判 head 为空或仅一个节点。"),
        ],
    },
    {
        "id": "REVIEW-0275",
        "title": "选择排序",
        "language": "python",
        "code": '''def selection_sort(arr):
    """选择排序 -- AI 生成，待审查"""
    n = len(arr)
    for i in range(n):
        min_idx = 0
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr''',
        "defect_count": 1,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "排序算法实现",
        "defects": [
            (5, "logic", "min_idx 初始化为 0 而不是 i：每轮都把全局最小元素当作本轮最小去交换，会把前面已排好的位置重新打乱（[3,1,2] 排完变成 [2,1,3]）。应初始化为 i。"),
        ],
    },
    {
        "id": "REVIEW-0276",
        "title": "去除字符串空格",
        "language": "python",
        "code": '''def remove_spaces(s):
    """去除字符串空格 -- AI 生成，待审查"""
    result = ""
    for i in range(len(s)):
        if s[i] != " ":
            result += s[i]
    return result''',
        "defect_count": 2,
        "difficulty": 2,
        "eta_minutes": 6,
        "related_weakness": "字符串处理",
        "defects": [
            (5, "logic", "只过滤半角空格，Tab、换行、全角空格等其它空白字符全部保留，与去除空白的目标不符。应改用 str.isspace 判断或 split 后拼接。"),
            (6, "performance", "result += s[i] 逐字符拼接依赖 CPython 对单引用字符串的原地优化才能线性完成；不满足优化条件（多引用/其他解释器）时每步都重建新串，性能不可靠。应收集到列表再 join。"),
        ],
    },
]

# ──────────────────────────────────────────────────────────────────
# 调试竞技场挑战（Arena Challenges）
# ──────────────────────────────────────────────────────────────────
# 每个挑战包含一段有 bug 的代码和它触发的测试失败输出。
# 用户在限时内修复代码，通过全部测试即视为过关。
# id 使用业务可读短 ID（非 UUID），如 DEBUG-0091。
#
# 字段说明：
#   code:           待修复代码（用户限时内修复并通过全部测试即过关）
#   failing_output: 修复前触发的失败输出（"报错现场"线索）
#   test_cases:     Judge0 判题测试用例列表（服务端秘密，不下发前端）
#   time_limit_sec: 作答限时（秒），600 = 10 分钟；前端倒计时用，倒计时结束自动提交。
#                   注意与 Judge0 判题 CPU 上限（全局 10s，judge0_client.py）是两回事，
#                   本字段不参与判题链路。
#   difficulty:     难度等级（1-5）
# ──────────────────────────────────────────────────────────────────

ARENA_CHALLENGES = [
    {
        "id": "DEBUG-0091",
        "title": "中位数统计 · 测试全挂",
        "related_weakness": "边界条件处理",
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
        # 循环只跑一轮，但左中位取错了位置
    return (nums[lo] + nums[mid + 1]) / 2''',
        "failing_output": """$ pytest test_median.py -v
test_median.py::test_odd            PASSED   [ 20%]
test_median.py::test_single         PASSED   [ 40%]
test_median.py::test_even           FAILED   assert 3.5 == 3.0  [ 60%]
test_median.py::test_even_negative  FAILED   assert -2.5 == -3.5  [ 80%]
test_median.py::test_even_unsorted  FAILED   assert 6.5 == 6.0  [100%]

=================== 2 passed, 3 failed in 0.05s ===================
median([4,1,2,5]) -> 3.5（期望 3.0）
偶数个时中间两个数取错了：右中位用了 nums[mid + 1]，应为 nums[mid]。""",
        # Judge0 判题测试用例：输入为 JSON 数组（stdin），期望为中位数输出
        "test_cases": [
            {"input": "[1]", "expected_output": "1"},
            {"input": "[3, 1, 2]", "expected_output": "2"},
            {"input": "[4, 1, 2, 5]", "expected_output": "3.0"},
            # 排序后 [-5, -4, -3, -1]，中位数 (-4 + -3) / 2 = -3.5
            {"input": "[-1, -4, -3, -5]", "expected_output": "-3.5"},
            {"input": "[9, 5, 2, 7, 8, 1]", "expected_output": "6.0"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0092",
        "title": "二分查找 · 越界",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def binary_search(arr, target):
    """二分查找 -- AI 生成，测试全挂，待修复"""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1''',
        "failing_output": """$ pytest test_bsearch.py -v
test_bsearch.py::test_found         PASSED   [ 20%]
test_bsearch.py::test_single        PASSED   [ 40%]
test_bsearch.py::test_not_found     IndexError: list index out of range  [ 60%]
test_bsearch.py::test_last_element  PASSED   [ 80%]
test_bsearch.py::test_empty         IndexError: list index out of range  [100%]

=================== 3 passed, 2 failed in 0.09s ===================
right 初始化为 len(arr)，当 target 大于所有元素或数组为空时 mid 越界。""",
        # Judge0 判题测试用例：输入第一行 JSON 数组、第二行目标值，期望为下标或 -1
        "test_cases": [
            {"input": "[1, 2, 3, 4, 5]\n3", "expected_output": "2"},
            {"input": "[1, 2, 3, 4, 5]\n6", "expected_output": "-1"},
            {"input": "[1, 2, 3, 4, 5]\n5", "expected_output": "4"},
            {"input": "[7]\n7", "expected_output": "0"},
            {"input": "[]\n1", "expected_output": "-1"},
        ],
        "time_limit_sec": 600,
        "difficulty": 1,
    },
    {
        "id": "DEBUG-0093",
        "title": "字符串反转 · 指针丢失",
        "related_weakness": "指针的内存布局",
        "language": "c",
        "code": '''#include <stdlib.h>
#include <string.h>

char* reverse_str(char *s) {
    /* 字符串反转 -- AI 生成，测试全挂，待修复 */
    int len = strlen(s);
    char *result = malloc(len + 1);
    char *dest = result;
    char *src = s + len - 1;
    while (src >= s) {
        *dest++ = *src--;
    }
    *dest = '\\0';
    return dest;
}''',
        "failing_output": """$ gcc -o test test.c && ./test
test_str_reverse("hello")    -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("a")        -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("")         -> "" (expected "")                        OK
test_str_reverse("abcdef")   -> 运行错误（free(): invalid pointer）    FAIL
test_str_reverse("12345")    -> 运行错误（free(): invalid pointer）    FAIL

======================== 1/5 tests passed ========================
返回的是 dest（已移到字符串末尾），不是 result；测试程序 free 这个偏移指针直接崩溃。""",
        # Judge0 判题测试用例：输入为单行字符串（stdin），期望为反转结果
        "test_cases": [
            {"input": "hello", "expected_output": "olleh"},
            {"input": "a", "expected_output": "a"},
            {"input": "", "expected_output": ""},
            {"input": "abcdef", "expected_output": "fedcba"},
            {"input": "12345", "expected_output": "54321"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0094",
        "title": "去重计数 · 逻辑错误",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def count_unique(words):
    """去重计数 -- AI 生成，测试全挂，待修复"""
    seen = set()
    count = 0
    for w in words:
        seen.add(w)
        count += 1
    return count''',
        "failing_output": """$ pytest test_unique.py -v
test_unique.py::test_empty          PASSED   [ 20%]
test_unique.py::test_all_unique     PASSED   [ 40%]
test_unique.py::test_all_same       FAILED   assert 3 == 1  [ 60%]
test_unique.py::test_mixed          FAILED   assert 5 == 3  [ 80%]
test_unique.py::test_with_numbers   FAILED   assert 3 == 2  [100%]

=================== 2 passed, 3 failed in 0.05s ===================
count 对每个 word 都 +1，没有跳过已见元素。需要加 if w not in seen 判断。""",
        # Judge0 判题测试用例：输入为 JSON 单词数组（stdin），期望为去重计数
        "test_cases": [
            {"input": "[]", "expected_output": "0"},
            {"input": '["a", "b", "c"]', "expected_output": "3"},
            {"input": '["a", "a", "a"]', "expected_output": "1"},
            {"input": '["a", "b", "a", "c", "b"]', "expected_output": "3"},
            {"input": '["1", "1", "2"]', "expected_output": "2"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0095",
        "title": "阶乘 · 栈溢出",
        "related_weakness": "递归出口设计",
        "language": "python",
        "code": '''def factorial(n):
    """阶乘 -- AI 生成，测试全挂，待修复"""
    return n * factorial(n - 1)''',
        "failing_output": """$ pytest test_factorial.py -v
test_factorial.py::test_zero     RecursionError  [ 20%]
test_factorial.py::test_one      RecursionError  [ 40%]
test_factorial.py::test_three    RecursionError  [ 60%]
test_factorial.py::test_five     RecursionError  [ 80%]
test_factorial.py::test_ten      RecursionError  [100%]

=================== 0 passed, 5 failed in 0.12s ===================
RecursionError: maximum recursion depth exceeded
缺少递归出口（基例），需要加 if n <= 1: return 1。""",
        # Judge0 判题测试用例：输入为整数（stdin），期望为阶乘结果
        "test_cases": [
            {"input": "0", "expected_output": "1"},
            {"input": "1", "expected_output": "1"},
            {"input": "5", "expected_output": "120"},
            {"input": "3", "expected_output": "6"},
            {"input": "10", "expected_output": "3628800"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0096",
        "title": "数组右旋 · 方向反了",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def rotate(nums, k):
    """数组右旋 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    k = k % n
    return nums[k:] + nums[:k]''',
        "failing_output": """$ pytest test_rotate.py -v
test_rotate.py::test_basic       FAILED   [ 20%]
test_rotate.py::test_zero        PASSED   [ 40%]
test_rotate.py::test_wrap        FAILED   [ 60%]
test_rotate.py::test_single      PASSED   [ 80%]
test_rotate.py::test_big_k       FAILED   [100%]

=================== 2 passed, 3 failed in 0.06s ===================
rotate([1,2,3,4,5], 2) -> [3,4,5,1,2]（期望 [4,5,1,2,3]）
方向反了：切片拼的是向左旋，向右旋应取 nums[-k:] + nums[:-k]。""",
        "test_cases": [
            {"input": "[1,2,3,4,5]\n2", "expected_output": "[4, 5, 1, 2, 3]"},
            {"input": "[1,2,3]\n0", "expected_output": "[1, 2, 3]"},
            {"input": "[1,2,3,4]\n1", "expected_output": "[4, 1, 2, 3]"},
            {"input": "[1]\n5", "expected_output": "[1]"},
            {"input": "[1,2,3,4,5,6]\n4", "expected_output": "[3, 4, 5, 6, 1, 2]"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0097",
        "title": "字符频次 · 计数不累加",
        "related_weakness": "字符串处理",
        "language": "python",
        "code": '''def most_frequent(s):
    """出现次数最多的字符 -- AI 生成，测试全挂，待修复"""
    counts = {}
    for ch in s:
        if ch in counts:
            counts[ch] = 1
        else:
            counts[ch] = 1
    return max(counts, key=counts.get)''',
        "failing_output": """$ pytest test_freq.py -v
test_freq.py::test_hello       FAILED   [ 20%]
test_freq.py::test_aaabbc      PASSED   [ 40%]
test_freq.py::test_xyz         PASSED   [ 60%]
test_freq.py::test_mississippi FAILED   [ 80%]
test_freq.py::test_abracadabra PASSED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
most_frequent("hello") -> 'h'（期望 'l'）
命中已存在的字符时把计数重置为 1，所有字符计数恒为 1，max 只能返回最先插入的字符。""",
        "test_cases": [
            {"input": "hello", "expected_output": "l"},
            {"input": "aaabbc", "expected_output": "a"},
            {"input": "xyz", "expected_output": "x"},
            {"input": "mississippi", "expected_output": "i"},
            {"input": "abracadabra", "expected_output": "a"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0098",
        "title": "括号匹配 · 空栈出栈",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def is_balanced(s):
    """括号匹配 -- AI 生成，测试全挂，待修复"""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if stack.pop() == pairs[ch]:
                continue
            return False
    return len(stack) == 0''',
        "failing_output": """$ pytest test_balanced.py -v
test_balanced.py::test_ok         PASSED   [ 17%]
test_balanced.py::test_mixed      PASSED   [ 33%]
test_balanced.py::test_mismatch   PASSED   [ 50%]
test_balanced.py::test_interleave PASSED   [ 67%]
test_balanced.py::test_extra_open PASSED   [ 83%]
test_balanced.py::test_stray      IndexError: pop from empty list  [100%]

=================== 5 passed, 1 failed in 0.07s ===================
is_balanced(")") -> IndexError: pop from empty list
出栈前没有判空：出现右括号而栈为空时直接崩溃，应返回 False。""",
        "test_cases": [
            {"input": "()", "expected_output": "True"},
            {"input": "()[]{}", "expected_output": "True"},
            {"input": "(]", "expected_output": "False"},
            {"input": "([)]", "expected_output": "False"},
            {"input": "((()", "expected_output": "False"},
            {"input": ")", "expected_output": "False"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0099",
        "title": "最大子数组和 · 不回退",
        "related_weakness": "动态规划状态设计",
        "language": "python",
        "code": '''def max_subarray(nums):
    """最大子数组和 -- AI 生成，测试全挂，待修复"""
    cur = nums[0]
    best = nums[0]
    for x in nums[1:]:
        cur = cur + x
        if cur > best:
            best = cur
    return best''',
        "failing_output": """$ pytest test_maxsub.py -v
test_maxsub.py::test_example     FAILED   [ 20%]
test_maxsub.py::test_single      PASSED   [ 40%]
test_maxsub.py::test_all_neg     PASSED   [ 60%]
test_maxsub.py::test_neg_then_pos PASSED  [ 80%]
test_maxsub.py::test_two_neg     FAILED   [100%]

=================== 3 passed, 2 failed in 0.06s ===================
max_subarray([-2,1,-3,4,-1,2,1,-5,4]) -> 2（期望 6）
max_subarray([-2,-1]) -> -2（期望 -1）
Kadane 漏了回退：cur 累计后从不与 x 取 max，负数把整段和一直拖到为负。""",
        "test_cases": [
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6"},
            {"input": "[1]", "expected_output": "1"},
            {"input": "[-1,-2,-3]", "expected_output": "-1"},
            {"input": "[5,4,-1,7,8]", "expected_output": "23"},
            {"input": "[-2,-1]", "expected_output": "-1"},
        ],
        "time_limit_sec": 600,
        "difficulty": 4,
    },
    {
        "id": "DEBUG-0100",
        "title": "字符串压缩 · 计数归零",
        "related_weakness": "字符串处理",
        "language": "python",
        "code": '''def compress(s):
    """字符串压缩 -- AI 生成，测试全挂，待修复"""
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(s[i - 1] + str(count))
            count = 0
    result.append(s[len(s) - 1] + str(count))
    return "".join(result)''',
        "failing_output": """$ pytest test_compress.py -v
test_compress.py::test_aabbb     FAILED   [ 20%]
test_compress.py::test_single    PASSED   [ 40%]
test_compress.py::test_aa        PASSED   [ 60%]
test_compress.py::test_ab        FAILED   [ 80%]
test_compress.py::test_aab       FAILED   [100%]

=================== 2 passed, 3 failed in 0.05s ===================
compress("aabbb") -> 'a2b2'（期望 'a2b3'）
compress("ab") -> 'a1b0'（期望 'a1b1'）
一组字符结束时把 count 重置为 0，下一段从 0 开始计导致少 1；应重置为 1。""",
        "test_cases": [
            {"input": "aabbb", "expected_output": "a2b3"},
            {"input": "a", "expected_output": "a1"},
            {"input": "aa", "expected_output": "a2"},
            {"input": "ab", "expected_output": "a1b1"},
            {"input": "aab", "expected_output": "a2b1"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0101",
        "title": "回文判断 · 比错了对象",
        "related_weakness": "字符串处理",
        "language": "python",
        "code": '''def is_palindrome(s):
    """回文判断 -- AI 生成，测试全挂，待修复"""
    cleaned = "".join(ch.lower() for ch in s if ch.isalnum())
    for i in range(len(cleaned) // 2):
        if cleaned[i] != cleaned[i + 1]:
            return False
    return True''',
        "failing_output": """$ pytest test_pal.py -v
test_pal.py::test_phrase      FAILED   [ 20%]
test_pal.py::test_not_pal     PASSED   [ 40%]
test_pal.py::test_blank       PASSED   [ 60%]
test_pal.py::test_abba        FAILED   [ 80%]
test_pal.py::test_abcba       FAILED   [100%]

=================== 2 passed, 3 failed in 0.05s ===================
is_palindrome("abba") -> False（期望 True）
比较的是相邻字符而不是首尾对称字符：cleaned[i] != cleaned[i+1] 只在相邻相同时才通过。""",
        "test_cases": [
            {"input": "A man, a plan, a canal: Panama", "expected_output": "True"},
            {"input": "race a car", "expected_output": "False"},
            {"input": " ", "expected_output": "True"},
            {"input": "abba", "expected_output": "True"},
            {"input": "abcba", "expected_output": "True"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0102",
        "title": "链表反转 · 返回了空指针",
        "related_weakness": "链表操作",
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
        cur = next;
    }
    return cur;
}''',
        "failing_output": """$ gcc -o test test.c && ./test
test_reverse("1 2 3")      -> (空)       期望 "3 2 1"    FAIL
test_reverse("42")         -> (空)       期望 "42"        FAIL
test_reverse("4 3 2 1")    -> (空)       期望 "1 2 3 4"   FAIL
test_reverse("-1 -2")      -> (空)       期望 "-2 -1"     FAIL
test_reverse("5 4 3 2 1")  -> (空)       期望 "1 2 3 4 5" FAIL

======================== 0/5 tests passed ========================
返回的是 cur（循环结束后已是 NULL），应返回翻转后的新头 prev。""",
        "test_cases": [
            {"input": "3\n1 2 3", "expected_output": "3 2 1"},
            {"input": "1\n42", "expected_output": "42"},
            {"input": "4\n4 3 2 1", "expected_output": "1 2 3 4"},
            {"input": "2\n-1 -2", "expected_output": "-2 -1"},
            {"input": "5\n5 4 3 2 1", "expected_output": "1 2 3 4 5"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0103",
        "title": "移动零 · 末尾没补零",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def move_zeros(nums):
    """把 0 移到末尾 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    idx = 0
    for i in range(n):
        if nums[i] != 0:
            nums[idx] = nums[i]
            idx += 1
    return nums''',
        "failing_output": """$ pytest test_zeros.py -v
test_zeros.py::test_mixed      FAILED   [ 20%]
test_zeros.py::test_zero_only  PASSED   [ 40%]
test_zeros.py::test_no_zero    PASSED   [ 60%]
test_zeros.py::test_two_zeros  FAILED   [ 80%]
test_zeros.py::test_one_zero   PASSED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
move_zeros([0,1,0,3,12]) -> [1,3,12,3,12]（期望 [1,3,12,0,0]）
只把非零元素搬到前面，末尾没补 0，原尾元素残留在后面。""",
        "test_cases": [
            {"input": "[0,1,0,3,12]", "expected_output": "[1, 3, 12, 0, 0]"},
            {"input": "[0]", "expected_output": "[0]"},
            {"input": "[0,0,1]", "expected_output": "[1, 0, 0]"},
            {"input": "[1,0]", "expected_output": "[1, 0]"},
            {"input": "[1,2,3]", "expected_output": "[1, 2, 3]"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
    },
    {
        "id": "DEBUG-0104",
        "title": "字符串转整数 · 空串崩溃",
        "related_weakness": "字符串处理",
        "language": "python",
        "code": '''def str_to_int(s):
    """字符串转整数 -- AI 生成，测试全挂，待修复"""
    s = s.strip()
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
        "failing_output": """$ pytest test_atoi.py -v
test_atoi.py::test_positive    PASSED   [ 20%]
test_atoi.py::test_negative    PASSED   [ 40%]
test_atoi.py::test_words_tail  PASSED   [ 60%]
test_atoi.py::test_words_head  PASSED   [ 80%]
test_atoi.py::test_empty       IndexError: string index out of range  [100%]

=================== 4 passed, 1 failed in 0.05s ===================
str_to_int("") -> IndexError: string index out of range
strip 之后直接读 s[0]，没先判空；空字符串应返回 0。""",
        "test_cases": [
            {"input": "42", "expected_output": "42"},
            {"input": "   -42", "expected_output": "-42"},
            {"input": "4193 with words", "expected_output": "4193"},
            {"input": "words 987", "expected_output": "0"},
            {"input": "", "expected_output": "0"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0105",
        "title": "矩阵转置 · 下标写反",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def transpose(matrix):
    """矩阵转置 -- AI 生成，测试全挂，待修复"""
    rows = len(matrix)
    cols = len(matrix[0])
    result = [[0] * rows for _ in range(cols)]
    for i in range(rows):
        for j in range(cols):
            result[i][j] = matrix[j][i]
    return result''',
        "failing_output": """$ pytest test_transpose.py -v
test_transpose.py::test_1x1     PASSED   [ 20%]
test_transpose.py::test_2x2     PASSED   [ 40%]
test_transpose.py::test_2x3     IndexError: list index out of range  [ 60%]
test_transpose.py::test_3x2     IndexError: list index out of range  [ 80%]
test_transpose.py::test_3x3     PASSED   [100%]

=================== 3 passed, 2 failed in 0.06s ===================
transpose([[1,2,3],[4,5,6]]) -> IndexError: list index out of range
赋值写反了：result[i][j] = matrix[j][i]，非方阵时 j 越界；应改为 result[j][i] = matrix[i][j]。""",
        "test_cases": [
            {"input": "[[1,2,3],[4,5,6]]", "expected_output": "[[1, 4], [2, 5], [3, 6]]"},
            {"input": "[[1]]", "expected_output": "[[1]]"},
            {"input": "[[1,2],[3,4]]", "expected_output": "[[1, 3], [2, 4]]"},
            {"input": "[[5]]", "expected_output": "[[5]]"},
            {"input": "[[1,2],[3,4],[5,6]]", "expected_output": "[[1, 3, 5], [2, 4, 6]]"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0106",
        "title": "约瑟夫环 · 下标多算一",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def josephus(n, k):
    """约瑟夫环最后幸存者 -- AI 生成，测试全挂，待修复"""
    people = list(range(1, n + 1))
    idx = 0
    while len(people) > 1:
        idx = (idx + k) % len(people)
        people.pop(idx)
    return people[0]''',
        "failing_output": """$ pytest test_josephus.py -v
test_josephus.py::test_5_3      FAILED   [ 20%]
test_josephus.py::test_1_1      PASSED   [ 40%]
test_josephus.py::test_7_3      FAILED   [ 60%]
test_josephus.py::test_3_2      FAILED   [ 80%]
test_josephus.py::test_10_4     FAILED   [100%]

=================== 1 passed, 4 failed in 0.06s ===================
josephus(5,3) -> 1（期望 4）
出列下标多算了 1：idx = (idx + k) % n 把当前人也数了一次，应改为 (idx + k - 1) % n。""",
        "test_cases": [
            {"input": "5 3", "expected_output": "4"},
            {"input": "1 1", "expected_output": "1"},
            {"input": "7 3", "expected_output": "4"},
            {"input": "3 2", "expected_output": "3"},
            {"input": "10 4", "expected_output": "5"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0107",
        "title": "缺失最小正数 · 边界值",
        "related_weakness": "边界条件处理",
        "language": "python",
        "code": '''def first_missing_positive(nums):
    """第一个缺失的正整数 -- AI 生成，测试全挂，待修复"""
    n = len(nums)
    present = [False] * (n + 1)
    for x in nums:
        if 1 <= x <= n:
            present[x] = True
    for i in range(1, n + 1):
        if not present[i]:
            return i
    return n''',
        "failing_output": """$ pytest test_fmp.py -v
test_fmp.py::test_1_2_0        PASSED   [ 20%]
test_fmp.py::test_3_4_neg_1_1  PASSED   [ 40%]
test_fmp.py::test_big          PASSED   [ 60%]
test_fmp.py::test_1_2_3        FAILED   [ 80%]
test_fmp.py::test_single       FAILED   [100%]

=================== 3 passed, 2 failed in 0.05s ===================
first_missing_positive([1,2,3]) -> 3（期望 4）
1..n 全部出现时返回 n，但缺失的最小正整数是 n+1；应在循环后返回 n + 1。""",
        "test_cases": [
            {"input": "[1,2,0]", "expected_output": "3"},
            {"input": "[3,4,-1,1]", "expected_output": "2"},
            {"input": "[7,8,9,11,12]", "expected_output": "1"},
            {"input": "[1,2,3]", "expected_output": "4"},
            {"input": "[1]", "expected_output": "2"},
        ],
        "time_limit_sec": 600,
        "difficulty": 5,
    },
    {
        "id": "DEBUG-0108",
        "title": "快乐数 · 死循环",
        "related_weakness": "递归出口设计",
        "language": "python",
        "code": '''def is_happy(n):
    """快乐数 -- AI 生成，测试全挂，待修复"""
    while n != 1:
        n = sum(int(d) ** 2 for d in str(n))
    return True''',
        "failing_output": """$ pytest test_happy.py -v
test_happy.py::test_19          PASSED   [ 20%]
test_happy.py::test_1           PASSED   [ 40%]
test_happy.py::test_2           TIMEOUT  [ 60%] 执行超过 5s（疑似死循环）
test_happy.py::test_7           PASSED   [ 80%]
test_happy.py::test_4           TIMEOUT  [100%] 执行超过 5s（疑似死循环）

=================== 3 passed, 2 timeout in 15.40s ==================
is_happy(2) 卡死：没有记录已访问过的数字，非快乐数在 4-16-37-... 循环里永远出不来。需要加 seen 集合判重。""",
        "test_cases": [
            {"input": "19", "expected_output": "True"},
            {"input": "2", "expected_output": "False"},
            {"input": "1", "expected_output": "True"},
            {"input": "7", "expected_output": "True"},
            {"input": "4", "expected_output": "False"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0109",
        "title": "链表中间节点 · 快慢同速",
        "related_weakness": "链表操作",
        "language": "c",
        "code": '''#include <stdio.h>
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
        fast = fast->next;
    }
    return slow;
}''',
        "failing_output": """$ gcc -o test test.c && ./test
test_middle("1 2 3")    -> 3       期望 2      FAIL
test_middle("42")       -> 42      期望 42     PASS
test_middle("1 2 3 4")  -> 4       期望 3      FAIL
test_middle("7 8")      -> 8       期望 8      PASS
test_middle("5 4 3 2 1")-> 1       期望 3      FAIL

======================== 2/5 tests passed ========================
fast 每次只走一步，slow 也跟着一直走到尾；fast 应每次跳两步，slow 才能停在中间。""",
        "test_cases": [
            {"input": "3\n1 2 3", "expected_output": "2"},
            {"input": "1\n42", "expected_output": "42"},
            {"input": "4\n1 2 3 4", "expected_output": "3"},
            {"input": "2\n7 8", "expected_output": "8"},
            {"input": "5\n5 4 3 2 1", "expected_output": "3"},
        ],
        "time_limit_sec": 600,
        "difficulty": 3,
    },
    {
        "id": "DEBUG-0110",
        "title": "反转单词顺序 · 反转错了对象",
        "related_weakness": "字符串处理",
        "language": "python",
        "code": '''def reverse_words(s):
    """反转单词顺序 -- AI 生成，测试全挂，待修复"""
    words = s.split()
    return " ".join(word[::-1] for word in words)''',
        "failing_output": """$ pytest test_rwords.py -v
test_rwords.py::test_sentence   FAILED   [ 20%]
test_rwords.py::test_spaces     FAILED   [ 40%]
test_rwords.py::test_single     PASSED   [ 60%]
test_rwords.py::test_hello      FAILED   [ 80%]
test_rwords.py::test_multi_sp   FAILED   [100%]

=================== 1 passed, 4 failed in 0.05s ===================
reverse_words("the sky is blue") -> 'eht yks si eulb'（期望 'blue is sky the'）
对每个单词做了字符反转，而没有反转单词顺序；应 reversed(words) 而不是 word[::-1]。""",
        "test_cases": [
            {"input": "the sky is blue", "expected_output": "blue is sky the"},
            {"input": "  hello world  ", "expected_output": "world hello"},
            {"input": "a", "expected_output": "a"},
            {"input": "hello", "expected_output": "hello"},
            {"input": "  a   b ", "expected_output": "b a"},
        ],
        "time_limit_sec": 600,
        "difficulty": 2,
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
# 五场考试：
#   cert-pointer:   指针能力认证（15 分钟，80 分及格）
#   cert-recursion: 递归能力认证（15 分钟，80 分及格）
#   cert-sorting:   排序算法认证（15 分钟，80 分及格）
#   cert-linkedlist:链表操作认证（15 分钟，80 分及格）
#   placement:      定级测试（5 分钟，不设及格线，用于评估新用户水平）
# ──────────────────────────────────────────────────────────────────

# (exam_id, topic, time_limit_min, pass_score)
CERT_EXAMS = [
    ("cert-pointer", "指针", 15, 80),
    ("cert-recursion", "递归", 15, 80),
    ("cert-sorting", "排序算法", 15, 80),
    ("cert-linkedlist", "链表操作", 15, 80),
    ("placement", "定级测试", 5, 0),
]

# 认证考试 -> 关联知识点（考试级粒度：每场正式考试单一主题）。
# 认证判分后按逐题对错对该知识点记掌握度事件，参与个性化推荐。
# placement 不在此表：它覆盖面广，提交时对全部知识点统一写定级事件。
CERT_EXAM_KNOWLEDGE_POINT = {
    "cert-pointer": "指针的内存布局",
    "cert-recursion": "递归出口设计",
    "cert-sorting": "排序算法实现",
    "cert-linkedlist": "链表操作",
}

# ──────────────────────────────────────────────────────────────────
# 认证考试题目 (CERT_QUESTIONS)
# ──────────────────────────────────────────────────────────────────
# 数据结构：(exam_id, qid, kind, prompt, options, starter_code,
#            answer_correct, answer_includes, test_cases, sort)
#   exam_id:         所属考试 ID
#   qid:            题目编号（q1/q2... 认证考试 / p1/p2... 定级测试）
#   kind:           题型（mcq=选择题 / code=编程题）
#   prompt:         题干文本
#   options:        选择题选项列表（编程题为 None）
#   starter_code:   编程题起始代码模板（选择题为 None）
#   answer_correct: 选择题正确答案（服务端比对，绝不下发）
#   answer_includes:编程题关键片段（用户代码含此即算正确；Judge0 不可用时降级用。
#                   判定语义：去除全部空白后，所有片段都必须命中；单个片段内可用
#                   "||" 分隔多个备选写法（任一命中即算该片段命中），用于兼容
#                   同一算法的多种正确实现）
#   test_cases:     编程题测试用例（Judge0 判题用，每项 {"input", "expected_output"}；
#                   选择题为 None；服务端秘密，绝不下发）
#   sort:           显示排序（最后一个字段，省略字段名）
#
# 答案安全策略：answer_correct / answer_includes / test_cases 仅存在于服务端，
# 前端 API 响应绝不包含这些字段，防止作弊。
# ──────────────────────────────────────────────────────────────────

# (exam_id, qid, kind, prompt, options, starter_code, answer_correct, answer_includes, test_cases, sort)
CERT_QUESTIONS = [
    # ── 指针能力认证（cert-pointer）6 题：4 MCQ + 2 code ──
    ("cert-pointer", "q1", "mcq", "int a = 5; int *p = &a; *p = 10; 之后 a 的值是？",
     ["5", "10", "未定义", "编译错误"], None, "10", None, None, 1),
    ("cert-pointer", "q2", "mcq", "free(p) 之后，指针 p 本身变成什么？",
     ["NULL", "悬空指针（值不变但目标已释放）", "自动销毁", "指向堆顶"], None,
     "悬空指针（值不变但目标已释放）", None, None, 2),
    ("cert-pointer", "q3", "mcq", "对 int arr[10]，arr 与 &arr[0] 的关系是？",
     ["值相等", "类型完全相同", "arr 多一级间接", "毫无关系"], None, "值相等", None, None, 3),
    ("cert-pointer", "q4", "mcq", "32 位系统下 int *p; p++ 让 p 前进多少字节？",
     ["1", "2", "4", "8"], None, "4", None, None, 4),
    ("cert-pointer", "q5", "code", "手写 swap：通过指针交换两个 int 的值。",
     None, "void swap(int *a, int *b) {\n    \n}", None, ["*a=*b", "*b="],
     [{"input": "3 5", "expected_output": "5 3"},
      {"input": "-1 7", "expected_output": "7 -1"},
      {"input": "0 0", "expected_output": "0 0"},
      {"input": "100 -100", "expected_output": "-100 100"}], 5),
    ("cert-pointer", "q6", "code", "写一个函数 find，接收 int* 数组首地址和长度，返回最大值所在位置的指针；空数组返回 NULL。",
     None, "#include <stdlib.h>\nint* find(int *arr, int n) {\n    \n}", None,
     ["NULL", "arr[i]||*(arr+i"],
     [{"input": "0", "expected_output": "NULL"},
      {"input": "1\n42", "expected_output": "42 0"},
      {"input": "3\n10 5 20", "expected_output": "20 2"},
      {"input": "4\n-1 -5 -2 -9", "expected_output": "-1 0"}], 6),
    # ── 定级测试（placement）5 题：3 MCQ + 2 code ──
    ("placement", "p1", "mcq", "读代码找 bug：for (i = 0; i <= n; i++) sum += arr[i]; 问题在哪？",
     ["越界访问 arr[n]", "sum 类型不对", "循环方向错了", "没有 bug"], None, "越界访问 arr[n]", None, None, 1),
    ("placement", "p2", "mcq", "下面哪段代码会死循环？",
     ["while (x > 0) { x -= 2; }（x 为奇数正数）", "for (i = 0; i < 10; i++)",
      "while (x != 0) { x = x - 2; }（x 为奇数正数）", "do { x--; } while (x > 0);"], None,
     "while (x != 0) { x = x - 2; }（x 为奇数正数）", None, None, 2),
    ("placement", "p3", "mcq", "测试发现 quicksort([2,2,1]) 返回 [1,2]，最可能丢了什么？",
     ["与 pivot 相等的元素", "最小值", "第一个元素", "什么都不缺"], None, "与 pivot 相等的元素", None, None, 3),
    ("placement", "p4", "code", "手写：返回字符串中第一个不重复的字符下标，没有则返回 -1。",
     None, "def first_unique(s):\n    ", None, ["==1", "return-1"],
     [{"input": "leetcode", "expected_output": "0"},
      {"input": "loveleetcode", "expected_output": "2"},
      {"input": "aabb", "expected_output": "-1"},
      {"input": "a", "expected_output": "0"},
      {"input": "abab", "expected_output": "-1"}], 4),
    ("placement", "p5", "code", "手写：判断一个整数是否为 2 的幂。",
     None, "def is_power_of_two(n):\n    ", None, ["n>0||n<=0||n<1", "n&(n-1)||n%2||n//=2"],
     [{"input": "1", "expected_output": "True"},
      {"input": "16", "expected_output": "True"},
      {"input": "3", "expected_output": "False"},
      {"input": "0", "expected_output": "False"},
      {"input": "1024", "expected_output": "True"}], 5),
    # ── 递归能力认证（cert-recursion）6 题：4 MCQ + 2 code ──
    ("cert-recursion", "q1", "mcq", "递归函数缺少基例（终止条件）会导致什么？",
     ["编译错误", "无限递归导致栈溢出", "返回 None", "语法错误"], None,
     "无限递归导致栈溢出", None, None, 1),
    ("cert-recursion", "q2", "mcq", "def f(n):\n    if n <= 1: return 1\n    return n * f(n-1)\n上述函数计算的是什么？",
     ["斐波那契数", "阶乘", "幂运算", "排列数"], None, "阶乘", None, None, 2),
    ("cert-recursion", "q3", "mcq", "朴素递归实现斐波那契数列 fib(n) = fib(n-1) + fib(n-2) 的主要性能问题是什么？",
     ["递归层数太深", "大量重复计算（同一 fib(k) 被多次调用）", "返回值溢出", "没有性能问题"], None,
     "大量重复计算（同一 fib(k) 被多次调用）", None, None, 3),
    ("cert-recursion", "q4", "mcq", "尾递归优化（tail call optimization）的好处是什么？",
     ["减少代码行数", "复用栈帧，避免栈溢出", "提高数值精度", "自动并行执行"], None,
     "复用栈帧，避免栈溢出", None, None, 4),
    ("cert-recursion", "q5", "code", "手写：用递归实现字符串反转。例如 reverse_str(\"hello\") 返回 \"olleh\"。",
     None, "def reverse_str(s):\n    ", None, ["reverse_str(s[1:])||reverse_str(s[:-1])||s[::-1]"],
     [{"input": "hello", "expected_output": "olleh"},
      {"input": "a", "expected_output": "a"},
      {"input": "", "expected_output": ""},
      {"input": "abcdef", "expected_output": "fedcba"},
      {"input": "12345", "expected_output": "54321"}], 5),
    ("cert-recursion", "q6", "code", "手写：用递归实现幂运算 power(base, exp)，返回 base 的 exp 次方。不使用 ** 运算符。",
     None, "def power(base, exp):\n    ", None, ["return1", "power(base,exp-1)||power(base,exp-2)||power(base,exp//2)"],
     [{"input": "2 3", "expected_output": "8"},
      {"input": "5 0", "expected_output": "1"},
      {"input": "3 4", "expected_output": "81"},
      {"input": "-2 3", "expected_output": "-8"},
      {"input": "2 10", "expected_output": "1024"}], 6),
    # ── 排序算法认证（cert-sorting）6 题：4 MCQ + 2 code ──
    ("cert-sorting", "q1", "mcq", "对一个基本有序的数组做冒泡排序，若实现加入了提前退出标志，最优时间复杂度是？",
     ["O(n)", "O(n log n)", "O(n²)", "O(1)"], None, "O(n)", None, None, 1),
    ("cert-sorting", "q2", "mcq", "快速排序的平均时间复杂度是？",
     ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], None, "O(n log n)", None, None, 2),
    ("cert-sorting", "q3", "mcq", "归并排序的空间复杂度是？",
     ["O(n)", "O(1)", "O(log n)", "O(n log n)"], None, "O(n)", None, None, 3),
    ("cert-sorting", "q4", "mcq", "下列哪个排序算法是不稳定的？",
     ["快速排序", "冒泡排序", "插入排序", "归并排序"], None, "快速排序", None, None, 4),
    ("cert-sorting", "q5", "code", "手写：实现冒泡排序 bubble_sort(arr)，升序排序并返回数组。",
     None, "def bubble_sort(arr):\n    ", None,
     ["arr[j+1]||arr[i+1]", "arr[j]>arr[j+1]||arr[j+1]<arr[j]||arr[i]>arr[i+1]||arr[i+1]<arr[i]"],
     [{"input": "[3,1,2]", "expected_output": "[1, 2, 3]"},
      {"input": "[]", "expected_output": "[]"},
      {"input": "[5]", "expected_output": "[5]"},
      {"input": "[5,4,3,2,1]", "expected_output": "[1, 2, 3, 4, 5]"},
      {"input": "[2,2,1,1]", "expected_output": "[1, 1, 2, 2]"}], 5),
    ("cert-sorting", "q6", "code", "手写：实现快速排序 quicksort(arr)，升序排序并返回数组。",
     None, "def quicksort(arr):\n    ", None, ["pivot||partition", "quicksort("],
     [{"input": "[3,1,2]", "expected_output": "[1, 2, 3]"},
      {"input": "[4,2,2,8]", "expected_output": "[2, 2, 4, 8]"},
      {"input": "[]", "expected_output": "[]"},
      {"input": "[1]", "expected_output": "[1]"},
      {"input": "[9,7,5,3,1]", "expected_output": "[1, 3, 5, 7, 9]"}], 6),
    # ── 链表操作认证（cert-linkedlist）6 题：4 MCQ + 2 code ──
    ("cert-linkedlist", "q1", "mcq", "在单链表头部插入一个新节点的时间复杂度是？",
     ["O(1)", "O(n)", "O(log n)", "O(n²)"], None, "O(1)", None, None, 1),
    ("cert-linkedlist", "q2", "mcq", "迭代反转单链表时，通常需要同时维护几个指针？",
     ["3 个（prev / cur / next）", "1 个", "2 个", "4 个"], None,
     "3 个（prev / cur / next）", None, None, 2),
    ("cert-linkedlist", "q3", "mcq", "判断单链表是否存在环，常用的方法有？",
     ["快慢双指针", "哈希集合记录已访问节点", "两者都可", "反转链表后比较"], None, "两者都可", None, None, 3),
    ("cert-linkedlist", "q4", "mcq", "已知某节点的前驱节点，删除该节点的时间复杂度是？",
     ["O(1)", "O(n)", "O(log n)", "O(n log n)"], None, "O(1)", None, None, 4),
    ("cert-linkedlist", "q5", "code", "手写：实现 remove_nth_from_end(arr, n)，删除数组倒数第 n 个元素并返回新数组（模拟删除链表倒数第 n 个节点）。",
     None, "def remove_nth_from_end(arr, n):\n    ", None, ["len(arr)-n", "return"],
     [{"input": "[1,2,3,4,5]\n2", "expected_output": "[1, 2, 3, 5]"},
      {"input": "[1,2,3,4,5]\n1", "expected_output": "[1, 2, 3, 4]"},
      {"input": "[1]\n1", "expected_output": "[]"},
      {"input": "[1,2]\n2", "expected_output": "[2]"},
      {"input": "[1,2,3]\n3", "expected_output": "[2, 3]"}], 5),
    ("cert-linkedlist", "q6", "code", "手写：实现 merge_two_sorted(a, b)，合并两个升序数组并返回升序数组（模拟合并两个有序链表）。",
     None, "def merge_two_sorted(a, b):\n    ", None, ["while||sorted(", "append||sorted("],
     [{"input": "[1,2,4]\n[1,3,4]", "expected_output": "[1, 1, 2, 3, 4, 4]"},
      {"input": "[]\n[]", "expected_output": "[]"},
      {"input": "[]\n[0]", "expected_output": "[0]"},
      {"input": "[1,3,5]\n[2,4,6]", "expected_output": "[1, 2, 3, 4, 5, 6]"},
      {"input": "[5]\n[1]", "expected_output": "[1, 5]"}], 6),
]


async def seed_deck(db: AsyncSession) -> None:
    """灌入种子数据（幂等）。

    执行流程：
    1. 幂等检查：如果知识点表已有数据 → 跳过所有插入（安全可重复执行）
    2. 插入知识点（13 个）
    3. 插入审查关卡（30 个），然后 await db.flush() 确保外键可用
    4. 插入注入缺陷（子表，依赖审查关卡的外键）
    5. 插入竞技场挑战（20 个）
    6. 插入认证考试（5 个），然后 await db.flush() 确保外键可用
    7. 插入认证题目（29 道，依赖考试的外键）
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
    # scalar 在无记录时可能返回 None（func.count 亦可能为 0），
    # `count and count > 0` 用一次判断同时兜住 None 与 0 两种"空表"情况
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
        # 解包元组：每个题目有 10 个字段
        (
            exam_id,
            qid,
            kind,
            prompt,
            options,
            starter_code,
            answer_correct,
            answer_includes,
            test_cases,
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
                test_cases=test_cases,
                sort_order=sort_order,
            )
        )

    # ── 步骤 8：提交事务 ──
    # 所有数据一次性提交，保证原子性——要么全部成功，要么全部回滚
    await db.commit()
