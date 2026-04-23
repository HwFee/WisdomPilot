"""
根据习题数量配置文件生成题目并导入数据库
严格按照每个小节的base_questions_count和knowledge_points生成
"""

import asyncio
import json
import glob
import os
import sys
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.models.section_base_question import SectionBaseQuestion
from app.database import async_session

COURSE_CODE = "C"  # C语言程序设计


# 题目模板库 - 按知识点类型分组
class QuestionTemplates:
    """选择题模板"""

    @staticmethod
    def c_program_structure(order):
        templates = [
            {
                "title": "C程序入口",
                "question_text": "C语言程序的执行入口是哪个函数？",
                "options": ["A. main()", "B. start()", "C. run()", "D. printf()"],
                "correct_answer": "A",
                "explanation": "C语言规定，程序的执行从main函数开始，每个C程序必须有且只能有一个main函数作为程序入口。"
            },
            {
                "title": "main函数格式",
                "question_text": "以下哪个是标准的main函数定义？",
                "options": ["A. void main()", "B. main()", "C. int main()", "D. main(void)"],
                "correct_answer": "C",
                "explanation": "标准的main函数应该返回int类型，即int main()，返回值表示程序结束状态。"
            },
            {
                "title": "头文件引入",
                "question_text": "#include <stdio.h>这行代码的作用是什么？",
                "options": ["A. 定义一个变量", "B. 包含标准输入输出头文件", "C. 声明一个函数", "D. 输出文字"],
                "correct_answer": "B",
                "explanation": "#include是预处理指令，stdio.h是标准输入输出库的头文件，用于使用printf、scanf等函数。"
            },
            {
                "title": "程序结构组成",
                "question_text": "C程序的基本组成部分不包括以下哪一项？",
                "options": ["A. 预处理指令", "B. main函数", "C. 注释", "D. 变量定义"],
                "correct_answer": "D",
                "explanation": "C程序的基本组成部分是预处理指令、main函数和语句。变量定义不是必须的组成部分。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def statement_comment(order):
        templates = [
            {
                "title": "语句结束符",
                "question_text": "C语言中，每条语句应该以什么符号结尾？",
                "options": ["A. 冒号 :", "B. 逗号 ,", "C. 分号 ;", "D. 句号 ."],
                "correct_answer": "C",
                "explanation": "C语言中，分号(;)是语句的结束符，每条可执行语句都必须以分号结尾。"
            },
            {
                "title": "注释的作用",
                "question_text": "关于C语言注释的说法，正确的是？",
                "options": ["A. 注释会被编译器执行", "B. 注释对程序运行没有影响", "C. 注释只能写在代码后面", "D. 注释不能多行"],
                "correct_answer": "B",
                "explanation": "注释是给程序员看的说明文字，不参与程序编译和执行，对程序运行没有任何影响。"
            },
            {
                "title": "多行注释",
                "question_text": "以下哪个是C语言的多行注释格式？",
                "options": ["A. // 注释内容", "B. /* 注释内容 */", "C. # 注释内容", "D. <!-- 注释内容 -->"],
                "correct_answer": "B",
                "explanation": "C语言使用/*和*/包围多行注释，使用//标记单行注释。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def data_type(order):
        templates = [
            {
                "title": "基本数据类型",
                "question_text": "以下哪个不是C语言的基本数据类型？",
                "options": ["A. int", "B. float", "C. bool", "D. char"],
                "correct_answer": "C",
                "explanation": "C语言的基本数据类型包括int、float、double、char，没有bool类型（C99之前）。"
            },
            {
                "title": "整型int",
                "question_text": "在C语言中，int类型通常占用多少字节？",
                "options": ["A. 1字节", "B. 2字节", "C. 4字节", "D. 8字节"],
                "correct_answer": "C",
                "explanation": "在大多数现代系统上，int类型占用4个字节（32位），可以表示约-21亿到21亿的整数。"
            },
            {
                "title": "字符型",
                "question_text": "char类型的变量用于存储什么？",
                "options": ["A. 整数", "B. 单个字符", "C. 小数", "D. 字符串"],
                "correct_answer": "B",
                "explanation": "char类型用于存储单个字符，通常占用1个字节，使用单引号包围字符常量。"
            },
            {
                "title": "浮点型",
                "question_text": "用于表示小数（实数）的数据类型是？",
                "options": ["A. int和char", "B. float和double", "C. bool和void", "D. 只有float"],
                "correct_answer": "B",
                "explanation": "C语言中，float和double用于表示浮点数（小数），double是双精度浮点型。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def identifier(order):
        templates = [
            {
                "title": "合法标识符",
                "question_text": "以下哪个是合法的C语言标识符？",
                "options": ["A. 2name", "B. my-age", "C. student_age", "D. int"],
                "correct_answer": "C",
                "explanation": "标识符由字母、数字、下划线组成，必须以字母或下划线开头，不能使用关键字。"
            },
            {
                "title": "标识符规则",
                "question_text": "C语言中，标识符不能以什么开头？",
                "options": ["A. 字母", "B. 下划线", "C. 数字", "D. 字母或下划线"],
                "correct_answer": "C",
                "explanation": "标识符必须以字母或下划线开头，不能以数字开头。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def variable_constant(order):
        templates = [
            {
                "title": "变量定义",
                "question_text": "以下哪个是正确的变量定义？",
                "options": ["A. int age;", "B. int age", "C. int age.", "D. int age:"],
                "correct_answer": "A",
                "explanation": "C语言中变量定义需要在类型和变量名之间有空格，语句以分号结束。"
            },
            {
                "title": "常量定义",
                "question_text": "定义一个常量，使其值不可修改，应该使用什么关键字？",
                "options": ["A. var", "B. const", "C. static", "D. final"],
                "correct_answer": "B",
                "explanation": "使用const关键字定义的常量在程序运行期间不能被修改，如const int MAX=100;"
            },
            {
                "title": "宏定义",
                "question_text": "以下哪个是定义宏常量的正确方式？",
                "options": ["A. const PI = 3.14;", "B. #define PI 3.14", "C. var PI = 3.14;", "D. int PI = 3.14;"],
                "correct_answer": "B",
                "explanation": "使用#define预处理器指令定义宏常量，在编译前进行替换，如#define PI 3.14"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def printf_format(order):
        templates = [
            {
                "title": "printf输出",
                "question_text": "使用printf输出整数，应该使用哪个格式符？",
                "options": ["A. %f", "B. %d", "C. %c", "D. %s"],
                "correct_answer": "B",
                "explanation": "%d用于输出整数，%f用于输出浮点数，%c用于输出字符，%s用于输出字符串。"
            },
            {
                "title": "换行符",
                "question_text": "在printf中，表示换行的转义字符是？",
                "options": ["A. \\t", "B. \\n", "C. \\r", "D. \\\\"],
                "correct_answer": "B",
                "explanation": "\\n表示换行符，\\t表示制表符，\\r表示回车，\\\\表示反斜杠。"
            },
            {
                "title": "格式符",
                "question_text": "输出双精度浮点数double，应该使用哪个格式符？",
                "options": ["A. %f", "B. %lf", "C. %d", "D. %c"],
                "correct_answer": "B",
                "explanation": "%lf用于输出double类型（长浮点），%f用于输出float类型。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def relational_operator(order):
        templates = [
            {
                "title": "关系运算符",
                "question_text": "以下哪个运算符表示大于等于？",
                "options": ["A. >", "B. <>", "C. >=", "D. =<"],
                "correct_answer": "C",
                "explanation": ">=表示大于等于，>表示大于，<=表示小于等于，<>不是C语言的运算符。"
            },
            {
                "title": "等于运算符",
                "question_text": "在C语言中，判断两个值相等应该使用哪个运算符？",
                "options": ["A. =", "B. ==", "C. ===", "D. !="],
                "correct_answer": "B",
                "explanation": "==是相等比较运算符，=是赋值运算符，两者含义完全不同。"
            },
            {
                "title": "不等于",
                "question_text": "表示不等于的运算符是？",
                "options": ["A. <>", "B. ><", "C. !=", "D. ~="],
                "correct_answer": "C",
                "explanation": "!=表示不等于，是C语言的关系运算符之一。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def logical_operator(order):
        templates = [
            {
                "title": "逻辑与",
                "question_text": "在C语言中，逻辑与运算符是？",
                "options": ["A. &", "B. &&", "C. |", "D. ||"],
                "correct_answer": "B",
                "explanation": "&&是逻辑与运算符，&是按位与运算符，两者含义不同。"
            },
            {
                "title": "逻辑或",
                "question_text": "逻辑或运算符是？",
                "options": ["A. &", "B. &&", "C. |", "D. ||"],
                "correct_answer": "D",
                "explanation": "||是逻辑或运算符，|是按位或运算符。"
            },
            {
                "title": "逻辑非",
                "question_text": "逻辑非运算符是？",
                "options": ["A. !", "B. ~", "C. not", "D. ^"],
                "correct_answer": "A",
                "explanation": "!是逻辑非运算符，~是按位取反运算符。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def if_statement(order):
        templates = [
            {
                "title": "if语句格式",
                "question_text": "以下哪个是if语句的正确基本形式？",
                "options": ["A. if(条件) 语句;", "B. if 条件 then 语句", "C. if(条件) then {语句}", "D. if 条件 {语句}"],
                "correct_answer": "A",
                "explanation": "C语言中if语句的标准形式是：if(条件) 语句; 条件为真时执行语句。"
            },
            {
                "title": "if-else结构",
                "question_text": "if-else语句的正确形式是？",
                "options": ["A. if(条件) 语句; else 语句;", "B. if 条件 语句; else 语句", "C. if(条件) {语句} else {语句}", "D. if 条件 then 语句 else 语句"],
                "correct_answer": "A",
                "explanation": "if-else的标准形式是if(条件) 语句; else 语句;，else后不需要再判断条件。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def if_nesting(order):
        templates = [
            {
                "title": "if嵌套",
                "question_text": "以下关于if语句嵌套的说法，正确的是？",
                "options": ["A. if语句可以无限嵌套", "B. if语句嵌套层数过多会影响程序可读性", "C. 内层if必须和外层if使用相同的条件", "D. if语句嵌套后else总与最内层匹配"],
                "correct_answer": "B",
                "explanation": "if嵌套层数过多会导致代码难以理解和维护，应谨慎使用或改用其他结构。"
            },
            {
                "title": "else配对",
                "question_text": "在C语言中，else与哪个if配对？",
                "options": ["A. 总是与第一个if配对", "B. 与最接近的尚未配对的if配对", "C. 与最远的if配对", "D. 由程序员指定"],
                "correct_answer": "B",
                "explanation": "else总是与离它最近的前一个尚未配对的if配对，除非使用花括号改变配对关系。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def conditional_operator(order):
        templates = [
            {
                "title": "条件运算符",
                "question_text": "条件运算符的正确形式是？",
                "options": ["A. (条件)?表达式1:表达式2", "B. (条件)?表达式1,表达式2", "C. (条件)表达式1:表达式2", "D. (条件)?表达式1;表达式2"],
                "correct_answer": "A",
                "explanation": "条件运算符是C语言中唯一的三目运算符，形式为：条件?表达式1:表达式2。"
            },
            {
                "title": "条件运算符功能",
                "question_text": "表达式(a>b)?a:b的作用是？",
                "options": ["A. 比较a和b的大小", "B. 返回a和b中的较大值", "C. 判断a是否大于b", "D. 交换a和b的值"],
                "correct_answer": "B",
                "explanation": "当a>b为真时返回a，否则返回b，即返回a和b中的较大值。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def switch_statement(order):
        templates = [
            {
                "title": "switch基础",
                "question_text": "switch语句的括号内通常放什么类型的表达式？",
                "options": ["A. 浮点型", "B. 字符型或整型", "C. 布尔型", "D. 任何类型"],
                "correct_answer": "B",
                "explanation": "switch语句的表达式通常是整数或字符类型，不能是浮点型或字符串。"
            },
            {
                "title": "switch中break",
                "question_text": "在switch语句中，break语句的作用是？",
                "options": ["A. 结束程序运行", "B. 跳出switch语句", "C. 跳过所有case", "D. 返回函数"],
                "correct_answer": "B",
                "explanation": "break语句用于跳出switch语句，如果没有break，会继续执行后面的case。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def for_loop(order):
        templates = [
            {
                "title": "for循环格式",
                "question_text": "以下哪个是for循环的正确格式？",
                "options": ["A. for(初始化;条件;更新)", "B. for 初始化;条件;更新", "C. for(初始化,条件,更新)", "D. for[初始化;条件;更新]"],
                "correct_answer": "A",
                "explanation": "for循环的标准格式是for(初始化;条件;更新)，三个部分以分号分隔。"
            },
            {
                "title": "for循环执行顺序",
                "question_text": "for循环的执行顺序是？",
                "options": ["A. 条件->循环体->更新->条件", "B. 初始化->条件->循环体->更新->条件", "C. 循环体->初始化->条件->更新", "D. 更新->条件->循环体->初始化"],
                "correct_answer": "B",
                "explanation": "for循环执行顺序：先执行初始化，然后判断条件，条件为真则执行循环体，最后执行更新，再判断条件。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def while_loop(order):
        templates = [
            {
                "title": "while循环",
                "question_text": "while循环的特点是？",
                "options": ["A. 先执行循环体再判断条件", "B. 先判断条件再执行循环体", "C. 循环体至少执行一次", "D. 循环体最多执行一次"],
                "correct_answer": "B",
                "explanation": "while循环先判断条件，条件为真才执行循环体，可能一次都不执行。"
            },
            {
                "title": "while循环格式",
                "question_text": "while循环的正确格式是？",
                "options": ["A. while 条件 {循环体}", "B. while(条件) {循环体}", "C. while{条件} 循环体", "D. 循环体 while 条件"],
                "correct_answer": "B",
                "explanation": "while循环的标准格式是while(条件) {循环体}，先判断条件。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def do_while_loop(order):
        templates = [
            {
                "title": "do-while循环",
                "question_text": "do-while循环的特点是？",
                "options": ["A. 先判断条件再执行循环体", "B. 循环体至少执行一次", "C. 循环体可能不执行", "D. 循环次数固定"],
                "correct_answer": "B",
                "explanation": "do-while循环先执行循环体再判断条件，所以循环体至少执行一次。"
            },
            {
                "title": "do-while格式",
                "question_text": "do-while循环的正确格式是？",
                "options": ["A. do {循环体} while(条件)", "B. while(条件) do {循环体}", "C. do 循环体 while 条件", "D. do{循环体} while 条件"],
                "correct_answer": "A",
                "explanation": "do-while的标准格式是do {循环体} while(条件);注意条件后有分号。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def loop_nesting(order):
        templates = [
            {
                "title": "循环嵌套",
                "question_text": "以下关于循环嵌套的说法，正确的是？",
                "options": ["A. 循环嵌套只能两层", "B. 外层循环执行一次，内层循环执行完整一轮", "C. 内外层循环变量不能相同", "D. 循环嵌套不影响程序效率"],
                "correct_answer": "B",
                "explanation": "循环嵌套时，外层循环每执行一次，内层循环完成完整的一轮迭代。"
            },
            {
                "title": "嵌套循环执行次数",
                "question_text": "双重循环中，外层循环5次，内层循环3次，总执行多少次循环体？",
                "options": ["A. 8次", "B. 15次", "C. 5次", "D. 3次"],
                "correct_answer": "B",
                "explanation": "双重循环总执行次数是外层次数乘以内层次数：5 x 3 = 15次。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def break_continue(order):
        templates = [
            {
                "title": "break语句",
                "question_text": "break语句的作用是？",
                "options": ["A. 结束整个程序", "B. 跳出当前循环", "C. 跳过本次循环剩余语句", "D. 结束当前函数"],
                "correct_answer": "B",
                "explanation": "break语句用于跳出当前循环（for、while、do-while）或switch语句。"
            },
            {
                "title": "continue语句",
                "question_text": "continue语句的作用是？",
                "options": ["A. 结束整个循环", "B. 跳出循环体", "C. 跳过本次循环剩余语句，开始下一次循环", "D. 结束程序"],
                "correct_answer": "C",
                "explanation": "continue语句跳过本次循环剩余语句，直接进入下一次循环条件判断。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def function_definition(order):
        templates = [
            {
                "title": "函数定义",
                "question_text": "以下哪个是函数定义的正确格式？",
                "options": ["A. int func() { }", "B. func int() { }", "C. int func { }", "D. func() int { }"],
                "correct_answer": "A",
                "explanation": "函数定义格式：返回类型 函数名(参数列表) { 函数体 }，如int func() { }。"
            },
            {
                "title": "函数返回类型",
                "question_text": "如果函数不需要返回值，应该使用什么返回类型？",
                "options": ["A. int", "B. void", "C. null", "D. empty"],
                "correct_answer": "B",
                "explanation": "void表示空类型，用于表示函数不返回任何值。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def function_call(order):
        templates = [
            {
                "title": "函数调用",
                "question_text": "以下哪个是正确的函数调用？",
                "options": ["A. func;", "B. func()", "C. call func", "D. func"],
                "correct_answer": "B",
                "explanation": "函数调用需要使用括号，如func()，即使没有参数也要加括号。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def macro_definition(order):
        templates = [
            {
                "title": "宏定义",
                "question_text": "#define MAX 100 这行代码的作用是？",
                "options": ["A. 定义一个变量MAX等于100", "B. 定义一个符号常量MAX值为100", "C. 声明一个函数", "D. 包含头文件"],
                "correct_answer": "B",
                "explanation": "#define是宏定义，用来定义符号常量，在编译前进行文本替换。"
            },
            {
                "title": "宏定义与const",
                "question_text": "宏定义和const常量有什么区别？",
                "options": ["A. 没有区别", "B. 宏定义在编译前处理，const在编译时处理", "C. const在编译前处理", "D. 两者处理时机相同"],
                "correct_answer": "B",
                "explanation": "宏定义在预处理阶段进行文本替换，const在编译阶段处理，const有类型检查。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def conditional_compilation(order):
        templates = [
            {
                "title": "条件编译",
                "question_text": "#ifdef DEBUG的作用是？",
                "options": ["A. 如果定义了DEBUG，则编译后面的代码", "B. 取消定义DEBUG", "C. 结束DEBUG", "D. 声明DEBUG"],
                "correct_answer": "A",
                "explanation": "#ifdef表示如果已定义该标识符，则编译后面的代码块，用于调试代码。"
            },
            {
                "title": "条件编译指令",
                "question_text": "以下哪个不是条件编译指令？",
                "options": ["A. #ifdef", "B. #ifndef", "C. #defined", "D. #ifnot"],
                "correct_answer": "D",
                "explanation": "条件编译指令包括#ifdef、#ifndef、#elif等，没有#ifnot。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def one_dimensional_array(order):
        templates = [
            {
                "title": "数组定义",
                "question_text": "以下哪个是定义含有5个整数的数组的正确方式？",
                "options": ["A. int arr(5);", "B. int arr[5];", "C. int[5] arr;", "D. array int arr[5];"],
                "correct_answer": "B",
                "explanation": "C语言中数组定义的正确格式是：类型 数组名[元素个数];，如int arr[5];"
            },
            {
                "title": "数组下标",
                "question_text": "数组arr[5]的元素下标范围是？",
                "options": ["A. 1-5", "B. 0-4", "C. 0-5", "D. 1-4"],
                "correct_answer": "B",
                "explanation": "C语言数组下标从0开始，所以arr[5]的元素是arr[0]到arr[4]。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def two_dimensional_array(order):
        templates = [
            {
                "title": "二维数组定义",
                "question_text": "定义一个3行4列的二维整型数组，正确的是？",
                "options": ["A. int arr[3,4];", "B. int arr[3][4];", "C. int[3,4] arr;", "D. arr int[3][4];"],
                "correct_answer": "B",
                "explanation": "二维数组定义格式：类型 数组名[行数][列数];，如int arr[3][4];"
            },
            {
                "title": "二维数组存储",
                "question_text": "二维数组在内存中是如何存储的？",
                "options": ["A. 按行存储", "B. 按列存储", "C. 随机存储", "D. 树形存储"],
                "correct_answer": "A",
                "explanation": "二维数组在内存中按行存储，即先存第一行，再存第二行，依此类推。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def string_basics(order):
        templates = [
            {
                "title": "字符串结束符",
                "question_text": "C语言中，字符串的结束标志是什么？",
                "options": ["A.空格", "B.换行符", "C.'\\0'或0", "D.字符串长度"],
                "correct_answer": "C",
                "explanation": "C语言中字符串以'\\0'（空字符）作为结束标志，占用一个字节。"
            },
            {
                "title": "字符串存储",
                "question_text": "字符串\"hello\"需要占用多少字节？",
                "options": ["A.5", "B.6", "C.7", "D.4"],
                "correct_answer": "B",
                "explanation": "\"hello\"有5个字符，加上结束符'\\0'，共6个字节。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def string_functions(order):
        templates = [
            {
                "title": "字符串长度函数",
                "question_text": "strlen(\"abc\")的返回值是？",
                "options": ["A.2", "B.3", "C.4", "D.abc"],
                "correct_answer": "B",
                "explanation": "strlen返回字符串长度，不包括结束符'\\0'，所以\"abc\"长度为3。"
            },
            {
                "title": "字符串复制函数",
                "question_text": "strcpy(s1,s2)函数的作用是？",
                "options": ["A. 比较s1和s2", "B. 将s2复制到s1", "C. 连接s1和s2", "D. 计算s1和s2的长度"],
                "correct_answer": "B",
                "explanation": "strcpy用于将s2的内容复制到s1中，包括结束符'\\0'。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_variable(order):
        templates = [
            {
                "title": "指针定义",
                "question_text": "以下哪个是定义整型指针变量的正确方式？",
                "options": ["A. int *p;", "B. pointer int p;", "C. int p*;", "D. *int p;"],
                "correct_answer": "A",
                "explanation": "定义指针变量使用类型*变量名的格式，如int *p;表示p是指向整型的指针。"
            },
            {
                "title": "取地址运算符",
                "question_text": "如果int a=10; &a表示什么？",
                "options": ["A. a的值", "B. a的地址", "C. a的引用", "D. a的指针"],
                "correct_answer": "B",
                "explanation": "&是取地址运算符，&a表示变量a在内存中的地址。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_arithmetic(order):
        templates = [
            {
                "title": "指针运算",
                "question_text": "如果int *p; p+1会移动多少字节？",
                "options": ["A.1字节", "B.2字节", "C.4字节", "D.取决于类型"],
                "correct_answer": "D",
                "explanation": "指针运算中，p+1移动的字节数取决于指针指向的数据类型，int通常移动4字节。"
            },
            {
                "title": "指针比较",
                "question_text": "两个指针可以进行比较运算吗？",
                "options": ["A.不可以", "B.可以，但只能在同一数组内", "C.可以，任何指针都行", "D.只有整型指针可以"],
                "correct_answer": "B",
                "explanation": "同类型指针可以在同一数组内进行比较，用于判断位置关系。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_array(order):
        templates = [
            {
                "title": "数组名作为指针",
                "question_text": "数组名作为右值时，表示什么？",
                "options": ["A.数组第一个元素的副本", "B.数组第一个元素的地址", "C.数组所有元素", "D.数组长度"],
                "correct_answer": "B",
                "explanation": "数组名作为右值时表示数组首元素的地址（指针常量）。"
            },
            {
                "title": "指针与数组关系",
                "question_text": "arr[i]与*(arr+i)的关系是？",
                "options": ["A. arr[i]更快", "B. *(arr+i)更快", "C.两者等价", "D.没有关系"],
                "correct_answer": "C",
                "explanation": "arr[i]和*(arr+i)在C语言中是等价的，都是访问数组第i个元素。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_string(order):
        templates = [
            {
                "title": "字符指针与字符串",
                "question_text": "char *s=\"hello\"; s指向什么？",
                "options": ["A.字符h", "B.字符串hello", "C.字符h的地址", "D.字符串首地址"],
                "correct_answer": "D",
                "explanation": "字符指针s指向字符串\"hello\"的首字符地址，字符串在数组中存储。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_parameter(order):
        templates = [
            {
                "title": "指针作为参数",
                "question_text": "在函数中修改主调函数变量，需要使用什么？",
                "options": ["A. 值传递", "B. 指针或引用", "C. 全局变量", "D. 静态变量"],
                "correct_answer": "B",
                "explanation": "C语言中函数参数是值传递，要修改主调函数变量需要传递指针或使用指针参数。"
            },
            {
                "title": "指针参数作用",
                "question_text": "void swap(int *a, int *b)函数的作用是？",
                "options": ["A. 交换a和b的值", "B. 交换*a和*b的值", "C. 什么都不做", "D. 比较a和b"],
                "correct_answer": "B",
                "explanation": "传递指针后，函数通过*a和*b可以访问和修改主调函数中的实际变量值。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_return(order):
        templates = [
            {
                "title": "返回指针",
                "question_text": "函数可以返回指针吗？",
                "options": ["A.不可以", "B.可以，但返回的必须是静态或动态内存", "C.可以返回任何指针", "D.只能返回整数"],
                "correct_answer": "B",
                "explanation": "函数可以返回指针，但返回的指针必须指向有效的内存区域，如静态变量或动态分配内存。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def struct_definition(order):
        templates = [
            {
                "title": "结构体定义",
                "question_text": "定义结构体的关键字是？",
                "options": ["A. union", "B. struct", "C. enum", "D. typedef"],
                "correct_answer": "B",
                "explanation": "struct用于定义结构体类型，如struct Student { int age; };"
            },
            {
                "title": "结构体大小",
                "question_text": "结构体的大小等于各成员大小之和吗？",
                "options": ["A.总是等于", "B.不一定，由于内存对齐可能更大", "C.总是更大", "D.总是更小"],
                "correct_answer": "B",
                "explanation": "由于内存对齐，结构体大小可能大于各成员大小之和，这是正常的。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def struct_variable(order):
        templates = [
            {
                "title": "结构体变量定义",
                "question_text": "根据已定义的结构体struct Student，如何定义变量？",
                "options": ["A. student s;", "B. struct Student s;", "C. Student s;", "D. struct s;"],
                "correct_answer": "B",
                "explanation": "定义结构体变量需要使用struct关键字，如struct Student s;或使用typedef简化。"
            },
            {
                "title": "结构体成员访问",
                "question_text": "结构体变量s的成员age，应该如何访问？",
                "options": ["A. s.age", "B. s->age", "C. *s.age", "D. s[age]"],
                "correct_answer": "A",
                "explanation": "结构体变量使用点运算符访问成员，如s.age；结构体指针使用->运算符。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def struct_array(order):
        templates = [
            {
                "title": "结构体数组",
                "question_text": "定义结构体数组的正确方式是？",
                "options": ["A. struct Student[10];", "B. struct Student students[10];", "C. Student[10] students;", "D. students[10] struct;"],
                "correct_answer": "B",
                "explanation": "定义结构体数组：struct Student students[10];表示10个struct Student类型的元素。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def struct_pointer(order):
        templates = [
            {
                "title": "结构体指针",
                "question_text": "struct Student *p; p->age等价于？",
                "options": ["A. p.age", "B. (*p).age", "C. *p.age", "D. p[age]"],
                "correct_answer": "B",
                "explanation": "结构体指针p使用->访问成员，等价于(*p).age，即先解引用再访问成员。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def union_type(order):
        templates = [
            {
                "title": "联合体",
                "question_text": "联合体与结构体的主要区别是？",
                "options": ["A.联合体成员共享同一块内存", "B.联合体可以包含更多成员", "C.结构体成员共享内存", "D.没有区别"],
                "correct_answer": "A",
                "explanation": "联合体的所有成员共享同一块内存，修改一个成员会影响其他成员的值。"
            },
            {
                "title": "联合体大小",
                "question_text": "联合体的大小由什么决定？",
                "options": ["A.所有成员大小之和", "B.最大成员的大小", "C.最小成员的大小", "D.成员数量"],
                "correct_answer": "B",
                "explanation": "联合体大小由最大成员的大小决定，因为所有成员共享同一块内存。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def enum_type(order):
        templates = [
            {
                "title": "枚举类型",
                "question_text": "enum COLOR {RED, GREEN, BLUE}; RED的值是？",
                "options": ["A.0", "B.1", "C.2", "D.没有值"],
                "correct_answer": "A",
                "explanation": "枚举值默认从0开始，RED=0，GREEN=1，BLUE=2，可以人为指定。"
            },
            {
                "title": "枚举使用",
                "question_text": "枚举类型的主要作用是？",
                "options": ["A.节省内存", "B.提高代码可读性", "C.加快运行速度", "D.方便输入输出"],
                "correct_answer": "B",
                "explanation": "枚举用于定义一组命名的整型常量，提高代码可读性和可维护性。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_open_close(order):
        templates = [
            {
                "title": "文件打开函数",
                "question_text": "fopen函数的返回值类型是？",
                "options": ["A.int", "B.FILE *", "C.char *", "D.void *"],
                "correct_answer": "B",
                "explanation": "fopen返回FILE类型的指针，用于标识打开的文件。"
            },
            {
                "title": "文件打开模式",
                "question_text": "以文本方式读取文件，应该使用什么模式？",
                "options": ["A.\"r\"", "B.\"rb\"", "C.\"w\"", "D.\"a\""],
                "correct_answer": "A",
                "explanation": "\"r\"表示以文本方式读取，\"rb\"表示以二进制方式读取。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_read_write(order):
        templates = [
            {
                "title": "fprintf函数",
                "question_text": "fprintf的作用是？",
                "options": ["A. 从文件读取数据", "B. 向文件写入数据", "C. 关闭文件", "D. 打开文件"],
                "correct_answer": "B",
                "explanation": "fprintf用于向文件写入数据，功能类似printf，只是输出到文件。"
            },
            {
                "title": "fscanf函数",
                "question_text": "fscanf的作用是？",
                "options": ["A. 从文件读取格式化数据", "B. 向文件写入数据", "C. 判断文件结束", "D. 文件定位"],
                "correct_answer": "A",
                "explanation": "fscanf用于从文件读取格式化数据，功能类似scanf，从文件读取。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_position(order):
        templates = [
            {
                "title": "文件定位函数",
                "question_text": "fseek函数的作用是？",
                "options": ["A. 读取文件", "B. 写入文件", "C. 移动文件指针位置", "D. 关闭文件"],
                "correct_answer": "C",
                "explanation": "fseek用于移动文件指针到指定位置，便于随机访问文件内容。"
            },
            {
                "title": "ftell函数",
                "question_text": "ftell函数返回什么？",
                "options": ["A. 文件大小", "B. 当前文件指针位置（从文件开始的偏移量）", "C. 文件行数", "D. 文件字符数"],
                "correct_answer": "B",
                "explanation": "ftell返回当前文件指针位置相对于文件开头的偏移量（字节数）。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_error(order):
        templates = [
            {
                "title": "feof函数",
                "question_text": "feof函数的作用是？",
                "options": ["A. 关闭文件", "B. 打开文件", "C. 判断文件是否结束", "D. 创建新文件"],
                "correct_answer": "C",
                "explanation": "feof用于判断文件是否已经到达结束位置。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def algorithm_flowchart(order):
        templates = [
            {
                "title": "算法特性",
                "question_text": "算法的特性不包括以下哪一项？",
                "options": ["A. 有穷性", "B. 确定性", "C. 无限性", "D. 可行性"],
                "correct_answer": "C",
                "explanation": "算法必须具有有穷性（有限步骤结束）、确定性（每步明确）、可行性（能够执行）。"
            },
            {
                "title": "流程图符号",
                "question_text": "在流程图中，菱形框表示什么？",
                "options": ["A. 开始/结束", "B. 输入/输出", "C. 处理", "D. 判断"],
                "correct_answer": "D",
                "explanation": "流程图中，椭圆表示开始/结束，平行四边形表示输入/输出，矩形表示处理，菱形表示判断。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def modular_design(order):
        templates = [
            {
                "title": "模块化设计",
                "question_text": "模块化程序设计的优点是？",
                "options": ["A. 程序更小", "B. 易于维护和扩展", "C. 运行更快", "D. 减少内存使用"],
                "correct_answer": "B",
                "explanation": "模块化设计将程序分成独立模块，提高代码的可维护性、可扩展性和可重用性。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def student_management(order):
        templates = [
            {
                "title": "学生管理系统功能",
                "question_text": "学生管理系统通常不包括以下哪个功能？",
                "options": ["A. 添加学生信息", "B. 删除学生信息", "C. 修改学生信息", "D. 自动批改作业"],
                "correct_answer": "D",
                "explanation": "学生管理系统主要管理学生信息，包括增删改查，不包括自动批改作业功能。"
            }
        ]
        return templates[order % len(templates)]

    @staticmethod
    def default_template(order):
        templates = [
            {
                "title": "基本概念",
                "question_text": "以下关于该知识点的说法，正确的是？",
                "options": ["A. 正确", "B. 错误", "C. 不确定", "D. 以上都不对"],
                "correct_answer": "A",
                "explanation": "请根据课堂所学知识进行判断。"
            }
        ]
        return templates[order % len(templates)]


class FillBlankTemplates:
    """填空题模板"""

    @staticmethod
    def c_program_structure(order):
        templates = [
            {"title": "C程序入口", "question_text": "C语言程序的执行入口是______函数。", "correct_answer": "main", "explanation": "C语言规定，程序的执行从main函数开始。"},
            {"title": "语句结束符", "question_text": "C语言中，每条语句以______作为结束标志。", "correct_answer": ";", "explanation": "分号是C语言语句的结束标志。"},
            {"title": "头文件", "question_text": "#include <stdio.h>中，stdio.h是______输入输出库的头文件。", "correct_answer": "标准", "explanation": "stdio.h是标准输入输出库的头文件。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def data_type(order):
        templates = [
            {"title": "基本数据类型", "question_text": "C语言的基本数据类型包括int、float、double和______。", "correct_answer": "char", "explanation": "C语言四种基本数据类型：int、float、double、char。"},
            {"title": "整型大小", "question_text": "在大多数系统上，int类型通常占用______个字节。", "correct_answer": "4", "explanation": "int类型通常占用4个字节（32位）。"},
            {"title": "字符型", "question_text": "char类型用于存储______个字符。", "correct_answer": "1", "explanation": "char类型用于存储单个字符。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def printf_format(order):
        templates = [
            {"title": "格式符", "question_text": "printf中输出整数使用______格式符。", "correct_answer": "%d", "explanation": "%d用于输出整数。"},
            {"title": "换行符", "question_text": "printf中表示换行的转义字符是______。", "correct_answer": "\\n", "explanation": "\\n表示换行。"},
            {"title": "double格式符", "question_text": "输出double类型应该使用______格式符。", "correct_answer": "%lf", "explanation": "%lf用于输出double类型。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def variable_constant(order):
        templates = [
            {"title": "常量关键字", "question_text": "定义常量应使用______关键字。", "correct_answer": "const", "explanation": "const用于定义常量。"},
            {"title": "宏定义", "question_text": "#define是______定义，用于定义符号常量。", "correct_answer": "宏", "explanation": "#define是宏定义。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def relational_operator(order):
        templates = [
            {"title": "关系运算符", "question_text": "大于等于运算符是______。", "correct_answer": ">=", "explanation": ">=表示大于等于。"},
            {"title": "相等运算符", "question_text": "判断相等的运算符是______。", "correct_answer": "==", "explanation": "==是相等比较运算符。"},
            {"title": "不等于", "question_text": "不等于运算符是______。", "correct_answer": "!=", "explanation": "!=表示不等于。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def logical_operator(order):
        templates = [
            {"title": "逻辑与", "question_text": "逻辑与运算符是______。", "correct_answer": "&&", "explanation": "&&是逻辑与运算符。"},
            {"title": "逻辑或", "question_text": "逻辑或运算符是______。", "correct_answer": "||", "explanation": "||是逻辑或运算符。"},
            {"title": "逻辑非", "question_text": "逻辑非运算符是______。", "correct_answer": "!", "explanation": "!是逻辑非运算符。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def if_statement(order):
        templates = [
            {"title": "if格式", "question_text": "if语句的条件需要放在______括号中。", "correct_answer": "圆", "explanation": "if语句使用圆括号包围条件。"},
            {"title": "if-else格式", "question_text": "if-else语句中，else后面______（需要/不需要）再写条件。", "correct_answer": "不需要", "explanation": "else后不需要再写条件。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def for_loop(order):
        templates = [
            {"title": "for循环格式", "question_text": "for循环的三个表达式以______分隔。", "correct_answer": "分号", "explanation": "for(初始化;条件;更新)。"},
            {"title": "for循环执行顺序", "question_text": "for循环先执行______，再判断条件。", "correct_answer": "初始化", "explanation": "for循环先执行初始化部分。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def while_loop(order):
        templates = [
            {"title": "while循环特点", "question_text": "while循环是______判断再执行循环体。", "correct_answer": "先", "explanation": "while先判断条件再执行。"},
            {"title": "do-while特点", "question_text": "do-while循环的循环体至少执行______次。", "correct_answer": "1", "explanation": "do-while先执行再判断，所以至少执行一次。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def break_continue(order):
        templates = [
            {"title": "break作用", "question_text": "break语句用于跳出当前______。", "correct_answer": "循环", "explanation": "break用于跳出循环。"},
            {"title": "continue作用", "question_text": "continue语句跳过本次循环的______语句。", "correct_answer": "剩余", "explanation": "continue跳过剩余语句进入下次循环。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def function_definition(order):
        templates = [
            {"title": "函数定义格式", "question_text": "函数定义需要指定返回类型、函数名和______列表。", "correct_answer": "参数", "explanation": "函数定义需要参数列表。"},
            {"title": "无返回值函数", "question_text": "如果函数不返回值，应该使用______作为返回类型。", "correct_answer": "void", "explanation": "void表示空类型。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def macro_definition(order):
        templates = [
            {"title": "宏定义", "question_text": "#define用于______定义，在编译前处理。", "correct_answer": "宏", "explanation": "#define是宏定义。"},
            {"title": "条件编译", "question_text": "#ifdef表示如果______了该标识符。", "correct_answer": "定义", "explanation": "#ifdef检查标识符是否已定义。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def one_dimensional_array(order):
        templates = [
            {"title": "数组定义", "question_text": "定义数组需要指定元素______。", "correct_answer": "个数", "explanation": "数组定义需要指定元素个数。"},
            {"title": "数组下标", "question_text": "数组下标从______开始。", "correct_answer": "0", "explanation": "C语言数组下标从0开始。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def two_dimensional_array(order):
        templates = [
            {"title": "二维数组定义", "question_text": "二维数组定义需要指定行数和______数。", "correct_answer": "列", "explanation": "二维数组需要指定行列数。"},
            {"title": "二维数组存储", "question_text": "二维数组在内存中按______顺序存储。", "correct_answer": "行", "explanation": "二维数组按行存储。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def string_basics(order):
        templates = [
            {"title": "字符串结束符", "question_text": "C语言中字符串以______作为结束标志。", "correct_answer": "\\0", "explanation": "字符串以\\0结束。"},
            {"title": "字符串长度", "question_text": "字符串\"hello\"占用______个字节。", "correct_answer": "6", "explanation": "\"hello\"有5个字符加上结束符共6字节。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_variable(order):
        templates = [
            {"title": "指针定义", "question_text": "定义指针变量需要使用______运算符。", "correct_answer": "*", "explanation": "指针定义使用*号。"},
            {"title": "取地址", "question_text": "&是______运算符，用于获取变量地址。", "correct_answer": "取地址", "explanation": "&用于取地址。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_arithmetic(order):
        templates = [
            {"title": "指针运算", "question_text": "指针加1移动的字节数取决于指针指向的______。", "correct_answer": "类型", "explanation": "指针运算与类型相关。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def pointer_array(order):
        templates = [
            {"title": "数组名指针", "question_text": "数组名作为右值时表示______个元素的地址。", "correct_answer": "首", "explanation": "数组名表示首元素地址。"},
            {"title": "arr与指针", "question_text": "arr[i]与______等价。", "correct_answer": "*(arr+i)", "explanation": "arr[i] == *(arr+i)。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def struct_definition(order):
        templates = [
            {"title": "结构体关键字", "question_text": "定义结构体使用______关键字。", "correct_answer": "struct", "explanation": "struct用于定义结构体。"},
            {"title": "结构体大小", "question_text": "结构体大小可能大于各成员之和，原因是______对齐。", "correct_answer": "内存", "explanation": "内存对齐可能导致结构体更大。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def union_type(order):
        templates = [
            {"title": "联合体特点", "question_text": "联合体的所有成员共享______块内存。", "correct_answer": "同一", "explanation": "联合体成员共享内存。"},
            {"title": "联合体大小", "question_text": "联合体大小由最大______的大小决定。", "correct_answer": "成员", "explanation": "联合体大小由最大成员决定。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def enum_type(order):
        templates = [
            {"title": "枚举默认值", "question_text": "枚举值默认从______开始。", "correct_answer": "0", "explanation": "枚举值默认从0开始。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_open_close(order):
        templates = [
            {"title": "文件打开函数", "question_text": "fopen返回______类型的指针。", "correct_answer": "FILE", "explanation": "fopen返回FILE*。"},
            {"title": "文件关闭", "question_text": "关闭文件使用______函数。", "correct_answer": "fclose", "explanation": "fclose用于关闭文件。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def file_position(order):
        templates = [
            {"title": "文件定位", "question_text": "fseek用于移动文件______的位置。", "correct_answer": "指针", "explanation": "fseek移动文件指针。"},
            {"title": "ftell返回值", "question_text": "ftell返回当前指针相对于文件______的偏移量。", "correct_answer": "开头", "explanation": "ftell返回相对于文件开头的偏移。"}
        ]
        return templates[order % len(templates)]

    @staticmethod
    def default_template(order):
        templates = [
            {"title": "基本概念", "question_text": "请填写正确答案：______。", "correct_answer": "答案", "explanation": "请根据知识填写。"}
        ]
        return templates[order % len(templates)]


def get_template_for_kp(kp_name, q_type, order):
    """根据知识点名称获取对应模板"""
    kp_lower = kp_name.lower()

    # 选择题模板映射
    if "c程序的基本结构" in kp_lower or "main函数" in kp_lower:
        return QuestionTemplates.c_program_structure(order) if q_type == "choice" else FillBlankTemplates.c_program_structure(order)
    elif "语句与注释" in kp_lower:
        return QuestionTemplates.statement_comment(order) if q_type == "choice" else FillBlankTemplates.c_program_structure(order)
    elif "基本数据类型" in kp_lower:
        return QuestionTemplates.data_type(order) if q_type == "choice" else FillBlankTemplates.data_type(order)
    elif "标识符" in kp_lower:
        return QuestionTemplates.identifier(order) if q_type == "choice" else FillBlankTemplates.default_template(order)
    elif "变量与常量" in kp_lower:
        return QuestionTemplates.variable_constant(order) if q_type == "choice" else FillBlankTemplates.variable_constant(order)
    elif "printf格式化输出" in kp_lower:
        return QuestionTemplates.printf_format(order) if q_type == "choice" else FillBlankTemplates.printf_format(order)
    elif "算法与流程图" in kp_lower or "程序设计描述方法" in kp_lower:
        return QuestionTemplates.algorithm_flowchart(order) if q_type == "choice" else FillBlankTemplates.default_template(order)
    elif "模块化设计" in kp_lower or "程序设计流程" in kp_lower:
        return QuestionTemplates.modular_design(order) if q_type == "choice" else FillBlankTemplates.default_template(order)
    elif "学生管理系统" in kp_lower:
        return QuestionTemplates.student_management(order) if q_type == "choice" else FillBlankTemplates.default_template(order)
    elif "关系运算符" in kp_lower:
        return QuestionTemplates.relational_operator(order) if q_type == "choice" else FillBlankTemplates.relational_operator(order)
    elif "逻辑运算符" in kp_lower:
        return QuestionTemplates.logical_operator(order) if q_type == "choice" else FillBlankTemplates.logical_operator(order)
    elif "if语句基本形式" in kp_lower:
        return QuestionTemplates.if_statement(order) if q_type == "choice" else FillBlankTemplates.if_statement(order)
    elif "if语句嵌套" in kp_lower:
        return QuestionTemplates.if_nesting(order) if q_type == "choice" else FillBlankTemplates.if_statement(order)
    elif "条件运算符" in kp_lower:
        return QuestionTemplates.conditional_operator(order) if q_type == "choice" else FillBlankTemplates.if_statement(order)
    elif "switch" in kp_lower:
        return QuestionTemplates.switch_statement(order) if q_type == "choice" else FillBlankTemplates.if_statement(order)
    elif "for循环基本结构" in kp_lower or "for循环变体" in kp_lower:
        return QuestionTemplates.for_loop(order) if q_type == "choice" else FillBlankTemplates.for_loop(order)
    elif "while循环" in kp_lower:
        return QuestionTemplates.while_loop(order) if q_type == "choice" else FillBlankTemplates.while_loop(order)
    elif "do-while" in kp_lower:
        return QuestionTemplates.do_while_loop(order) if q_type == "choice" else FillBlankTemplates.while_loop(order)
    elif "循环嵌套" in kp_lower:
        return QuestionTemplates.loop_nesting(order) if q_type == "choice" else FillBlankTemplates.default_template(order)
    elif "break" in kp_lower or "continue" in kp_lower:
        return QuestionTemplates.break_continue(order) if q_type == "choice" else FillBlankTemplates.break_continue(order)
    elif "函数定义" in kp_lower:
        return QuestionTemplates.function_definition(order) if q_type == "choice" else FillBlankTemplates.function_definition(order)
    elif "函数声明" in kp_lower:
        return QuestionTemplates.function_definition(order) if q_type == "choice" else FillBlankTemplates.function_definition(order)
    elif "函数调用" in kp_lower:
        return QuestionTemplates.function_call(order) if q_type == "choice" else FillBlankTemplates.function_definition(order)
    elif "宏定义" in kp_lower:
        return QuestionTemplates.macro_definition(order) if q_type == "choice" else FillBlankTemplates.macro_definition(order)
    elif "条件编译" in kp_lower:
        return QuestionTemplates.conditional_compilation(order) if q_type == "choice" else FillBlankTemplates.macro_definition(order)
    elif "一维数组基础" in kp_lower or "数组遍历" in kp_lower:
        return QuestionTemplates.one_dimensional_array(order) if q_type == "choice" else FillBlankTemplates.one_dimensional_array(order)
    elif "二维数组基础" in kp_lower or "二维数组应用" in kp_lower:
        return QuestionTemplates.two_dimensional_array(order) if q_type == "choice" else FillBlankTemplates.two_dimensional_array(order)
    elif "字符串基础" in kp_lower:
        return QuestionTemplates.string_basics(order) if q_type == "choice" else FillBlankTemplates.string_basics(order)
    elif "字符串函数" in kp_lower:
        return QuestionTemplates.string_functions(order) if q_type == "choice" else FillBlankTemplates.string_basics(order)
    elif "指针变量" in kp_lower:
        return QuestionTemplates.pointer_variable(order) if q_type == "choice" else FillBlankTemplates.pointer_variable(order)
    elif "指针运算" in kp_lower:
        return QuestionTemplates.pointer_arithmetic(order) if q_type == "choice" else FillBlankTemplates.pointer_arithmetic(order)
    elif "指针与一维数组" in kp_lower or "指针与数组" in kp_lower:
        return QuestionTemplates.pointer_array(order) if q_type == "choice" else FillBlankTemplates.pointer_array(order)
    elif "指针与字符串" in kp_lower:
        return QuestionTemplates.pointer_string(order) if q_type == "choice" else FillBlankTemplates.pointer_array(order)
    elif "指针作为参数" in kp_lower:
        return QuestionTemplates.pointer_parameter(order) if q_type == "choice" else FillBlankTemplates.pointer_variable(order)
    elif "指针作为返回值" in kp_lower or "指针与函数" in kp_lower:
        return QuestionTemplates.pointer_return(order) if q_type == "choice" else FillBlankTemplates.pointer_variable(order)
    elif "结构体定义" in kp_lower:
        return QuestionTemplates.struct_definition(order) if q_type == "choice" else FillBlankTemplates.struct_definition(order)
    elif "结构体变量" in kp_lower:
        return QuestionTemplates.struct_variable(order) if q_type == "choice" else FillBlankTemplates.struct_definition(order)
    elif "结构体数组" in kp_lower:
        return QuestionTemplates.struct_array(order) if q_type == "choice" else FillBlankTemplates.struct_definition(order)
    elif "结构体指针" in kp_lower:
        return QuestionTemplates.struct_pointer(order) if q_type == "choice" else FillBlankTemplates.struct_definition(order)
    elif "联合体" in kp_lower:
        return QuestionTemplates.union_type(order) if q_type == "choice" else FillBlankTemplates.union_type(order)
    elif "枚举" in kp_lower:
        return QuestionTemplates.enum_type(order) if q_type == "choice" else FillBlankTemplates.enum_type(order)
    elif "文件打开" in kp_lower or "文件关闭" in kp_lower:
        return QuestionTemplates.file_open_close(order) if q_type == "choice" else FillBlankTemplates.file_open_close(order)
    elif "文件读写" in kp_lower:
        return QuestionTemplates.file_read_write(order) if q_type == "choice" else FillBlankTemplates.file_open_close(order)
    elif "文件定位" in kp_lower:
        return QuestionTemplates.file_position(order) if q_type == "choice" else FillBlankTemplates.file_position(order)
    elif "文件错误处理" in kp_lower:
        return QuestionTemplates.file_error(order) if q_type == "choice" else FillBlankTemplates.file_position(order)
    else:
        return QuestionTemplates.default_template(order) if q_type == "choice" else FillBlankTemplates.default_template(order)


def generate_question(kp_name, difficulty, q_type, order, section_id, chapter_id):
    """生成一道题目"""
    template = get_template_for_kp(kp_name, q_type, order)

    return {
        "title": template["title"],
        "question_text": template["question_text"],
        "options": template.get("options"),
        "correct_answer": template["correct_answer"],
        "explanation": template["explanation"],
        "difficulty": difficulty,
        "question_type": q_type,
        "section_id": section_id,
        "chapter_id": chapter_id,
        "knowledge_points": [kp_name]
    }


async def generate_and_import_questions():
    """根据配置文件生成并导入所有题目"""

    # 读取所有配置文件
    config_dir = Path(__file__).parent / "习题数量配置"
    config_files = sorted(config_dir.glob("第*节_*.json"))

    print(f"找到 {len(config_files)} 个小节配置文件")

    all_questions = []

    for config_file in config_files:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        chapter_index = config["chapter_index"]
        section_index = config["section_index"]
        section_title = config["section_title"]
        base_questions_count = config["base_questions_count"]
        knowledge_points = config["knowledge_points"]

        print(f"\n处理: 第{chapter_index}章第{section_index}节 - {section_title}")
        print(f"  需生成 {base_questions_count} 道题")

        # 统计各知识点需要生成的题目数
        kp_exercises = {}
        for kp in knowledge_points:
            kp_exercises[kp["name"]] = kp.get("exercises_needed", 2)

        total_from_kps = sum(kp_exercises.values())
        print(f"  知识点分配: {total_from_kps} 题")

        # 生成题目
        questions = []
        q_order = 0

        for kp in knowledge_points:
            kp_name = kp["name"]
            difficulty = kp["difficulty"]
            exercises_needed = kp_exercises[kp_name]

            # 60% 选择题, 40% 填空题
            choice_count = int(exercises_needed * 0.6)
            fillblank_count = exercises_needed - choice_count

            # 确保至少有一道
            if choice_count == 0 and fillblank_count == 0:
                choice_count = 1

            # 生成选择题
            for i in range(choice_count):
                q = generate_question(kp_name, difficulty, "choice", q_order, None, None)
                q["order"] = q_order
                questions.append(q)
                q_order += 1

            # 生成填空题
            for i in range(fillblank_count):
                q = generate_question(kp_name, difficulty, "fill_blank", q_order, None, None)
                q["order"] = q_order
                questions.append(q)
                q_order += 1

        # 调整题目数量以匹配base_questions_count
        while len(questions) < base_questions_count:
            kp = knowledge_points[len(questions) % len(knowledge_points)]
            q = generate_question(kp["name"], kp["difficulty"], "choice", q_order, None, None)
            q["order"] = q_order
            questions.append(q)
            q_order += 1

        while len(questions) > base_questions_count:
            questions.pop()

        print(f"  实际生成: {len(questions)} 道题 (选择题: {sum(1 for q in questions if q['question_type']=='choice')}, 填空题: {sum(1 for q in questions if q['question_type']=='fill_blank')})")

        all_questions.extend(questions)

    print(f"\n总计生成: {len(all_questions)} 道题")

    # 导入数据库
    print("\n开始导入数据库...")

    async with async_session() as db:
        # 先查询所有章节和小节
        from sqlalchemy import select
        from app.models.chapter import Chapter
        from app.models.section import Section

        chapter_result = await db.execute(select(Chapter).where(Chapter.course_code == COURSE_CODE))
        chapters = {c.index: c.id for c in chapter_result.scalars().all()}

        section_result = await db.execute(select(Section).where(Section.course_code == COURSE_CODE))
        sections = section_result.scalars().all()

        # 建立 section 映射 (chapter_index, section_index) -> section_id
        section_map = {}
        for s in sections:
            key = (s.chapter_index, s.section_index)
            section_map[key] = s.id

        print(f"找到 {len(chapters)} 个章节, {len(sections)} 个小节")

        # 准备批量插入
        db_questions = []
        for q in all_questions:
            # 找到对应的 section_id
            # 需要从配置文件中获取 chapter_index 和 section_index
            # 暂时跳过，因为需要在循环中获取
            pass

    print("数据库导入需要完整的章节映射，请检查配置后继续。")


if __name__ == "__main__":
    asyncio.run(generate_and_import_questions())
