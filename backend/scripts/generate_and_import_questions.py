"""
Generate and Import Base Questions to Database

根据每个小节的知识点，生成选择题和填空题，导入到数据库。

题目类型：
- choice: 选择题
- fill_blank: 填空题

生成规则：
- 基于BKT模型计算每个小节需要的题数
- 选择题和填空题比例约为 6:4
- 每道题关联1-2个知识点
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.section_base_question import SectionBaseQuestion
from app.models.section import Section
from app.models.chapter import Chapter


# ============================================================
# C语言课程完整知识点数据（用于生成题目）
# ============================================================
COURSE_DATA = {
    1: {  # 第1章: 简单C程序设计
        1: {  # 1.1 C程序入门
            "title": "C程序入门",
            "knowledge_points": [
                {"name": "C程序的基本结构", "difficulty": 1},
                {"name": "main函数", "difficulty": 1},
                {"name": "语句与注释", "difficulty": 1}
            ],
            "base_count": 6
        },
        2: {  # 1.2 基本数据类型与变量
            "title": "基本数据类型与变量",
            "knowledge_points": [
                {"name": "基本数据类型", "difficulty": 1},
                {"name": "标识符", "difficulty": 1},
                {"name": "变量与常量", "difficulty": 1},
                {"name": "printf格式化输出", "difficulty": 1}
            ],
            "base_count": 8
        },
        3: {  # 1.3 程序设计基础
            "title": "程序设计基础",
            "knowledge_points": [
                {"name": "算法与流程图", "difficulty": 2},
                {"name": "程序设计描述方法", "difficulty": 2},
                {"name": "常见错误分析", "difficulty": 2},
                {"name": "编程风格", "difficulty": 1}
            ],
            "base_count": 8
        }
    },
    2: {  # 第2章: 选择控制结构与应用
        1: {  # 2.1 关系运算与逻辑运算
            "title": "关系运算与逻辑运算",
            "knowledge_points": [
                {"name": "关系运算符", "difficulty": 1},
                {"name": "逻辑运算符", "difficulty": 1},
                {"name": "if语句基本形式", "difficulty": 1}
            ],
            "base_count": 6
        },
        2: {  # 2.2 if语句嵌套与应用
            "title": "if语句嵌套与应用",
            "knowledge_points": [
                {"name": "if语句嵌套", "difficulty": 2},
                {"name": "条件运算符", "difficulty": 1}
            ],
            "base_count": 4
        },
        3: {  # 2.3 switch语句
            "title": "switch语句",
            "knowledge_points": [
                {"name": "switch语句基础", "difficulty": 1},
                {"name": "switch语句深入", "difficulty": 2}
            ],
            "base_count": 4
        }
    },
    3: {  # 第3章: 循环结构及应用
        1: {  # 3.1 for循环
            "title": "for循环",
            "knowledge_points": [
                {"name": "for循环基本结构", "difficulty": 1},
                {"name": "for循环变体", "difficulty": 2}
            ],
            "base_count": 4
        },
        2: {  # 3.2 while循环
            "title": "while循环",
            "knowledge_points": [
                {"name": "while循环", "difficulty": 1},
                {"name": "do-while循环", "difficulty": 1}
            ],
            "base_count": 4
        },
        3: {  # 3.3 循环嵌套与控制
            "title": "循环嵌套与控制",
            "knowledge_points": [
                {"name": "循环嵌套", "difficulty": 2},
                {"name": "break与continue", "difficulty": 1}
            ],
            "base_count": 4
        }
    },
    4: {  # 第4章: 模块化设计与应用
        1: {  # 4.1 函数基础
            "title": "函数基础",
            "knowledge_points": [
                {"name": "函数定义", "difficulty": 1},
                {"name": "函数声明", "difficulty": 1},
                {"name": "函数调用", "difficulty": 1}
            ],
            "base_count": 6
        },
        2: {  # 4.2 预处理指令
            "title": "预处理指令",
            "knowledge_points": [
                {"name": "宏定义", "difficulty": 1},
                {"name": "条件编译", "difficulty": 1}
            ],
            "base_count": 4
        }
    },
    5: {  # 第5章: 相同数据类型集合
        1: {  # 5.1 一维数组
            "title": "一维数组",
            "knowledge_points": [
                {"name": "一维数组基础", "difficulty": 1},
                {"name": "数组遍历与操作", "difficulty": 1}
            ],
            "base_count": 4
        },
        2: {  # 5.2 二维数组
            "title": "二维数组",
            "knowledge_points": [
                {"name": "二维数组基础", "difficulty": 2},
                {"name": "二维数组应用", "difficulty": 2}
            ],
            "base_count": 4
        },
        3: {  # 5.3 字符串与字符数组
            "title": "字符串与字符数组",
            "knowledge_points": [
                {"name": "字符串基础", "difficulty": 1},
                {"name": "字符串函数", "difficulty": 2}
            ],
            "base_count": 4
        }
    },
    6: {  # 第6章: 指针基础
        1: {  # 6.1 指针概念
            "title": "指针概念",
            "knowledge_points": [
                {"name": "指针变量", "difficulty": 3},
                {"name": "指针运算", "difficulty": 3}
            ],
            "base_count": 4
        },
        2: {  # 6.2 指针与数组
            "title": "指针与数组",
            "knowledge_points": [
                {"name": "指针与一维数组", "difficulty": 3},
                {"name": "指针与字符串", "difficulty": 3}
            ],
            "base_count": 4
        },
        3: {  # 6.3 指针与函数
            "title": "指针与函数",
            "knowledge_points": [
                {"name": "指针作为参数", "difficulty": 3},
                {"name": "指针作为返回值", "difficulty": 3}
            ],
            "base_count": 4
        }
    },
    7: {  # 第7章: 结构体与联合体
        1: {  # 7.1 结构体基础
            "title": "结构体基础",
            "knowledge_points": [
                {"name": "结构体定义", "difficulty": 2},
                {"name": "结构体变量", "difficulty": 2}
            ],
            "base_count": 4
        },
        2: {  # 7.2 结构体应用
            "title": "结构体应用",
            "knowledge_points": [
                {"name": "结构体数组", "difficulty": 2},
                {"name": "结构体指针", "difficulty": 3}
            ],
            "base_count": 4
        },
        3: {  # 7.3 联合体与枚举
            "title": "联合体与枚举",
            "knowledge_points": [
                {"name": "联合体", "difficulty": 2},
                {"name": "枚举类型", "difficulty": 2}
            ],
            "base_count": 4
        }
    },
    8: {  # 第8章: 文件操作
        1: {  # 8.1 文件基础
            "title": "文件基础",
            "knowledge_points": [
                {"name": "文件打开与关闭", "difficulty": 2},
                {"name": "文件读写", "difficulty": 2}
            ],
            "base_count": 4
        },
        2: {  # 8.2 文件应用
            "title": "文件应用",
            "knowledge_points": [
                {"name": "文件定位", "difficulty": 2},
                {"name": "文件错误处理", "difficulty": 2}
            ],
            "base_count": 4
        }
    },
    9: {  # 第9章: 综合应用
        1: {  # 9.1 程序设计方法
            "title": "程序设计方法",
            "knowledge_points": [
                {"name": "程序设计流程", "difficulty": 2},
                {"name": "模块化设计", "difficulty": 3}
            ],
            "base_count": 4
        },
        2: {  # 9.2 综合案例
            "title": "综合案例",
            "knowledge_points": [
                {"name": "学生管理系统", "difficulty": 4},
                {"name": "文件处理案例", "difficulty": 3}
            ],
            "base_count": 4
        }
    }
}


# ============================================================
# 题目生成函数
# ============================================================

def generate_questions_for_kp(kp_name: str, difficulty: int, q_type: str, order: int) -> dict:
    """根据知识点生成一道题目"""
    kp_lower = kp_name.lower()

    # ==================== 选择题 ====================
    if q_type == "choice":
        if "c程序的基本结构" in kp_lower or "main函数" in kp_lower:
            return _gen_c_structure_choice(kp_name, order)
        elif "语句与注释" in kp_lower:
            return _gen_statement_comment_choice(kp_name, order)
        elif "基本数据类型" in kp_lower:
            return _gen_data_type_choice(kp_name, order)
        elif "标识符" in kp_lower:
            return _gen_identifier_choice(kp_name, order)
        elif "变量与常量" in kp_lower:
            return _gen_var_const_choice(kp_name, order)
        elif "printf" in kp_lower:
            return _gen_printf_choice(kp_name, order)
        elif "算法与流程图" in kp_lower:
            return _gen_algorithm_choice(kp_name, order)
        elif "关系运算符" in kp_lower:
            return _gen_relational_choice(kp_name, order)
        elif "逻辑运算符" in kp_lower:
            return _gen_logical_choice(kp_name, order)
        elif "if语句基本形式" in kp_lower or "if语句嵌套" in kp_lower:
            return _gen_if_choice(kp_name, order)
        elif "条件运算符" in kp_lower:
            return _gen_ternary_choice(kp_name, order)
        elif "switch" in kp_lower:
            return _gen_switch_choice(kp_name, order)
        elif "for循环" in kp_lower:
            return _gen_for_choice(kp_name, order)
        elif "while循环" in kp_lower or "do-while" in kp_lower:
            return _gen_while_choice(kp_name, order)
        elif "循环嵌套" in kp_lower:
            return _gen_nested_loop_choice(kp_name, order)
        elif "break" in kp_lower or "continue" in kp_lower:
            return _gen_break_continue_choice(kp_name, order)
        elif "函数定义" in kp_lower or "函数声明" in kp_lower or "函数调用" in kp_lower:
            return _gen_function_choice(kp_name, order)
        elif "宏定义" in kp_lower:
            return _gen_macro_choice(kp_name, order)
        elif "条件编译" in kp_lower:
            return _gen_cond_compile_choice(kp_name, order)
        elif "一维数组" in kp_lower:
            return _gen_1d_array_choice(kp_name, order)
        elif "二维数组" in kp_lower:
            return _gen_2d_array_choice(kp_name, order)
        elif "字符串基础" in kp_lower or "字符串函数" in kp_lower:
            return _gen_string_choice(kp_name, order)
        elif "指针变量" in kp_lower or "指针运算" in kp_lower:
            return _gen_pointer_choice(kp_name, order)
        elif "指针与一维数组" in kp_lower or "指针与数组" in kp_lower:
            return _gen_pointer_array_choice(kp_name, order)
        elif "指针与字符串" in kp_lower:
            return _gen_pointer_string_choice(kp_name, order)
        elif "指针作为参数" in kp_lower or "指针作为返回值" in kp_lower or "指针与函数" in kp_lower:
            return _gen_pointer_func_choice(kp_name, order)
        elif "结构体定义" in kp_lower or "结构体变量" in kp_lower:
            return _gen_struct_choice(kp_name, order)
        elif "结构体数组" in kp_lower or "结构体指针" in kp_lower:
            return _gen_struct_app_choice(kp_name, order)
        elif "联合体" in kp_lower:
            return _gen_union_choice(kp_name, order)
        elif "枚举" in kp_lower:
            return _gen_enum_choice(kp_name, order)
        elif "文件打开" in kp_lower or "文件关闭" in kp_lower or "文件读写" in kp_lower:
            return _gen_file_choice(kp_name, order)
        elif "文件定位" in kp_lower or "文件错误处理" in kp_lower:
            return _gen_file_app_choice(kp_name, order)
        elif "程序设计流程" in kp_lower:
            return _gen_design_flow_choice(kp_name, order)
        elif "模块化设计" in kp_lower:
            return _gen_modular_choice(kp_name, order)
        elif "学生管理系统" in kp_lower:
            return _gen_case_choice(kp_name, order)
        elif "文件处理案例" in kp_lower:
            return _gen_file_case_choice(kp_name, order)
        else:
            return _gen_generic_choice(kp_name, order)

    # ==================== 填空题 ====================
    else:
        if "c程序的基本结构" in kp_lower or "main函数" in kp_lower:
            return _gen_c_structure_fill(kp_name, order)
        elif "语句与注释" in kp_lower:
            return _gen_statement_comment_fill(kp_name, order)
        elif "基本数据类型" in kp_lower:
            return _gen_data_type_fill(kp_name, order)
        elif "标识符" in kp_lower:
            return _gen_identifier_fill(kp_name, order)
        elif "变量与常量" in kp_lower:
            return _gen_var_const_fill(kp_name, order)
        elif "printf" in kp_lower:
            return _gen_printf_fill(kp_name, order)
        elif "算法与流程图" in kp_lower:
            return _gen_algorithm_fill(kp_name, order)
        elif "关系运算符" in kp_lower:
            return _gen_relational_fill(kp_name, order)
        elif "逻辑运算符" in kp_lower:
            return _gen_logical_fill(kp_name, order)
        elif "if语句" in kp_lower:
            return _gen_if_fill(kp_name, order)
        elif "switch" in kp_lower:
            return _gen_switch_fill(kp_name, order)
        elif "for循环" in kp_lower:
            return _gen_for_fill(kp_name, order)
        elif "while循环" in kp_lower or "do-while" in kp_lower:
            return _gen_while_fill(kp_name, order)
        elif "循环嵌套" in kp_lower:
            return _gen_nested_loop_fill(kp_name, order)
        elif "break" in kp_lower or "continue" in kp_lower:
            return _gen_break_continue_fill(kp_name, order)
        elif "函数" in kp_lower:
            return _gen_function_fill(kp_name, order)
        elif "宏定义" in kp_lower or "条件编译" in kp_lower:
            return _gen_macro_fill(kp_name, order)
        elif "一维数组" in kp_lower:
            return _gen_1d_array_fill(kp_name, order)
        elif "二维数组" in kp_lower:
            return _gen_2d_array_fill(kp_name, order)
        elif "字符串" in kp_lower:
            return _gen_string_fill(kp_name, order)
        elif "指针" in kp_lower:
            return _gen_pointer_fill(kp_name, order)
        elif "结构体" in kp_lower:
            return _gen_struct_fill(kp_name, order)
        elif "联合体" in kp_lower or "枚举" in kp_lower:
            return _gen_union_enum_fill(kp_name, order)
        elif "文件" in kp_lower:
            return _gen_file_fill(kp_name, order)
        else:
            return _gen_generic_fill(kp_name, order)


# ============================================================
# 选择题生成函数
# ============================================================

def _gen_c_structure_choice(kp_name, order):
    templates = [
        {
            "title": "C程序入口",
            "question_text": "C语言程序的执行入口是哪个函数？",
            "options": ["A. main()", "B. start()", "C. run()", "D. printf()"],
            "correct_answer": "A",
            "explanation": "C语言规定，程序的执行从main函数开始，每个C程序必须有且只能有一个main函数作为程序入口。",
            "difficulty": 1
        },
        {
            "title": "main函数格式",
            "question_text": "以下哪个是标准的main函数定义？",
            "options": ["A. void main()", "B. main()", "C. int main()", "D. main(void)"],
            "correct_answer": "C",
            "explanation": "标准的main函数应该返回int类型，即int main()，返回值表示程序结束状态。",
            "difficulty": 1
        },
        {
            "title": "头文件引入",
            "question_text": "在C语言中，#include <stdio.h>这行代码的作用是什么？",
            "options": ["A. 定义一个变量", "B. 包含标准输入输出头文件", "C. 声明一个函数", "D. 输出文字"],
            "correct_answer": "B",
            "explanation": "#include是预处理指令，stdio.h是标准输入输出库的头文件，用于使用printf、scanf等函数。",
            "difficulty": 1
        },
        {
            "title": "程序结构组成",
            "question_text": "C程序的基本组成部分不包括以下哪一项？",
            "options": ["A. 预处理指令", "B. main函数", "C. 注释", "D. 变量定义"],
            "correct_answer": "D",
            "explanation": "C程序的基本组成部分是预处理指令、main函数和语句。变量定义不是必须的组成部分。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_statement_comment_choice(kp_name, order):
    templates = [
        {
            "title": "语句结束符",
            "question_text": "C语言中，每条语句应该以什么符号结尾？",
            "options": ["A. 冒号 :", "B. 逗号 ,", "C. 分号 ;", "D. 句号 ."],
            "correct_answer": "C",
            "explanation": "C语言中，分号(;)是语句的结束符，每条可执行语句都必须以分号结尾。",
            "difficulty": 1
        },
        {
            "title": "注释的作用",
            "question_text": "关于C语言注释的说法，正确的是？",
            "options": ["A. 注释会被编译器执行", "B. 注释对程序运行没有影响", "C. 注释只能写在代码后面", "D. 注释不能多行"],
            "correct_answer": "B",
            "explanation": "注释是给程序员看的说明文字，不参与程序编译和执行，对程序运行没有任何影响。",
            "difficulty": 1
        },
        {
            "title": "多行注释",
            "question_text": "以下哪个是C语言的多行注释格式？",
            "options": ["A. // 注释内容", "B. /* 注释内容 */", "C. # 注释内容", "D. <!-- 注释内容 -->"],
            "correct_answer": "B",
            "explanation": "C语言使用/*和*/包围多行注释，使用//标记单行注释。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_data_type_choice(kp_name, order):
    templates = [
        {
            "title": "基本数据类型",
            "question_text": "以下哪个不是C语言的基本数据类型？",
            "options": ["A. int", "B. float", "C. bool", "D. char"],
            "correct_answer": "C",
            "explanation": "C语言的基本数据类型包括int、float、double、char，没有bool类型（C99之前）。",
            "difficulty": 1
        },
        {
            "title": "整型int",
            "question_text": "在C语言中，int类型通常占用多少字节？",
            "options": ["A. 1字节", "B. 2字节", "C. 4字节", "D. 8字节"],
            "correct_answer": "C",
            "explanation": "在大多数现代系统上，int类型占用4个字节（32位），可以表示约-21亿到21亿的整数。",
            "difficulty": 1
        },
        {
            "title": "字符型",
            "question_text": "char类型的变量用于存储什么？",
            "options": ["A. 整数", "B. 单个字符", "C. 小数", "D. 字符串"],
            "correct_answer": "B",
            "explanation": "char类型用于存储单个字符，通常占用1个字节，使用单引号包围字符常量。",
            "difficulty": 1
        },
        {
            "title": "浮点型",
            "question_text": "用于表示小数（实数）的数据类型是？",
            "options": ["A. int和char", "B. float和double", "C. bool和void", "D. 只有float"],
            "correct_answer": "B",
            "explanation": "C语言中，float和double用于表示浮点数（小数），double是双精度浮点型。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_identifier_choice(kp_name, order):
    templates = [
        {
            "title": "合法标识符",
            "question_text": "以下哪个是合法的C语言标识符？",
            "options": ["A. 2name", "B. my-age", "C. student_age", "D. int"],
            "correct_answer": "C",
            "explanation": "标识符由字母、数字、下划线组成，必须以字母或下划线开头，不能使用关键字。",
            "difficulty": 1
        },
        {
            "title": "标识符规则",
            "question_text": "C语言中，标识符不能以什么开头？",
            "options": ["A. 字母", "B. 下划线", "C. 数字", "D. 字母或下划线"],
            "correct_answer": "C",
            "explanation": "标识符必须以字母或下划线开头，不能以数字开头。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_var_const_choice(kp_name, order):
    templates = [
        {
            "title": "变量定义",
            "question_text": "以下哪个是正确的变量定义？",
            "options": ["A. int age;", "B. int age", "C. int age.", "D. int age:"],
            "correct_answer": "A",
            "explanation": "C语言中变量定义需要在类型和变量名之间有空格，语句以分号结束。",
            "difficulty": 1
        },
        {
            "title": "常量定义",
            "question_text": "定义一个常量，使其值不可修改，应该使用什么关键字？",
            "options": ["A. var", "B. const", "C. static", "D. final"],
            "correct_answer": "B",
            "explanation": "使用const关键字定义的常量在程序运行期间不能被修改，如const int MAX=100;",
            "difficulty": 1
        },
        {
            "title": "宏定义",
            "question_text": "以下哪个是定义宏常量的正确方式？",
            "options": ["A. const PI = 3.14;", "B. #define PI 3.14", "C. var PI = 3.14;", "D. int PI = 3.14;"],
            "correct_answer": "B",
            "explanation": "使用#define预处理器指令定义宏常量，在编译前进行替换，如#define PI 3.14",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_printf_choice(kp_name, order):
    templates = [
        {
            "title": "printf输出",
            "question_text": "使用printf输出整数，应该使用哪个格式符？",
            "options": ["A. %f", "B. %d", "C. %c", "D. %s"],
            "correct_answer": "B",
            "explanation": "%d用于输出整数，%f用于输出浮点数，%c用于输出字符，%s用于输出字符串。",
            "difficulty": 1
        },
        {
            "title": "换行符",
            "question_text": "在printf中，表示换行的转义字符是？",
            "options": ["A. \\t", "B. \\n", "C. \\r", "D. \\\\"],
            "correct_answer": "B",
            "explanation": "\\n表示换行符，\\t表示制表符，\\r表示回车，\\\\表示反斜杠。",
            "difficulty": 1
        },
        {
            "title": "格式符",
            "question_text": "输出双精度浮点数double，应该使用哪个格式符？",
            "options": ["A. %f", "B. %lf", "C. %d", "D. %c"],
            "correct_answer": "B",
            "explanation": "%lf用于输出double类型（长浮点），%f用于输出float类型。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_algorithm_choice(kp_name, order):
    templates = [
        {
            "title": "算法特性",
            "question_text": "算法的特性不包括以下哪一项？",
            "options": ["A. 有穷性", "B. 确定性", "C. 无限性", "D. 可行性"],
            "correct_answer": "C",
            "explanation": "算法必须具有有穷性（有限步骤结束）、确定性（每步明确）、可行性（能够执行）。",
            "difficulty": 2
        },
        {
            "title": "流程图符号",
            "question_text": "在流程图中，菱形框表示什么？",
            "options": ["A. 开始/结束", "B. 输入/输出", "C. 处理", "D. 判断"],
            "correct_answer": "D",
            "explanation": "流程图中，椭圆表示开始/结束，平行四边形表示输入/输出，矩形表示处理，菱形表示判断。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_relational_choice(kp_name, order):
    templates = [
        {
            "title": "关系运算符",
            "question_text": "以下哪个运算符表示"大于等于"？",
            "options": ["A. >", "B. <>", "C. >=", "D. =<"],
            "correct_answer": "C",
            "explanation": ">=表示大于等于，>表示大于，<=表示小于等于，<>不是C语言的运算符。",
            "difficulty": 1
        },
        {
            "title": "等于运算符",
            "question_text": "在C语言中，判断两个值相等应该使用哪个运算符？",
            "options": ["A. =", "B. ==", "C. ===", "D. !="],
            "correct_answer": "B",
            "explanation": "==是相等比较运算符，=是赋值运算符，两者含义完全不同。",
            "difficulty": 1
        },
        {
            "title": "不等于",
            "question_text": "表示"不等于"的运算符是？",
            "options": ["A. <>", "B. ><", "C. !=", "D. ~="],
            "correct_answer": "C",
            "explanation": "!=表示不等于，是C语言的关系运算符之一。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_logical_choice(kp_name, order):
    templates = [
        {
            "title": "逻辑与",
            "question_text": "逻辑与运算符是？",
            "options": ["A. &", "B. &&", "C. |", "D. ||"],
            "correct_answer": "B",
            "explanation": "&&是逻辑与运算符，&是按位与运算符。逻辑与要求两边都为真结果才为真。",
            "difficulty": 1
        },
        {
            "title": "逻辑或",
            "question_text": "逻辑或运算符是？",
            "options": ["A. &", "B. &&", "C. |", "D. ||"],
            "correct_answer": "D",
            "explanation": "||是逻辑或运算符，|是按位或运算符。逻辑或要求任意一边为真结果就为真。",
            "difficulty": 1
        },
        {
            "title": "逻辑非",
            "question_text": "逻辑非运算符是？",
            "options": ["A. !", "B. ~", "C. not", "D. !="],
            "correct_answer": "A",
            "explanation": "!是逻辑非运算符，用于取反真假值。~是按位取反运算符。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_if_choice(kp_name, order):
    templates = [
        {
            "title": "if语句格式",
            "question_text": "以下哪个是if语句的正确格式？",
            "options": ["A. if 条件 {}", "B. if (条件) {}", "C. if 条件 then {}", "D. if {} 条件"],
            "correct_answer": "B",
            "explanation": "if语句的条件必须用括号包围，如if(a>b){}，注意括号后不要加分号。",
            "difficulty": 1
        },
        {
            "title": "if-else结构",
            "question_text": "在if-else语句中，如果有多条语句需要执行，应该？",
            "options": ["A. 不需要任何处理", "B. 用大括号包围", "C. 用中括号包围", "D. 用圆括号包围"],
            "correct_answer": "B",
            "explanation": "如果if或else后有多条语句，需要用大括号{}包围成复合语句。",
            "difficulty": 1
        },
        {
            "title": "else配对",
            "question_text": "else总是与哪个if配对？",
            "options": ["A. 第一个if", "B. 最接近的未配对的if", "C. 最后一个if", "D. 缩进最多的if"],
            "correct_answer": "B",
            "explanation": "else总是与离它最近的前一个未配对的if配对，这是由编译器的语法分析决定的。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_ternary_choice(kp_name, order):
    templates = [
        {
            "title": "条件运算符",
            "question_text": "条件运算符的表达式形式是？",
            "options": ["A. 条件 & 值1 : 值2", "B. 条件 ? 值1 : 值2", "C. 条件 : 值1 ? 值2", "D. 条件 = 值1 ? 值2"],
            "correct_answer": "B",
            "explanation": "条件运算符是C语言中唯一的三目运算符，形式为：条件 ? 表达式1 : 表达式2",
            "difficulty": 1
        },
        {
            "title": "条件运算符用途",
            "question_text": "条件运算符主要用于什么场景？",
            "options": ["A. 循环控制", "B. 简化if-else赋值语句", "C. 函数调用", "D. 变量定义"],
            "correct_answer": "B",
            "explanation": "条件运算符常用于简化简单的if-else赋值语句，如max=(a>b)?a:b;",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_switch_choice(kp_name, order):
    templates = [
        {
            "title": "switch语句",
            "question_text": "switch语句的表达式类型不能是？",
            "options": ["A. int", "B. char", "C. float", "D. 枚举"],
            "correct_answer": "C",
            "explanation": "switch括号内的表达式必须是整型或字符型（char）或枚举类型，不能是浮点型。",
            "difficulty": 1
        },
        {
            "title": "break作用",
            "question_text": "在switch语句中，break语句的作用是？",
            "options": ["A. 结束程序", "B. 跳出switch语句", "C. 跳过本次循环", "D. 继续执行下一个case"],
            "correct_answer": "B",
            "explanation": "break用于跳出当前的switch语句，如果没有break，会发生case穿透。",
            "difficulty": 1
        },
        {
            "title": "default分支",
            "question_text": "switch语句中的default分支什么时候执行？",
            "options": ["A. 总是执行", "B. 当所有case都不匹配时执行", "C. 第一个执行", "D. 最后执行"],
            "correct_answer": "B",
            "explanation": "default分支在所有case常量都不匹配表达式时执行，位置可以任意。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_for_choice(kp_name, order):
    templates = [
        {
            "title": "for循环格式",
            "question_text": "以下哪个是for循环的正确格式？",
            "options": ["A. for(初始化; 条件; 更新);", "B. for(初始化 条件 更新)", "C. for{初始化; 条件; 更新}", "D. for[初始化; 条件; 更新]"],
            "correct_answer": "A",
            "explanation": "for循环的三个表达式必须用分号分隔，条件用括号包围，循环体用大括号包围。",
            "difficulty": 1
        },
        {
            "title": "for循环执行顺序",
            "question_text": "for循环的执行顺序是？",
            "options": ["A. 条件→循环体→更新", "B. 初始化→条件→循环体→更新", "C. 更新→条件→循环体", "D. 初始化→循环体→条件"],
            "correct_answer": "B",
            "explanation": "for循环执行顺序：初始化(只执行一次)→判断条件→如果为真执行循环体→执行更新→回到判断条件。",
            "difficulty": 1
        },
        {
            "title": "死循环",
            "question_text": "以下哪个for循环是死循环？",
            "options": ["A. for(;;){}", "B. for(i=0; i<10; i++){}", "C. for(i=0; i>0; i++){}", "D. for(i=10; i>0; i--){}"],
            "correct_answer": "A",
            "explanation": "for(;;)没有初始化、没有条件判断（默认为真）、没有更新，会一直执行下去。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_while_choice(kp_name, order):
    templates = [
        {
            "title": "while循环",
            "question_text": "while循环是哪种类型的循环？",
            "options": ["A. 后测试循环", "B. 前测试循环", "C. 无限循环", "D. 计数循环"],
            "correct_answer": "B",
            "explanation": "while循环是前测试循环，先判断条件再执行循环体，循环体可能一次都不执行。",
            "difficulty": 1
        },
        {
            "title": "do-while特点",
            "question_text": "do-while循环的特点是？",
            "options": ["A. 循环体可能一次都不执行", "B. 循环体至少执行一次", "C. 必须知道循环次数", "D. 只能用于计数循环"],
            "correct_answer": "B",
            "explanation": "do-while是后测试循环，先执行循环体再判断条件，所以循环体至少执行一次。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_nested_loop_choice(kp_name, order):
    templates = [
        {
            "title": "循环嵌套",
            "question_text": "在循环嵌套中，外层循环执行一次，内层循环会？",
            "options": ["A. 只执行一次", "B. 执行完整一轮", "C. 不执行", "D. 执行两次"],
            "correct_answer": "B",
            "explanation": "外层循环执行一次，内层循环会从头到尾执行完整的一轮，然后外层再执行下一次。",
            "difficulty": 2
        },
        {
            "title": "九九乘法表",
            "question_text": "打印九九乘法表需要使用什么嵌套？",
            "options": ["A. for套while", "B. while套do-while", "C. for套for", "D. 只需一个循环"],
            "correct_answer": "C",
            "explanation": "九九乘法表需要行列嵌套，通常使用两个for循环嵌套实现，外层控制行，内层控制列。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_break_continue_choice(kp_name, order):
    templates = [
        {
            "title": "break作用范围",
            "question_text": "break语句只能跳出哪一层循环？",
            "options": ["A. 所有循环", "B. 最内层循环", "C. 最外层循环", "D. 指定层循环"],
            "correct_answer": "B",
            "explanation": "break只能跳出最内层的循环，如果要跳出多层循环，需要使用goto或设置多个退出条件。",
            "difficulty": 1
        },
        {
            "title": "continue语句",
            "question_text": "continue语句的作用是？",
            "options": ["A. 跳出循环", "B. 跳过本次循环剩余部分，进入下一次", "C. 结束程序", "D. 返回函数值"],
            "correct_answer": "B",
            "explanation": "continue跳过本次循环体中剩余的语句，直接进入下一次循环判断。",
            "difficulty": 1
        },
        {
            "title": "break与continue区别",
            "question_text": "break和continue的主要区别是？",
            "options": ["A. 没有区别", "B. break结束循环，continue跳过本次", "C. continue用于for，break用于while", "D. break只能用于循环"],
            "correct_answer": "B",
            "explanation": "break直接结束整个循环，continue跳过本次循环的剩余部分继续下一次循环。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_function_choice(kp_name, order):
    templates = [
        {
            "title": "函数定义",
            "question_text": "以下哪个是正确的函数定义？",
            "options": ["A. int func {}", "B. int func() {}", "C. func int() {}", "D. int (func) {}"],
            "correct_answer": "B",
            "explanation": "函数定义格式：返回类型 函数名(参数列表) { 函数体 }。",
            "difficulty": 1
        },
        {
            "title": "函数调用",
            "question_text": "调用函数的格式是？",
            "options": ["A. call 函数名();", "B. 函数名();", "C. run 函数名();", "D. exec 函数名();"],
            "correct_answer": "B",
            "explanation": "C语言中调用函数直接使用函数名加括号，如func();即可。",
            "difficulty": 1
        },
        {
            "title": "函数声明",
            "question_text": "函数声明的作用是？",
            "options": ["A. 定义函数功能", "B. 告诉编译器函数存在及其签名", "C. 调用函数", "D. 返回函数值"],
            "correct_answer": "B",
            "explanation": "函数声明（函数原型）告诉编译器函数的存在、返回类型和参数类型，以便在定义之前调用。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_macro_choice(kp_name, order):
    templates = [
        {
            "title": "无参宏定义",
            "question_text": "定义宏常量PI为3.14，正确的写法是？",
            "options": ["A. const PI = 3.14;", "B. #define PI 3.14", "C. #define PI = 3.14", "D. int PI = 3.14;"],
            "correct_answer": "B",
            "explanation": "宏定义使用#define，格式为#define 宏名 值。注意值前不能加=号。",
            "difficulty": 1
        },
        {
            "title": "带参宏",
            "question_text": "以下哪个是带参宏SQUARE(x)的正确定义？",
            "options": ["A. #define SQUARE(x) x*x", "B. #define SQUARE(x) (x)*(x)", "C. #define SQUARE(x) {x*x}", "D. #define SQUARE(x) =x*x"],
            "correct_answer": "B",
            "explanation": "带参宏定义时，参数要用括号包围，整体也要用括号，避免替换后优先级问题。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_cond_compile_choice(kp_name, order):
    templates = [
        {
            "title": "条件编译",
            "question_text": "#ifdef DEBUG的作用是？",
            "options": ["A. 定义DEBUG", "B. 如果定义了DEBUG则编译下面的代码", "C. 取消定义DEBUG", "D. 输出DEBUG的值"],
            "correct_answer": "B",
            "explanation": "#ifdef表示"如果有定义过\"，#ifdef DEBUG表示如果定义了DEBUG宏，则编译后续代码。",
            "difficulty": 1
        },
        {
            "title": "防止重复包含",
            "question_text": "防止头文件重复包含的正确格式是？",
            "options": ["A. #ifndef HEADER_H #define HEADER_H ... #endif", "B. #ifndef HEADER_H ... #endif", "C. #ifdef HEADER_H ... #endif", "D. #define HEADER_H ... #endif"],
            "correct_answer": "A",
            "explanation": "使用#ifndef、#define、#endif组合可以防止头文件被重复包含。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_1d_array_choice(kp_name, order):
    templates = [
        {
            "title": "数组定义",
            "question_text": "定义一个包含10个整数的数组，正确的写法是？",
            "options": ["A. int array(10);", "B. int array[10];", "C. int array{10};", "D. int [10]array;"],
            "correct_answer": "B",
            "explanation": "数组定义格式：类型 数组名[长度];，长度用方括号包围。",
            "difficulty": 1
        },
        {
            "title": "数组下标",
            "question_text": "数组的第一个元素下标是？",
            "options": ["A. 1", "B. 0", "C. -1", "D. 由程序员指定"],
            "correct_answer": "B",
            "explanation": "C语言数组下标从0开始，所以第一个元素是array[0]，最后一个是array[n-1]。",
            "difficulty": 1
        },
        {
            "title": "数组初始化",
            "question_text": "int a[5]={1,2}; 请问a[2]的值是？",
            "options": ["A. 1", "B. 2", "C. 0", "D. 随机值"],
            "correct_answer": "C",
            "explanation": "部分初始化时，未赋值的元素默认为0。所以a[0]=1, a[1]=2, a[2]=0, a[3]=0, a[4]=0。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_2d_array_choice(kp_name, order):
    templates = [
        {
            "title": "二维数组定义",
            "question_text": "定义一个3行4列的二维整型数组，正确的是？",
            "options": ["A. int array[3,4];", "B. int array[3][4];", "C. int array(3)(4);", "D. int[3]array[4];"],
            "correct_answer": "B",
            "explanation": "二维数组定义格式：类型 数组名[行数][列数];，行列都用方括号。",
            "difficulty": 1
        },
        {
            "title": "二维数组内存",
            "question_text": "二维数组在内存中的存储方式是？",
            "options": ["A. 按行存储", "B. 按列存储", "C. 随机存储", "D. 索引存储"],
            "correct_answer": "A",
            "explanation": "C语言二维数组按行存储，即先存储第一行所有元素，再存储第二行，依此类推。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_string_choice(kp_name, order):
    templates = [
        {
            "title": "字符串结束符",
            "question_text": "C语言中，字符串的结束标志是？",
            "options": ["A. '\\0'", "B. '\\n'", "C. '0'", "D. ' '"],
            "correct_answer": "A",
            "explanation": "C语言字符串以'\\0'（空字符）作为结束标志，strlen()等函数依赖这个标志计算长度。",
            "difficulty": 1
        },
        {
            "title": "字符串定义",
            "question_text": "以下哪个是合法的字符串定义？",
            "options": ["A. char s = \"hello\";", "B. char s[] = \"hello\";", "C. char s = 'hello';", "D. char s[5] = \"hello\";"],
            "correct_answer": "B",
            "explanation": "字符串应该用双引号包围，且定义时需要字符数组或字符指针来存储。",
            "difficulty": 1
        },
        {
            "title": "字符串长度",
            "question_text": "char s[]=\"hello\"; 请问字符串s的长度是？",
            "options": ["A. 4", "B. 5", "C. 6", "D. 7"],
            "correct_answer": "B",
            "explanation": "strlen()返回字符串长度，不包括结束符'\\0'。\"hello\"有5个字符，所以长度是5。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_pointer_choice(kp_name, order):
    templates = [
        {
            "title": "指针定义",
            "question_text": "定义一个指向int类型变量的指针p，正确的是？",
            "options": ["A. int *p;", "B. int p*;", "C. *int p;", "D. int p;"],
            "correct_answer": "A",
            "explanation": "指针定义格式：类型 *指针变量名;，*表示这是一个指针。",
            "difficulty": 1
        },
        {
            "title": "取地址运算符",
            "question_text": "如果int a=10; &a表示什么？",
            "options": ["A. a的值", "B. a的地址", "C. a的大小", "D. a的类型"],
            "correct_answer": "B",
            "explanation": "&是取地址运算符，&a表示变量a在内存中的地址。",
            "difficulty": 1
        },
        {
            "title": "指针赋值",
            "question_text": "int a=10, *p=&a; *p的值是？",
            "options": ["A. 10", "B. a的地址", "C. 不确定", "D. 编译错误"],
            "correct_answer": "A",
            "explanation": "*p表示指针p所指向的内存单元的值，即a的值，所以是10。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_pointer_array_choice(kp_name, order):
    templates = [
        {
            "title": "指针与数组",
            "question_text": "int a[5], *p=a; p+1指向？",
            "options": ["A. a[0]", "B. a[1]", "C. a[2]", "D. a的地址"],
            "correct_answer": "B",
            "explanation": "数组名a等价于&a[0]，即首元素地址。p+1指向下一个元素，所以是a[1]。",
            "difficulty": 2
        },
        {
            "title": "指针算术",
            "question_text": "char *p; 如果p的值为1000，则p+1的值是？",
            "options": ["A. 1000", "B. 1001", "C. 1002", "D. 1004"],
            "correct_answer": "B",
            "explanation": "指针算术运算中，加1表示向前移动一个元素的大小。char占1字节，所以p+1=1001。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_pointer_string_choice(kp_name, order):
    templates = [
        {
            "title": "字符串与指针",
            "question_text": "char *p=\"hello\"; *p的值是？",
            "options": ["A. 'h'", "B. \"hello\"", "C. 'o'", "D. '0'"],
            "correct_answer": "A",
            "explanation": "p指向字符串首字符'*p'就是'h'。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_pointer_func_choice(kp_name, order):
    templates = [
        {
            "title": "指针作参数",
            "question_text": "函数参数使用指针的目的是？",
            "options": ["A. 减少参数个数", "B. 在函数内修改外部变量", "C. 加快运行速度", "D. 避免参数传递"],
            "correct_answer": "B",
            "explanation": "指针作为参数可以在函数内部修改外部变量的值，实现双向通信。",
            "difficulty": 2
        },
        {
            "title": "返回指针",
            "question_text": "函数返回指针时，需要注意什么？",
            "options": ["A. 不能返回局部变量地址", "B. 必须返回整数", "C. 返回后指针自动+1", "D. 不需要注意事项"],
            "correct_answer": "A",
            "explanation": "不能返回局部变量（栈内存）的地址，因为函数结束后该内存会被回收。应该返回静态变量或堆内存的地址。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_struct_choice(kp_name, order):
    templates = [
        {
            "title": "结构体定义",
            "question_text": "定义结构体的关键字是？",
            "options": ["A. struct", "B. structure", "C. structtype", "D. typedef"],
            "correct_answer": "A",
            "explanation": "C语言使用struct关键字定义结构体，如struct Student {int age;};",
            "difficulty": 1
        },
        {
            "title": "结构体变量定义",
            "question_text": "以下哪个是定义结构体变量的正确方式？",
            "options": ["A. struct Student s;", "B. Student s;", "C. struct {int age;} s;", "D. both A and C"],
            "correct_answer": "D",
            "explanation": "可以使用struct Student s;或者先typedef再Student s;两种方式定义结构体变量。",
            "difficulty": 1
        },
        {
            "title": "结构体成员访问",
            "question_text": "访问结构体变量s的成员age，正确的是？",
            "options": ["A. s.age", "B. s->age", "C. *s.age", "D. s[age]"],
            "correct_answer": "A",
            "explanation": "使用点运算符.访问结构体变量的成员，如s.age。如果s是指针，使用s->age。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_struct_app_choice(kp_name, order):
    templates = [
        {
            "title": "结构体数组",
            "question_text": "定义结构体数组的正确方式是？",
            "options": ["A. struct Student[5];", "B. struct Student s[5];", "C. struct Student(5);", "D. struct[5] Student;"],
            "correct_answer": "B",
            "explanation": "结构体数组定义：struct 类型名 数组名[长度];，如struct Student stu[5];",
            "difficulty": 2
        },
        {
            "title": "结构体指针",
            "question_text": "p是指向结构体的指针，访问成员的运算符是？",
            "options": ["A. .", "B. ->", "C. *", "D. both A and B"],
            "correct_answer": "B",
            "explanation": "结构体指针使用->运算符访问成员，如p->age。也可以(*p).age，但->更简洁。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_union_choice(kp_name, order):
    templates = [
        {
            "title": "联合体",
            "question_text": "联合体（union）与结构体（struct）的主要区别是？",
            "options": ["A. 联合体所有成员共享同一块内存", "B. 联合体成员个数不同", "C. 没有区别", "D. 联合体不能有指针成员"],
            "correct_answer": "A",
            "explanation": "联合体的所有成员共享同一块内存，修改一个成员会影响其他成员的值。",
            "difficulty": 2
        },
        {
            "title": "联合体大小",
            "question_text": "union Data {int i; char c; double d;}; 请问Data类型的大小是？",
            "options": ["A. 4字节", "B. 8字节", "C. 13字节", "D. 取决于最大成员"],
            "correct_answer": "D",
            "explanation": "联合体的大小取决于最大成员的大小，因为所有成员共享同一块内存。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_enum_choice(kp_name, order):
    templates = [
        {
            "title": "枚举定义",
            "question_text": "枚举类型的定义关键字是？",
            "options": ["A. union", "B. struct", "C. enum", "D. int"],
            "correct_answer": "C",
            "explanation": "C语言使用enum关键字定义枚举类型，如enum Color {RED, GREEN, BLUE};",
            "difficulty": 1
        },
        {
            "title": "枚举值",
            "question_text": "enum Color {RED, GREEN, BLUE}; RED的值是？",
            "options": ["A. 字符串\"RED\"", "B. 0", "C. 'R'", "D. 1"],
            "correct_answer": "B",
            "explanation": "枚举值默认从0开始，RED=0, GREEN=1, BLUE=2。也可以显式指定值。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_file_choice(kp_name, order):
    templates = [
        {
            "title": "文件打开函数",
            "question_text": "打开文件的函数是？",
            "options": ["A. open()", "B. fopen()", "C. file_open()", "D. read()"],
            "correct_answer": "B",
            "explanation": "C语言使用fopen()函数打开文件，返回FILE指针。",
            "difficulty": 1
        },
        {
            "title": "文件关闭",
            "question_text": "关闭文件的函数是？",
            "options": ["A. close()", "B. fclose()", "C. file_close()", "D. end()"],
            "correct_answer": "B",
            "explanation": "使用fclose()函数关闭文件，参数是fopen()返回的FILE指针。",
            "difficulty": 1
        },
        {
            "title": "文件模式",
            "question_text": "以只读方式打开文件，模式字符串是？",
            "options": ["A. \"rw\"", "B. \"r\"", "C. \"w\"", "D. \"a\""],
            "correct_answer": "B",
            "explanation": "\"r\"只读，\"w\"只写（会清空文件），\"a\"追加，\"r+\"读写。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_file_app_choice(kp_name, order):
    templates = [
        {
            "title": "文件定位",
            "question_text": "将文件位置指针移到文件开头，使用哪个函数？",
            "options": ["A. fseek()", "B. rewind()", "C. ftell()", "D. fgetc()"],
            "correct_answer": "B",
            "explanation": "rewind()将文件位置指针移到文件开头，fseek()可以移到任意位置。",
            "difficulty": 2
        },
        {
            "title": "fseek参数",
            "question_text": "fseek(fp, 10, SEEK_SET); 表示？",
            "options": ["A. 从文件开头偏移10字节", "B. 从当前位置偏移10字节", "C. 从文件末尾偏移10字节", "D. 偏移10个字符"],
            "correct_answer": "A",
            "explanation": "SEEK_SET表示文件开头，SEEK_CUR表示当前位置，SEEK_END表示文件末尾。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_design_flow_choice(kp_name, order):
    templates = [
        {
            "title": "程序设计步骤",
            "question_text": "程序设计的基本步骤是？",
            "options": ["A. 编码→测试→维护", "B. 分析→设计→编码→测试→维护", "C. 编码→调试→运行", "D. 写代码→编译"],
            "correct_answer": "B",
            "explanation": "程序设计包括：问题分析、算法设计、编码实现、测试调试、运行维护等步骤。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_modular_choice(kp_name, order):
    templates = [
        {
            "title": "模块化设计",
            "question_text": "模块化设计的主要目的是？",
            "options": ["A. 增加代码量", "B. 提高代码复用性和可维护性", "C. 让程序运行更快", "D. 减少变量数量"],
            "correct_answer": "B",
            "explanation": "模块化设计将程序分成独立模块，提高代码复用性、可维护性和可读性。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_case_choice(kp_name, order):
    templates = [
        {
            "title": "学生管理系统",
            "question_text": "学生管理系统通常使用哪种数据结构存储学生信息？",
            "options": ["A. 数组", "B. 结构体数组", "C. 指针", "D. 文件"],
            "correct_answer": "B",
            "explanation": "学生信息通常用结构体表示，多个学生用结构体数组存储。",
            "difficulty": 3
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_file_case_choice(kp_name, order):
    templates = [
        {
            "title": "文件案例",
            "question_text": "将学生信息保存到文件中，应该使用什么模式打开文件？",
            "options": ["A. \"r\"", "B. \"w\"", "C. \"a\"", "D. \"rb\""],
            "correct_answer": "B",
            "explanation": "写入文件应使用\"w\"（新建或清空）或\"a\"（追加）模式。",
            "difficulty": 2
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


def _gen_generic_choice(kp_name, order):
    templates = [
        {
            "title": "知识点理解",
            "question_text": f"关于{kp_name}的说法，正确的是？",
            "options": ["A. 这是C语言的重要概念", "B. 需要通过练习掌握", "C. 是后续学习的基础", "D. 以上都对"],
            "correct_answer": "D",
            "explanation": f"{kp_name}是C语言学习中的重要概念，需要理解并通过练习巩固。",
            "difficulty": 1
        }
    ]
    t = templates[order % len(templates)]
    return {
        "title": t["title"],
        "question_text": t["question_text"],
        "options": t["options"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": t["difficulty"],
        "knowledge_points": [kp_name]
    }


# ============================================================
# 填空题生成函数
# ============================================================

def _gen_c_structure_fill(kp_name, order):
    templates = [
        {"question_text": "C程序的执行入口是______函数。", "correct_answer": "main", "explanation": "每个C程序必须有且只能有一个main函数作为程序执行的入口。"},
        {"question_text": "在C语言中，#include <stdio.h>是______指令。", "correct_answer": "预处理", "explanation": "#include是预处理指令，在编译前处理，用于引入头文件。"},
        {"question_text": "C程序的基本组成部分包括预处理指令、______和语句。", "correct_answer": "main函数", "explanation": "C程序由预处理指令、main函数和语句三部分组成。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_statement_comment_fill(kp_name, order):
    templates = [
        {"question_text": "C语言中，每条语句以______结尾。", "correct_answer": "分号", "explanation": "分号;是C语言语句的结束标志。"},
        {"question_text": "单行注释使用______开头。", "correct_answer": "//", "explanation": "C语言使用//表示单行注释，/* */表示多行注释。"},
        {"question_text": "多行注释使用______和______包围。", "correct_answer": "/* */", "explanation": "多行注释用/*开头，用*/结尾。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_data_type_fill(kp_name, order):
    templates = [
        {"question_text": "C语言的基本数据类型包括int、char、______和double。", "correct_answer": "float", "explanation": "C语言四种基本数据类型：整型int、字符型char、浮点型float和double。"},
        {"question_text": "int类型通常占用______个字节。", "correct_answer": "4", "explanation": "在现代系统中，int类型通常占用4个字节。"},
        {"question_text": "char类型用于存储______。", "correct_answer": "单个字符", "explanation": "char用于存储单个字符，通常占用1字节。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_identifier_fill(kp_name, order):
    templates = [
        {"question_text": "标识符由字母、数字和______组成。", "correct_answer": "下划线", "explanation": "标识符可以包含字母、数字和下划线。"},
        {"question_text": "标识符必须以______或下划线开头。", "correct_answer": "字母", "explanation": "标识符第一个字符必须是字母或下划线，不能以数字开头。"},
        {"question_text": "C语言的关键字如int、if等______（能/不能）用作标识符。", "correct_answer": "不能", "explanation": "关键字是保留字，不能用作标识符。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_var_const_fill(kp_name, order):
    templates = [
        {"question_text": "定义常量应使用______关键字。", "correct_answer": "const", "explanation": "const用于定义常量，如const int MAX=100;。"},
        {"question_text": "宏定义使用______预处理指令。", "correct_answer": "#define", "explanation": "#define用于定义宏常量，如#define PI 3.14。"},
        {"question_text": "变量在程序运行期间其值可以______。", "correct_answer": "改变/变化", "explanation": "变量的值在程序运行期间可以修改。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_printf_fill(kp_name, order):
    templates = [
        {"question_text": "printf中输出整数使用格式符______。", "correct_answer": "%d", "explanation": "%d用于输出int类型整数，%f用于输出浮点数。"},
        {"question_text": "换行符是______。", "correct_answer": "\\n", "explanation": "\\n是转义字符，表示换行。"},
        {"question_text": "输出双精度浮点数应使用格式符______。", "correct_answer": "%lf", "explanation": "%lf用于输出double类型（长浮点）。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_algorithm_fill(kp_name, order):
    templates = [
        {"question_text": "算法的特性包括有穷性、确定性、可行性和输入输出______。", "correct_answer": "输出", "explanation": "算法必须具有输出特性，至少有一个或多个输出。"},
        {"question_text": "在流程图中，菱形框表示______。", "correct_answer": "判断/条件", "explanation": "流程图菱形表示条件判断。"},
        {"question_text": "描述算法的三种方法是自然语言、流程图和______。", "correct_answer": "伪代码", "explanation": "伪代码是介于自然语言和编程语言之间的描述方式。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 2,
        "knowledge_points": [kp_name]
    }


def _gen_relational_fill(kp_name, order):
    templates = [
        {"question_text": "大于等于运算符是______。", "correct_answer": ">=", "explanation": ">=表示大于等于。"},
        {"question_text": "判断相等的运算符是______。", "correct_answer": "==", "explanation": "==用于比较相等，=是赋值。"},
        {"question_text": "不等于运算符是______。", "correct_answer": "!=", "explanation": "!=表示不等于。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_logical_fill(kp_name, order):
    templates = [
        {"question_text": "逻辑与运算符是______。", "correct_answer": "&&", "explanation": "&&是逻辑与运算符。"},
        {"question_text": "逻辑或运算符是______。", "correct_answer": "||", "explanation": "||是逻辑或运算符。"},
        {"question_text": "逻辑非运算符是______。", "correct_answer": "!", "explanation": "!是逻辑非运算符。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_if_fill(kp_name, order):
    templates = [
        {"question_text": "if语句的条件必须用______括起来。", "correct_answer": "圆括号/()", "explanation": "if条件必须用括号包围，如if(a>b)。"},
        {"question_text": "else与______的if配对。", "correct_answer": "最接近的未配对", "explanation": "else总是与最近的未配对if配对。"},
        {"question_text": "条件运算符是C语言中唯一的______运算符。", "correct_answer": "三目", "explanation": "条件运算符?:是唯一的三目运算符。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_switch_fill(kp_name, order):
    templates = [
        {"question_text": "switch语句的case常量必须是______或字符型。", "correct_answer": "整型", "explanation": "case常量必须是整型或字符型，不能是浮点型。"},
        {"question_text": "break语句的作用是跳出______语句。", "correct_answer": "switch", "explanation": "break用于跳出switch语句，防止case穿透。"},
        {"question_text": "switch语句中______分支可选，用于处理所有case都不匹配的情况。", "correct_answer": "default", "explanation": "default是可选的，当所有case都不匹配时执行。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_for_fill(kp_name, order):
    templates = [
        {"question_text": "for循环的三个表达式分别是初始化、条件和______。", "correct_answer": "更新", "explanation": "for(初始化; 条件; 更新)。"},
        {"question_text": "for循环中，初始化只执行______次。", "correct_answer": "一/1", "explanation": "初始化只在循环开始前执行一次。"},
        {"question_text": "for(;;)表示______循环。", "correct_answer": "无限/死", "explanation": "三个表达式都省略时，条件默认为真，导致无限循环。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_while_fill(kp_name, order):
    templates = [
        {"question_text": "while循环是______测试循环。", "correct_answer": "前", "explanation": "while先判断条件再执行循环体。"},
        {"question_text": "do-while循环是______测试循环。", "correct_answer": "后", "explanation": "do-while先执行循环体再判断条件。"},
        {"question_text": "do-while循环体至少执行______次。", "correct_answer": "一/1", "explanation": "因为先执行后判断，循环体至少执行一次。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_nested_loop_fill(kp_name, order):
    templates = [
        {"question_text": "外层循环执行一次，内层循环执行完整______。", "correct_answer": "一轮", "explanation": "内层循环会完整执行一轮，然后外层再执行下一次。"},
        {"question_text": "循环嵌套时，要注意控制循环变量的______避免冲突。", "correct_answer": "作用域/范围", "explanation": "内外层循环变量不要冲突。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 2,
        "knowledge_points": [kp_name]
    }


def _gen_break_continue_fill(kp_name, order):
    templates = [
        {"question_text": "break语句跳出______层循环。", "correct_answer": "一/1", "explanation": "break只能跳出最内层循环。"},
        {"question_text": "continue语句跳过本次循环的______部分。", "correct_answer": "剩余", "explanation": "continue跳过本次循环剩余语句，进入下一次。"},
        {"question_text": "break只能用于______和循环语句。", "correct_answer": "switch", "explanation": "break可以用于switch和循环，不能用于if。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_function_fill(kp_name, order):
    templates = [
        {"question_text": "函数的返回类型和参数列表构成函数的______。", "correct_answer": "原型/签名", "explanation": "函数原型告诉编译器函数的接口。"},
        {"question_text": "函数调用通过函数名和______列表执行函数。", "correct_answer": "实参", "explanation": "调用函数时传递的是实参。"},
        {"question_text": "如果函数定义在调用之后，需要先进行函数______。", "correct_answer": "声明", "explanation": "函数声明在调用之前，告诉编译器函数存在。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_macro_fill(kp_name, order):
    templates = [
        {"question_text": "带参宏定义时，参数应该用______包围。", "correct_answer": "圆括号/()", "explanation": "宏定义参数要加括号，避免替换问题。"},
        {"question_text": "防止头文件重复包含使用______和#endif。", "correct_answer": "#ifndef", "explanation": "使用#ifndef、#define、#endif组合防止重复包含。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_1d_array_fill(kp_name, order):
    templates = [
        {"question_text": "数组定义格式：类型 数组名[______];", "correct_answer": "长度/数量", "explanation": "数组需要指定长度，如int a[10];。"},
        {"question_text": "数组下标从______开始。", "correct_answer": "0/零", "explanation": "C语言数组下标从0开始，第一个元素是a[0]。"},
        {"question_text": "部分初始化时，未赋值的元素默认为______。", "correct_answer": "0", "explanation": "int a[5]={1};则a[0]=1,其他为0。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_2d_array_fill(kp_name, order):
    templates = [
        {"question_text": "二维数组定义格式：类型 数组名[______][______];", "correct_answer": "行数 列数", "explanation": "二维数组需要指定行数和列数。"},
        {"question_text": "二维数组在内存中按______存储。", "correct_answer": "行", "explanation": "C语言二维数组按行存储。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_string_fill(kp_name, order):
    templates = [
        {"question_text": "C语言字符串以______作为结束标志。", "correct_answer": "\\0", "explanation": "字符串以\\0结尾，strlen()依赖此标志。"},
        {"question_text": "字符串\"hello\"占用______个字节。", "correct_answer": "6", "explanation": "5个字符+1个结束符=6字节。"},
        {"question_text": "使用scanf输入字符串应使用______格式符。", "correct_answer": "%s", "explanation": "%s用于输入字符串。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_pointer_fill(kp_name, order):
    templates = [
        {"question_text": "指针定义格式：类型 *______名;", "correct_answer": "指针变量", "explanation": "int *p;定义整型指针p。"},
        {"question_text": "&是______运算符。", "correct_answer": "取地址", "explanation": "&是取地址运算符。"},
        {"question_text": "*p表示指针p指向的______。", "correct_answer": "值/内容", "explanation": "*p获取指针指向的内存单元的值。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_struct_fill(kp_name, order):
    templates = [
        {"question_text": "定义结构体使用______关键字。", "correct_answer": "struct", "explanation": "struct用于定义结构体。"},
        {"question_text": "访问结构体成员使用______运算符。", "correct_answer": ". /点", "explanation": "s.age使用点运算符访问成员。"},
        {"question_text": "结构体指针访问成员使用______运算符。", "correct_answer": "->", "explanation": "p->age或(*p).age访问结构体指针成员。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_union_enum_fill(kp_name, order):
    templates = [
        {"question_text": "联合体的所有成员共享______块内存。", "correct_answer": "同一", "explanation": "联合体成员共享同一内存空间。"},
        {"question_text": "枚举类型使用______关键字定义。", "correct_answer": "enum", "explanation": "enum用于定义枚举类型。"},
        {"question_text": "枚举值默认从______开始。", "correct_answer": "0/零", "explanation": "枚举值默认从0开始，如RED=0, GREEN=1。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_file_fill(kp_name, order):
    templates = [
        {"question_text": "打开文件使用______函数。", "correct_answer": "fopen", "explanation": "fopen()用于打开文件。"},
        {"question_text": "关闭文件使用______函数。", "correct_answer": "fclose", "explanation": "fclose()用于关闭文件。"},
        {"question_text": "以只读方式打开文件，模式字符串是______。", "correct_answer": "\"r\"", "explanation": "\"r\"表示只读模式打开文件。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


def _gen_generic_fill(kp_name, order):
    templates = [
        {"question_text": f"{kp_name}是C语言学习的重要内容。", "correct_answer": "正确/是", "explanation": f"{kp_name}是重要概念。"}
    ]
    t = templates[order % len(templates)]
    return {
        "question_text": t["question_text"],
        "correct_answer": t["correct_answer"],
        "explanation": t["explanation"],
        "difficulty": 1,
        "knowledge_points": [kp_name]
    }


# ============================================================
# 主函数：生成并导入题目
# ============================================================

async def generate_and_import_questions():
    """生成并导入所有习题到数据库"""
    async with AsyncSessionLocal() as db:
        # 获取所有章节和小节信息
        from sqlalchemy import select
        sections_query = select(Section, Chapter).join(Chapter, Section.chapter_id == Chapter.id)
        result = await db.execute(sections_query)
        section_chapter_map = {}

        for section, chapter in result.all():
            section_chapter_map[(chapter.order_index, section.order_index)] = {
                "section_id": section.id,
                "chapter_id": chapter.id
            }

        print(f"找到 {len(section_chapter_map)} 个小节")

        total_imported = 0

        # 遍历每个章节小节
        for chapter_idx, sections in COURSE_DATA.items():
            for section_idx, section_data in sections.items():
                key = (chapter_idx, section_idx)
                if key not in section_chapter_map:
                    print(f"警告: 未找到章节{chapter_idx}小节{section_idx}")
                    continue

                section_info = section_chapter_map[key]
                section_id = section_info["section_id"]
                chapter_id = section_info["chapter_id"]

                kps = section_data["knowledge_points"]
                base_count = section_data["base_count"]

                # 计算选择和填空题数量（6:4比例）
                choice_count = int(base_count * 0.6)
                fill_count = base_count - choice_count

                questions = []
                order = 1

                # 为每个知识点生成题目
                for kp in kps:
                    kp_name = kp["name"]
                    difficulty = kp["difficulty"]

                    # 生成选择题
                    for i in range(2):  # 每个知识点2道选择题
                        if choice_count > 0:
                            q_data = generate_questions_for_kp(kp_name, difficulty, "choice", order)
                            q = SectionBaseQuestion(
                                section_id=section_id,
                                chapter_id=chapter_id,
                                question_source="base",
                                order_index=order,
                                question_type="choice",
                                title=q_data.get("title", ""),
                                question_text=q_data["question_text"],
                                options=q_data["options"],
                                correct_answer=q_data["correct_answer"],
                                explanation=q_data.get("explanation", ""),
                                knowledge_points=q_data["knowledge_points"],
                                difficulty=q_data.get("difficulty", 1)
                            )
                            questions.append(q)
                            choice_count -= 1
                            order += 1

                    # 生成填空题
                    for i in range(1):  # 每个知识点1道填空题
                        if fill_count > 0:
                            q_data = generate_questions_for_kp(kp_name, difficulty, "fill_blank", order)
                            q = SectionBaseQuestion(
                                section_id=section_id,
                                chapter_id=chapter_id,
                                question_source="base",
                                order_index=order,
                                question_type="fill_blank",
                                title="",
                                question_text=q_data["question_text"],
                                options=None,
                                correct_answer=q_data["correct_answer"],
                                explanation=q_data.get("explanation", ""),
                                knowledge_points=q_data["knowledge_points"],
                                difficulty=q_data.get("difficulty", 1)
                            )
                            questions.append(q)
                            fill_count -= 1
                            order += 1

                # 批量插入
                if questions:
                    db.add_all(questions)
                    await db.commit()
                    total_imported += len(questions)
                    print(f"  章节{chapter_idx}小节{section_idx}: {section_data['title']} - 导入{len(questions)}题")

        print(f"\n总计导入 {total_imported} 道题目")


async def main():
    await generate_and_import_questions()


if __name__ == "__main__":
    asyncio.run(main())
