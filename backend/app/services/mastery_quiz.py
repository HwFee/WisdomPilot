"""
Mastery Quiz Service - 精进之路测试服务

提供知识点获取、AI 生成测试题、提交测试等功能。
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.chapter_mastery import ChapterMastery
from app.services.ai import ai_service
from app.schemas.mastery_quiz import (
    MasteryQuizGenerateRequest,
    MasteryQuizGenerateResponse,
    MasteryQuizSubmitRequest,
    MasteryQuizSubmitResponse,
    MasteryQuizQuestion,
    QuestionResult,
    UserProfileForQuiz,
    KnowledgePoint,
)
from app.utils.time import utc_now


class MasteryQuizSession(BaseModel):
    """测试会话模型（内存中临时存储）"""
    id: str
    user_id: str
    course_id: int
    chapter_id: int
    questions: list[dict]
    created_at: datetime
    expires_at: datetime


class MasteryQuizService:
    """精进之路测试服务

    注意：当前使用内存存储会话，适用于单实例部署。
    生产环境多实例部署时，应配置 Redis 存储：

    配置方式：
    1. 设置环境变量: REDIS_URL=redis://localhost:6379/0
    2. 安装依赖: pip install redis
    3. 将 _sessions 替换为 Redis 存储

    TODO: 添加 Redis 存储支持
    """

    # 内存中的会话存储（单实例适用）
    # 生产环境多实例应使用 Redis: {session_id: MasteryQuizSession}
    _sessions: dict[str, MasteryQuizSession] = {}

    async def get_chapter_knowledge_content(
        self,
        db: AsyncSession,
        chapter_id: int,
        user_id: str,
    ) -> Optional[dict]:
        """
        获取章节知识点内容

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            user_id: 用户ID

        Returns:
            知识点内容字典，包含章节信息和知识点列表
        """
        chapter, course = await self._get_chapter_with_course(db, chapter_id)
        if not chapter:
            return None

        # 生成或获取知识点
        knowledge_data = await self._generate_or_get_knowledge(
            db=db,
            chapter=chapter,
            course=course,
            user_id=user_id
        )

        if not knowledge_data:
            return None

        return {
            "chapter_id": chapter.id,
            "chapter_title": chapter.title,
            "knowledge_points": knowledge_data.get("knowledge_points", []),
            "total_points": len(knowledge_data.get("knowledge_points", [])),
            "estimated_time": knowledge_data.get("estimated_time", 15),
            "prerequisites": None,
            "next_chapters": None,
        }

    async def generate_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryQuizGenerateRequest,
    ) -> dict:
        """
        生成个性化测试题

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 生成请求

        Returns:
            生成结果，包含题目列表
        """
        # 获取章节信息
        chapter = await self._get_chapter(db, request.chapter_id)
        if not chapter:
            return {
                "success": False,
                "session_id": "",
                "questions": [],
                "user_profile_used": False,
                "weak_points_addressed": [],
                "message": "未找到章节"
            }

        # 获取用户画像
        user_profile = await self._get_user_profile(
            db=db,
            user_id=user_id,
            course_id=request.course_id
        )

        # 生成测试题
        questions = await self._generate_quiz_questions(
            chapter=chapter,
            user_profile=user_profile,
            request=request
        )

        if not questions:
            return {
                "success": False,
                "session_id": "",
                "questions": [],
                "user_profile_used": user_profile is not None,
                "weak_points_addressed": [],
                "message": "AI 服务暂时不可用，请稍后重试"
            }

        # 创建会话
        session_id = await self._create_quiz_session(
            user_id=user_id,
            course_id=request.course_id,
            chapter_id=request.chapter_id,
            questions=questions
        )

        # 提取针对的薄弱点
        weak_points_addressed = []
        if user_profile and user_profile.get("weak_knowledge_points"):
            weak_points = set(user_profile["weak_knowledge_points"])
            for q in questions:
                for kp in q.get("knowledge_points", []):
                    if kp in weak_points:
                        weak_points_addressed.append(kp)
            weak_points_addressed = list(set(weak_points_addressed))

        return {
            "success": True,
            "session_id": session_id,
            "questions": questions,
            "user_profile_used": user_profile is not None,
            "weak_points_addressed": weak_points_addressed,
            "message": f"成功生成 {len(questions)} 道测试题"
        }

    async def submit_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryQuizSubmitRequest,
    ) -> dict:
        """
        提交测试结果

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 提交请求

        Returns:
            测试结果
        """
        # 获取会话
        session = await self._get_quiz_session(request.session_id)
        if not session:
            return {
                "success": False,
                "session_id": request.session_id,
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0,
                "xp_earned": 0,
                "mastery_points_earned": 0,
                "results": [],
                "recommendations": [],
                "passed": False,
                "message": "会话不存在或已过期"
            }

        # 验证用户
        if session.user_id != user_id:
            return {
                "success": False,
                "session_id": request.session_id,
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0,
                "xp_earned": 0,
                "mastery_points_earned": 0,
                "results": [],
                "recommendations": [],
                "passed": False,
                "message": "无权访问此会话"
            }

        # 评估答案
        evaluation = await self._evaluate_answers(
            session=session,
            answers=request.answers
        )

        # 计算经验值和掌握点
        accuracy = evaluation["correct_count"] / evaluation["total_count"] if evaluation["total_count"] > 0 else 0
        xp_earned = int(accuracy * 50)  # 最高 50 XP
        mastery_points_earned = int(accuracy * 20)  # 最高 20 掌握点

        # 更新用户进度
        await self._update_user_progress(
            db=db,
            user_id=user_id,
            chapter_id=session.chapter_id,
            correct_count=evaluation["correct_count"],
            total_count=evaluation["total_count"]
        )

        # 生成学习建议
        recommendations = self._generate_recommendations(
            results=evaluation["results"],
            accuracy=accuracy
        )

        # 清理会话
        self._sessions.pop(request.session_id, None)

        return {
            "success": True,
            "session_id": request.session_id,
            "total_questions": evaluation["total_count"],
            "correct_answers": evaluation["correct_count"],
            "accuracy": accuracy,
            "xp_earned": xp_earned,
            "mastery_points_earned": mastery_points_earned,
            "results": evaluation["results"],
            "recommendations": recommendations,
            "passed": accuracy >= 0.8,
            "message": "提交成功" + ("，恭喜通过！" if accuracy >= 0.8 else "")
        }

    # ========================================
    # Private Helper Methods
    # ========================================

    async def _get_chapter_with_course(
        self,
        db: AsyncSession,
        chapter_id: int
    ) -> tuple[Optional[Chapter], Optional[Course]]:
        """获取章节和关联的课程"""
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            return None, None

        course_result = await db.execute(
            select(Course).where(Course.id == chapter.course_id)
        )
        course = course_result.scalar_one_or_none()

        return chapter, course

    async def _get_chapter(self, db: AsyncSession, chapter_id: int) -> Optional[Chapter]:
        """获取章节"""
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        return result.scalar_one_or_none()

    async def _generate_or_get_knowledge(
        self,
        db: AsyncSession,
        chapter: Chapter,
        course: Optional[Course],
        user_id: str,
    ) -> Optional[dict]:
        """生成或获取知识点"""
        # 先尝试使用预设知识点
        preset_knowledge = self._get_preset_knowledge(chapter)
        if preset_knowledge:
            return preset_knowledge

        if not ai_service.is_configured():
            # 返回默认知识点
            return {
                "knowledge_points": [
                    {
                        "id": f"kp_{chapter.id}_default",
                        "title": chapter.title,
                        "content": chapter.description or "本章节的知识点内容正在生成中...",
                        "examples": [],
                        "difficulty": 1,
                        "related_points": []
                    }
                ],
                "cached": False
            }

        # 使用 AI 生成知识点
        knowledge_data = await ai_service.generate_knowledge_content(
            chapter_title=chapter.title,
            chapter_description=chapter.description or "",
            course_name=course.name if course else "编程"
        )

        if not knowledge_data:
            return {
                "knowledge_points": [
                    {
                        "id": f"kp_{chapter.id}_default",
                        "title": chapter.title,
                        "content": chapter.description or "知识点内容",
                        "examples": [],
                        "difficulty": 1,
                        "related_points": []
                    }
                ],
                "cached": False
            }

        knowledge_data["cached"] = False
        return knowledge_data

    def _get_preset_knowledge(self, chapter: Chapter) -> Optional[dict]:
        """获取预设的知识点内容"""
        # C语言课程预设知识点
        c_knowledge_map = {
            "C语言入门": [
                {
                    "id": "c_intro_1",
                    "title": "程序的基本结构",
                    "content": "C语言程序由一个或多个函数组成，必须包含main函数作为程序入口。程序从main函数开始执行，到main函数结束。基本结构包括：预处理指令、函数定义、变量声明、语句和注释。",
                    "examples": [
                        "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}"
                    ],
                    "difficulty": 1,
                    "related_points": ["函数", "预处理指令"]
                },
                {
                    "id": "c_intro_2",
                    "title": "变量与数据类型",
                    "content": "C语言的基本数据类型包括：int（整数）、float（单精度浮点数）、double（双精度浮点数）、char（字符）。变量必须先声明后使用，声明时指定类型和名称。",
                    "examples": [
                        "int age = 25;\nfloat price = 99.9;\nchar grade = 'A';\ndouble pi = 3.14159265358979;"
                    ],
                    "difficulty": 1,
                    "related_points": ["整数类型", "浮点类型"]
                },
                {
                    "id": "c_intro_3",
                    "title": "输入输出函数",
                    "content": "printf()用于格式化输出，scanf()用于格式化输入。常用格式说明符：%d（整数）、%f（浮点数）、%c（字符）、%s（字符串）。注意scanf中变量前要加&取地址符。",
                    "examples": [
                        "int num;\nprintf(\"请输入一个整数: \");\nscanf(\"%d\", &num);\nprintf(\"你输入的是: %d\\n\", num);"
                    ],
                    "difficulty": 1,
                    "related_points": ["格式化输出", "格式化输入"]
                }
            ],
            "变量与数据类型": [
                {
                    "id": "c_var_1",
                    "title": "整型变量",
                    "content": "C语言提供多种整型：short（短整型）、int（整型）、long（长整型）、long long（超长整型）。可加signed或unsigned修饰。不同类型占用不同字节数，表示范围不同。",
                    "examples": [
                        "short s = 32767;\nint i = 2147483647;\nlong l = 2147483647L;\nunsigned int u = 4294967295U;"
                    ],
                    "difficulty": 1,
                    "related_points": ["数据类型", "取值范围"]
                },
                {
                    "id": "c_var_2",
                    "title": "浮点型变量",
                    "content": "浮点型用于表示小数。float占4字节，精度约6-7位；double占8字节，精度约15-16位。科学计数法用e或E表示，如3.14e2表示314。",
                    "examples": [
                        "float f = 3.14f;\ndouble d = 3.14159265358979;\nfloat scientific = 1.5e3f;  // 1500.0"
                    ],
                    "difficulty": 2,
                    "related_points": ["精度", "科学计数法"]
                },
                {
                    "id": "c_var_3",
                    "title": "字符型变量",
                    "content": "char类型用于存储单个字符，占1字节。字符用单引号括起，如'A'。实际存储的是ASCII码值。特殊字符需要转义，如\\n（换行）、\\t（制表符）、\\\\（反斜杠）。",
                    "examples": [
                        "char c = 'A';\nchar newline = '\\n';\nchar backslash = '\\\\';\nprintf(\"字符: %c, ASCII: %d\\n\", c, c);"
                    ],
                    "difficulty": 1,
                    "related_points": ["ASCII码", "转义字符"]
                }
            ],
            "运算符与表达式": [
                {
                    "id": "c_op_1",
                    "title": "算术运算符",
                    "content": "基本算术运算符：+（加）、-（减）、*（乘）、/（除）、%（取模）。注意整数除法结果为整数，取模只能用于整数。自增++和自减--可放在变量前或后。",
                    "examples": [
                        "int a = 10, b = 3;\nint sum = a + b;      // 13\nint quotient = a / b;  // 3 (整数除法)\nint remainder = a % b; // 1\nint c = a++;           // c=10, a=11 (后置自增)"
                    ],
                    "difficulty": 1,
                    "related_points": ["整数除法", "自增自减"]
                },
                {
                    "id": "c_op_2",
                    "title": "关系运算符",
                    "content": "关系运算符用于比较两个值：==（等于）、!=（不等于）、>（大于）、<（小于）、>=（大于等于）、<=（小于等于）。结果为1（真）或0（假）。",
                    "examples": [
                        "int a = 5, b = 3;\nint eq = (a == b);   // 0\nint gt = (a > b);    // 1\nint ne = (a != b);   // 1"
                    ],
                    "difficulty": 1,
                    "related_points": ["比较运算", "逻辑值"]
                },
                {
                    "id": "c_op_3",
                    "title": "逻辑运算符",
                    "content": "逻辑运算符：&&（逻辑与）、||（逻辑或）、!（逻辑非）。注意短路求值：&&遇假即停，||遇真即停。位运算符：&（按位与）、|（按位或）、^（按位异或）、~（按位取反）。",
                    "examples": [
                        "int a = 1, b = 0;\nint and_result = a && b;  // 0\nint or_result = a || b;   // 1\nint not_result = !b;      // 1"
                    ],
                    "difficulty": 2,
                    "related_points": ["短路求值", "位运算"]
                }
            ],
            "流程控制": [
                {
                    "id": "c_ctrl_1",
                    "title": "if-else语句",
                    "content": "条件语句用于根据条件执行不同代码。if后接条件表达式，条件为真执行对应代码块。else可选，条件为假时执行。可嵌套使用，注意else与最近的if配对。",
                    "examples": [
                        "int score = 85;\nif (score >= 90) {\n    printf(\"优秀\\n\");\n} else if (score >= 60) {\n    printf(\"及格\\n\");\n} else {\n    printf(\"不及格\\n\");\n}"
                    ],
                    "difficulty": 1,
                    "related_points": ["条件判断", "代码块"]
                },
                {
                    "id": "c_ctrl_2",
                    "title": "switch语句",
                    "content": "switch根据表达式的值选择执行对应case分支。表达式必须是整型或字符型。每个case后需break跳出，否则会继续执行下一case。default处理所有未匹配情况。",
                    "examples": [
                        "int day = 3;\nswitch (day) {\n    case 1: printf(\"周一\"); break;\n    case 2: printf(\"周二\"); break;\n    case 3: printf(\"周三\"); break;\n    default: printf(\"其他\");\n}"
                    ],
                    "difficulty": 2,
                    "related_points": ["多分支选择", "break语句"]
                },
                {
                    "id": "c_ctrl_3",
                    "title": "循环语句",
                    "content": "C语言有三种循环：for（适合已知次数）、while（先判断后执行）、do-while（先执行后判断）。break跳出循环，continue跳过本次迭代继续下一次。",
                    "examples": [
                        "// for循环\nfor (int i = 0; i < 10; i++) {\n    printf(\"%d \", i);\n}\n\n// while循环\nint j = 0;\nwhile (j < 10) {\n    printf(\"%d \", j++);\n}"
                    ],
                    "difficulty": 1,
                    "related_points": ["循环控制", "迭代"]
                }
            ],
            "数组": [
                {
                    "id": "c_arr_1",
                    "title": "一维数组",
                    "content": "数组是相同类型元素的集合，存储在连续内存中。声明时需指定类型和大小，索引从0开始。可初始化：int arr[5] = {1,2,3,4,5}; 或 int arr[] = {1,2,3};",
                    "examples": [
                        "int arr[5] = {10, 20, 30, 40, 50};\nfor (int i = 0; i < 5; i++) {\n    printf(\"arr[%d] = %d\\n\", i, arr[i]);\n}"
                    ],
                    "difficulty": 1,
                    "related_points": ["索引", "初始化"]
                },
                {
                    "id": "c_arr_2",
                    "title": "二维数组",
                    "content": "二维数组可看作数组的数组，常用于矩阵表示。声明：int matrix[3][4]; 表示3行4列。访问用两个索引：matrix[i][j]。按行存储，先存第一行所有元素。",
                    "examples": [
                        "int matrix[2][3] = {{1,2,3}, {4,5,6}};\nfor (int i = 0; i < 2; i++) {\n    for (int j = 0; j < 3; j++) {\n        printf(\"%d \", matrix[i][j]);\n    }\n    printf(\"\\n\");\n}"
                    ],
                    "difficulty": 2,
                    "related_points": ["矩阵", "多维数组"]
                },
                {
                    "id": "c_arr_3",
                    "title": "字符数组与字符串",
                    "content": "C语言没有字符串类型，用字符数组存储。字符串以'\\0'结尾。可用字符串字面量初始化：char str[] = \"Hello\"; 自动添加'\\0'。常用函数：strlen、strcpy、strcat、strcmp。",
                    "examples": [
                        "char str[20] = \"Hello\";\nprintf(\"长度: %zu\\n\", strlen(str));  // 5\nstrcat(str, \" World\");\nprintf(\"%s\\n\", str);  // Hello World"
                    ],
                    "difficulty": 2,
                    "related_points": ["字符串处理", "字符串函数"]
                }
            ],
            "函数": [
                {
                    "id": "c_func_1",
                    "title": "函数定义与调用",
                    "content": "函数是完成特定任务的代码块。定义包括：返回类型、函数名、参数列表、函数体。调用时传递参数，接收返回值。return语句返回结果并结束函数执行。",
                    "examples": [
                        "int add(int a, int b) {\n    return a + b;\n}\n\nint main() {\n    int result = add(3, 5);\n    printf(\"结果: %d\\n\", result);  // 8\n    return 0;\n}"
                    ],
                    "difficulty": 1,
                    "related_points": ["返回值", "参数传递"]
                },
                {
                    "id": "c_func_2",
                    "title": "函数声明与原型",
                    "content": "函数必须先声明后调用。可在使用前声明函数原型（只写头不写体），定义放在后面。原型告诉编译器函数的返回类型和参数类型。",
                    "examples": [
                        "// 函数原型\nint max(int a, int b);\n\nint main() {\n    printf(\"较大值: %d\\n\", max(3, 5));\n    return 0;\n}\n\nint max(int a, int b) {\n    return a > b ? a : b;\n}"
                    ],
                    "difficulty": 2,
                    "related_points": ["函数原型", "声明与定义"]
                },
                {
                    "id": "c_func_3",
                    "title": "递归函数",
                    "content": "函数调用自身称为递归。必须有终止条件（基准情况），否则无限递归。递归适合解决可分解为相似子问题的问题，如阶乘、斐波那契数列、汉诺塔等。",
                    "examples": [
                        "int factorial(int n) {\n    if (n <= 1) return 1;  // 基准情况\n    return n * factorial(n - 1);  // 递归调用\n}\n\n// factorial(5) = 5 * 4 * 3 * 2 * 1 = 120"
                    ],
                    "difficulty": 3,
                    "related_points": ["基准情况", "递归思想"]
                }
            ],
            "指针": [
                {
                    "id": "c_ptr_1",
                    "title": "指针基础",
                    "content": "指针是存储内存地址的变量。声明：int *p; 表示p是指向int的指针。&运算符取变量地址，*运算符解引用（获取指针指向的值）。指针未初始化时值为随机地址。",
                    "examples": [
                        "int a = 10;\nint *p = &a;  // p指向a\nprintf(\"a的值: %d\\n\", *p);  // 10\nprintf(\"a的地址: %p\\n\", p);"
                    ],
                    "difficulty": 2,
                    "related_points": ["地址", "解引用"]
                },
                {
                    "id": "c_ptr_2",
                    "title": "指针与数组",
                    "content": "数组名是指向首元素的指针。arr[i] 等价于 *(arr+i)。指针可遍历数组：p++移动到下一元素。指针算术考虑类型大小，int*加1实际移动4字节。",
                    "examples": [
                        "int arr[] = {10, 20, 30};\nint *p = arr;  // 指向首元素\nprintf(\"%d\\n\", *p);      // 10\nprintf(\"%d\\n\", *(p+1));  // 20\nprintf(\"%d\\n\", p[2]);    // 30"
                    ],
                    "difficulty": 2,
                    "related_points": ["指针算术", "数组遍历"]
                },
                {
                    "id": "c_ptr_3",
                    "title": "指针与函数",
                    "content": "指针作为函数参数可在函数内修改原变量的值（传地址而非传值）。常用于：交换两个变量的值、返回多个结果、处理大数组（避免复制）。",
                    "examples": [
                        "void swap(int *a, int *b) {\n    int temp = *a;\n    *a = *b;\n    *b = temp;\n}\n\nint x = 3, y = 5;\nswap(&x, &y);  // x=5, y=3"
                    ],
                    "difficulty": 3,
                    "related_points": ["传地址", "修改原变量"]
                }
            ],
            "结构体与共用体": [
                {
                    "id": "c_struct_1",
                    "title": "结构体定义与使用",
                    "content": "结构体是将不同类型数据组合在一起的复合数据类型。使用struct关键字定义，成员用点运算符访问。可嵌套定义，也可包含指针成员。",
                    "examples": [
                        "struct Student {\n    char name[50];\n    int age;\n    float score;\n};\n\nstruct Student stu = {\"张三\", 20, 85.5};\nprintf(\"姓名: %s, 年龄: %d\\n\", stu.name, stu.age);"
                    ],
                    "difficulty": 2,
                    "related_points": ["复合类型", "成员访问"]
                },
                {
                    "id": "c_struct_2",
                    "title": "结构体指针",
                    "content": "可定义指向结构体的指针。通过指针访问成员有两种方式：(*p).member 或 p->member（箭头运算符）。结构体指针常用于动态分配和链表。",
                    "examples": [
                        "struct Student *p = &stu;\nprintf(\"姓名: %s\\n\", (*p).name);\nprintf(\"年龄: %d\\n\", p->age);"
                    ],
                    "difficulty": 2,
                    "related_points": ["箭头运算符", "链表"]
                },
                {
                    "id": "c_struct_3",
                    "title": "共用体",
                    "content": "共用体(union)的所有成员共享同一内存空间，大小等于最大成员的大小。同一时刻只能存储一个成员的值。常用于节省内存或数据类型转换。",
                    "examples": [
                        "union Data {\n    int i;\n    float f;\n    char c;\n};\n\nunion Data d;\nd.i = 10;\nprintf(\"%d\\n\", d.i);"
                    ],
                    "difficulty": 3,
                    "related_points": ["内存共享", "类型转换"]
                }
            ],
            "文件操作": [
                {
                    "id": "c_file_1",
                    "title": "文件打开与关闭",
                    "content": "使用fopen打开文件，返回FILE指针。模式：r（读）、w（写）、a（追加）、rb/wb（二进制）。使用完毕必须fclose关闭文件，释放资源。",
                    "examples": [
                        "FILE *fp = fopen(\"data.txt\", \"r\");\nif (fp == NULL) {\n    printf(\"文件打开失败\\n\");\n    return 1;\n}\nfclose(fp);"
                    ],
                    "difficulty": 2,
                    "related_points": ["文件模式", "错误处理"]
                },
                {
                    "id": "c_file_2",
                    "title": "文件读写函数",
                    "content": "常用读写函数：fgetc/fputc（单字符）、fgets/fputs（字符串）、fscanf/fprintf（格式化）、fread/fwrite（二进制块）。EOF表示文件结束。",
                    "examples": [
                        "char ch;\nwhile ((ch = fgetc(fp)) != EOF) {\n    putchar(ch);\n}\nfprintf(fp, \"Hello, World!\\n\");"
                    ],
                    "difficulty": 2,
                    "related_points": ["格式化读写", "二进制读写"]
                },
                {
                    "id": "c_file_3",
                    "title": "文件定位",
                    "content": "ftell获取当前文件位置，fseek设置文件位置，rewind回到文件开头。常用fseek(fp, offset, SEEK_SET/SEEK_CUR/SEEK_END)进行随机访问。",
                    "examples": [
                        "fseek(fp, 0, SEEK_END);\nlong size = ftell(fp);\nrewind(fp);\nprintf(\"文件大小: %ld 字节\\n\", size);"
                    ],
                    "difficulty": 3,
                    "related_points": ["随机访问", "文件指针"]
                }
            ],
            "算法基础": [
                {
                    "id": "c_algo_1",
                    "title": "排序算法",
                    "content": "常见排序：冒泡排序（相邻比较交换）、选择排序（找最小放前面）、插入排序（逐个插入有序序列）。时间复杂度O(n²)，适合小规模数据。",
                    "examples": [
                        "// 冒泡排序\nfor (int i = 0; i < n-1; i++) {\n    for (int j = 0; j < n-1-i; j++) {\n        if (arr[j] > arr[j+1]) {\n            int temp = arr[j];\n            arr[j] = arr[j+1];\n            arr[j+1] = temp;\n        }\n    }\n}"
                    ],
                    "difficulty": 2,
                    "related_points": ["时间复杂度", "比较排序"]
                },
                {
                    "id": "c_algo_2",
                    "title": "查找算法",
                    "content": "顺序查找：遍历数组逐个比较，O(n)。二分查找：要求数组有序，每次排除一半，O(log n)。",
                    "examples": [
                        "int binary_search(int arr[], int n, int target) {\n    int left = 0, right = n - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (arr[mid] == target) return mid;\n        if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}"
                    ],
                    "difficulty": 2,
                    "related_points": ["二分查找", "有序数组"]
                },
                {
                    "id": "c_algo_3",
                    "title": "递归与分治",
                    "content": "递归将问题分解为更小的相似子问题。分治策略：分解、解决、合并。经典应用：快速排序、归并排序、二分查找。",
                    "examples": [
                        "int fib(int n) {\n    if (n <= 1) return n;\n    return fib(n-1) + fib(n-2);\n}\n\nint factorial(int n) {\n    if (n <= 1) return 1;\n    return n * factorial(n-1);\n}"
                    ],
                    "difficulty": 3,
                    "related_points": ["递归思想", "时间复杂度"]
                }
            ],
            "数据结构入门": [
                {
                    "id": "c_ds_1",
                    "title": "链表",
                    "content": "链表是动态数据结构，节点包含数据和指向下一节点的指针。优点：插入删除O(1)；缺点：访问需遍历O(n)。",
                    "examples": [
                        "struct Node {\n    int data;\n    struct Node *next;\n};\n\nstruct Node *newNode = malloc(sizeof(struct Node));\nnewNode->data = 10;\nnewNode->next = NULL;"
                    ],
                    "difficulty": 3,
                    "related_points": ["动态分配", "指针应用"]
                },
                {
                    "id": "c_ds_2",
                    "title": "栈与队列",
                    "content": "栈：后进先出(LIFO)，操作push/pop。队列：先进先出(FIFO)，操作enqueue/dequeue。",
                    "examples": [
                        "int stack[100], top = -1;\nvoid push(int x) { stack[++top] = x; }\nint pop() { return stack[top--]; }\nint isEmpty() { return top == -1; }"
                    ],
                    "difficulty": 2,
                    "related_points": ["LIFO", "FIFO"]
                },
                {
                    "id": "c_ds_3",
                    "title": "树与二叉树",
                    "content": "树是层次结构。二叉树每个节点最多两个子节点。二叉搜索树(BST)：左<根<右。遍历：前序、中序、后序。",
                    "examples": [
                        "struct TreeNode {\n    int val;\n    struct TreeNode *left, *right;\n};\n\nvoid inorder(struct TreeNode *root) {\n    if (root) {\n        inorder(root->left);\n        printf(\"%d \", root->val);\n        inorder(root->right);\n    }\n}"
                    ],
                    "difficulty": 3,
                    "related_points": ["递归遍历", "BST"]
                }
            ],
        }

        # 查找匹配的知识点
        for title, points in c_knowledge_map.items():
            if title in chapter.title or chapter.title in title:
                return {
                    "knowledge_points": points,
                    "cached": True
                }

        # 关键词匹配：处理编码或特殊字符问题
        keywords_map = {
            "结构": "结构体与共用体",
            "文件": "文件操作",
            "算法": "算法基础",
            "数据结构": "数据结构入门",
        }
        for keyword, map_title in keywords_map.items():
            if keyword in chapter.title and map_title in c_knowledge_map:
                return {
                    "knowledge_points": c_knowledge_map[map_title],
                    "cached": True
                }

        return None

    async def _get_user_profile(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: int
    ) -> Optional[dict]:
        """获取用户画像"""
        # 获取用户在各章节的掌握情况
        result = await db.execute(
            select(ChapterMastery).where(
                and_(
                    ChapterMastery.user_id == user_id,
                    ChapterMastery.course_id == course_id
                )
            )
        )
        masteries = result.scalars().all()

        if not masteries:
            return None

        # 计算当前水平
        total_mastery = sum(m.mastery_score for m in masteries)
        avg_mastery = total_mastery / len(masteries) if masteries else 0
        current_level = min(5.0, max(1.0, avg_mastery / 20))  # 转换为 1-5

        # 识别薄弱知识点
        weak_knowledge_points = []
        strong_knowledge_points = []

        for m in masteries:
            if m.mastery_score < 50:
                weak_knowledge_points.extend(m.objectives_status or [])
            elif m.mastery_score >= 80:
                strong_knowledge_points.extend(m.objectives_status or [])

        # 计算近期正确率
        total_exercises = sum(m.total_exercises for m in masteries)
        correct_exercises = sum(m.correct_exercises for m in masteries)
        recent_accuracy = correct_exercises / total_exercises if total_exercises > 0 else 0.5

        return {
            "user_id": user_id,
            "current_level": current_level,
            "weak_knowledge_points": list(set(weak_knowledge_points)),
            "strong_knowledge_points": list(set(strong_knowledge_points)),
            "recent_accuracy": recent_accuracy,
        }

    async def _generate_quiz_questions(
        self,
        chapter: Chapter,
        user_profile: Optional[dict],
        request: MasteryQuizGenerateRequest
    ) -> list[dict]:
        """生成测试题"""
        if not ai_service.is_configured():
            # 返回示例题目
            return [{
                "id": f"q_sample_{i}",
                "type": "choice",
                "difficulty": 2,
                "content": {
                    "text": f"示例题目 {i+1}：关于 {chapter.title} 的知识点",
                    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"]
                },
                "solution": {"answer": "A", "explanation": "示例解析"},
                "knowledge_points": [chapter.title]
            } for i in range(min(request.question_count, 3))]

        # 使用 AI 生成题目
        questions = await ai_service.generate_personalized_quiz(
            chapter_title=chapter.title,
            chapter_description=chapter.description or "",
            user_profile=user_profile,
            question_count=request.question_count,
            question_types=request.question_types,
            difficulty_range=request.difficulty_range
        )

        return questions

    async def _create_quiz_session(
        self,
        user_id: str,
        course_id: int,
        chapter_id: int,
        questions: list[dict]
    ) -> str:
        """创建测试会话"""
        session_id = str(uuid.uuid4())
        now = utc_now()

        session = MasteryQuizSession(
            id=session_id,
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            questions=questions,
            created_at=now,
            expires_at=datetime.fromtimestamp(now.timestamp() + 3600)  # 1小时后过期
        )

        self._sessions[session_id] = session
        return session_id

    async def _get_quiz_session(self, session_id: str) -> Optional[MasteryQuizSession]:
        """获取测试会话"""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # 检查是否过期
        if session.expires_at < utc_now():
            self._sessions.pop(session_id, None)
            return None

        return session

    async def _evaluate_answers(
        self,
        session: MasteryQuizSession,
        answers: list[Any]
    ) -> dict:
        """评估答案"""
        questions_map = {q["id"]: q for q in session.questions}

        results = []
        correct_count = 0

        for answer in answers:
            question_id = answer.question_id
            user_answer = answer.answer

            question = questions_map.get(question_id)
            if not question:
                continue

            correct_answer = question.get("solution", {}).get("answer", "")
            is_correct = str(user_answer) == str(correct_answer)

            if is_correct:
                correct_count += 1

            results.append({
                "question_id": question_id,
                "is_correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": question.get("solution", {}).get("explanation", ""),
                "knowledge_points": question.get("knowledge_points", [])
            })

        return {
            "correct_count": correct_count,
            "total_count": len(session.questions),
            "results": results
        }

    async def _update_user_progress(
        self,
        db: AsyncSession,
        user_id: str,
        chapter_id: int,
        correct_count: int,
        total_count: int
    ) -> None:
        """更新用户进度

        更新 ChapterMastery 记录：
        - 增加练习次数
        - 更新正确率
        - 更新掌握分数
        """
        # 获取或创建 ChapterMastery 记录
        result = await db.execute(
            select(ChapterMastery).where(
                and_(
                    ChapterMastery.user_id == user_id,
                    ChapterMastery.chapter_id == chapter_id
                )
            )
        )
        mastery = result.scalar_one_or_none()

        if mastery:
            # 更新现有记录
            mastery.total_exercises += total_count
            mastery.correct_exercises += correct_count

            # 重新计算分数
            accuracy = mastery.correct_exercises / mastery.total_exercises if mastery.total_exercises > 0 else 0
            mastery.accuracy_score = accuracy * 100
            mastery.mastery_score = min(100, mastery.mastery_score + (accuracy * 10))
            mastery.mastery_level = self._get_mastery_level(mastery.mastery_score)
        else:
            # 创建新记录
            accuracy = correct_count / total_count if total_count > 0 else 0
            mastery = ChapterMastery(
                user_id=user_id,
                course_id=0,  # Will be set by caller if needed
                chapter_id=chapter_id,
                total_exercises=total_count,
                correct_exercises=correct_count,
                accuracy_score=accuracy * 100,
                mastery_score=min(100, accuracy * 50),
                mastery_level=self._get_mastery_level(accuracy * 50),
            )
            db.add(mastery)

        await db.commit()

    def _get_mastery_level(self, score: float) -> str:
        """根据分数获取掌握等级"""
        if score >= 90:
            return "精通"
        elif score >= 75:
            return "熟练"
        elif score >= 60:
            return "练习"
        elif score >= 40:
            return "学习"
        else:
            return "入门"

    def _generate_recommendations(
        self,
        results: list[dict],
        accuracy: float
    ) -> list[str]:
        """生成学习建议"""
        recommendations = []

        if accuracy >= 0.9:
            recommendations.append("表现优秀！可以尝试更高难度的内容。")
        elif accuracy >= 0.7:
            recommendations.append("掌握良好，建议复习错误的知识点。")
        else:
            recommendations.append("建议重新学习相关知识点后再进行测试。")

        # 添加具体知识点建议
        wrong_topics = []
        for r in results:
            if not r["is_correct"]:
                wrong_topics.extend(r.get("knowledge_points", []))

        if wrong_topics:
            unique_topics = list(set(wrong_topics))[:3]
            recommendations.append(f"重点复习：{', '.join(unique_topics)}")

        return recommendations


# 全局单例
mastery_quiz_service = MasteryQuizService()
