"""
根据习题数量配置文件生成题目并导入数据库
严格按照每个小节的base_questions_count和knowledge_points生成
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.section_base_question import SectionBaseQuestion
from app.models.section import Section
from app.models.chapter import Chapter
from app.config import get_settings

COURSE_CODE = "C"  # C语言程序设计


# 题目模板库 - 选择题
CHOICE_TEMPLATES = {
    "c_program_structure": [
        {"title": "C程序入口", "question_text": "C语言程序的执行入口是哪个函数？", "options": ["A. main()", "B. start()", "C. run()", "D. printf()"], "correct_answer": "A", "explanation": "C语言规定，程序的执行从main函数开始，每个C程序必须有且只能有一个main函数作为程序入口。"},
        {"title": "main函数格式", "question_text": "以下哪个是标准的main函数定义？", "options": ["A. void main()", "B. main()", "C. int main()", "D. main(void)"], "correct_answer": "C", "explanation": "标准的main函数应该返回int类型，即int main()，返回值表示程序结束状态。"},
        {"title": "头文件引入", "question_text": "#include <stdio.h>这行代码的作用是什么？", "options": ["A. 定义一个变量", "B. 包含标准输入输出头文件", "C. 声明一个函数", "D. 输出文字"], "correct_answer": "B", "explanation": "#include是预处理指令，stdio.h是标准输入输出库的头文件，用于使用printf、scanf等函数。"},
    ],
    "statement_comment": [
        {"title": "语句结束符", "question_text": "C语言中，每条语句应该以什么符号结尾？", "options": ["A. 冒号 :", "B. 逗号 ,", "C. 分号 ;", "D. 句号 ."], "correct_answer": "C", "explanation": "C语言中，分号(;)是语句的结束符，每条可执行语句都必须以分号结尾。"},
        {"title": "注释的作用", "question_text": "关于C语言注释的说法，正确的是？", "options": ["A. 注释会被编译器执行", "B. 注释对程序运行没有影响", "C. 注释只能写在代码后面", "D. 注释不能多行"], "correct_answer": "B", "explanation": "注释是给程序员看的说明文字，不参与程序编译和执行，对程序运行没有任何影响。"},
        {"title": "多行注释", "question_text": "以下哪个是C语言的多行注释格式？", "options": ["A. // 注释内容", "B. /* 注释内容 */", "C. # 注释内容", "D. <!-- 注释内容 -->"], "correct_answer": "B", "explanation": "C语言使用/*和*/包围多行注释，使用//标记单行注释。"},
    ],
    "data_type": [
        {"title": "基本数据类型", "question_text": "以下哪个不是C语言的基本数据类型？", "options": ["A. int", "B. float", "C. bool", "D. char"], "correct_answer": "C", "explanation": "C语言的基本数据类型包括int、float、double、char，没有bool类型（C99之前）。"},
        {"title": "整型int", "question_text": "在C语言中，int类型通常占用多少字节？", "options": ["A. 1字节", "B. 2字节", "C. 4字节", "D. 8字节"], "correct_answer": "C", "explanation": "在大多数现代系统上，int类型占用4个字节（32位）。"},
        {"title": "字符型", "question_text": "char类型的变量用于存储什么？", "options": ["A. 整数", "B. 单个字符", "C. 小数", "D. 字符串"], "correct_answer": "B", "explanation": "char类型用于存储单个字符，通常占用1个字节，使用单引号包围字符常量。"},
        {"title": "浮点型", "question_text": "用于表示小数（实数）的数据类型是？", "options": ["A. int和char", "B. float和double", "C. bool和void", "D. 只有float"], "correct_answer": "B", "explanation": "C语言中，float和double用于表示浮点数（小数），double是双精度浮点型。"},
    ],
    "identifier": [
        {"title": "合法标识符", "question_text": "以下哪个是合法的C语言标识符？", "options": ["A. 2name", "B. my-age", "C. student_age", "D. int"], "correct_answer": "C", "explanation": "标识符由字母、数字、下划线组成，必须以字母或下划线开头，不能使用关键字。"},
        {"title": "标识符规则", "question_text": "C语言中，标识符不能以什么开头？", "options": ["A. 字母", "B. 下划线", "C. 数字", "D. 字母或下划线"], "correct_answer": "C", "explanation": "标识符必须以字母或下划线开头，不能以数字开头。"},
    ],
    "variable_constant": [
        {"title": "变量定义", "question_text": "以下哪个是正确的变量定义？", "options": ["A. int age;", "B. int age", "C. int age.", "D. int age:"], "correct_answer": "A", "explanation": "C语言中变量定义需要在类型和变量名之间有空格，语句以分号结束。"},
        {"title": "常量定义", "question_text": "定义一个常量，使其值不可修改，应该使用什么关键字？", "options": ["A. var", "B. const", "C. static", "D. final"], "correct_answer": "B", "explanation": "使用const关键字定义的常量在程序运行期间不能被修改。"},
        {"title": "宏定义", "question_text": "以下哪个是定义宏常量的正确方式？", "options": ["A. const PI = 3.14;", "B. #define PI 3.14", "C. var PI = 3.14;", "D. int PI = 3.14;"], "correct_answer": "B", "explanation": "使用#define预处理器指令定义宏常量，在编译前进行替换。"},
    ],
    "printf_format": [
        {"title": "printf输出", "question_text": "使用printf输出整数，应该使用哪个格式符？", "options": ["A. %f", "B. %d", "C. %c", "D. %s"], "correct_answer": "B", "explanation": "%d用于输出整数，%f用于输出浮点数，%c用于输出字符，%s用于输出字符串。"},
        {"title": "换行符", "question_text": "在printf中，表示换行的转义字符是？", "options": ["A. \\t", "B. \\n", "C. \\r", "D. \\\\"], "correct_answer": "B", "explanation": "\\n表示换行符，\\t表示制表符。"},
        {"title": "格式符", "question_text": "输出双精度浮点数double，应该使用哪个格式符？", "options": ["A. %f", "B. %lf", "C. %d", "D. %c"], "correct_answer": "B", "explanation": "%lf用于输出double类型（长浮点），%f用于输出float类型。"},
    ],
    "relational_operator": [
        {"title": "关系运算符", "question_text": "以下哪个运算符表示大于等于？", "options": ["A. >", "B. <>", "C. >=", "D. =<"], "correct_answer": "C", "explanation": ">=表示大于等于，>表示大于，<=表示小于等于。"},
        {"title": "等于运算符", "question_text": "在C语言中，判断两个值相等应该使用哪个运算符？", "options": ["A. =", "B. ==", "C. ===", "D. !="], "correct_answer": "B", "explanation": "==是相等比较运算符，=是赋值运算符，两者含义完全不同。"},
        {"title": "不等于", "question_text": "表示不等于的运算符是？", "options": ["A. <>", "B. ><", "C. !=", "D. ~="], "correct_answer": "C", "explanation": "!=表示不等于，是C语言的关系运算符之一。"},
    ],
    "logical_operator": [
        {"title": "逻辑与", "question_text": "在C语言中，逻辑与运算符是？", "options": ["A. &", "B. &&", "C. |", "D. ||"], "correct_answer": "B", "explanation": "&&是逻辑与运算符，&是按位与运算符。"},
        {"title": "逻辑或", "question_text": "逻辑或运算符是？", "options": ["A. &", "B. &&", "C. |", "D. ||"], "correct_answer": "D", "explanation": "||是逻辑或运算符，|是按位或运算符。"},
        {"title": "逻辑非", "question_text": "逻辑非运算符是？", "options": ["A. !", "B. ~", "C. not", "D. ^"], "correct_answer": "A", "explanation": "!是逻辑非运算符，~是按位取反运算符。"},
    ],
    "if_statement": [
        {"title": "if语句格式", "question_text": "以下哪个是if语句的正确基本形式？", "options": ["A. if(条件) 语句;", "B. if 条件 then 语句", "C. if(条件) then {语句}", "D. if 条件 {语句}"], "correct_answer": "A", "explanation": "C语言中if语句的标准形式是：if(条件) 语句;。"},
        {"title": "if-else结构", "question_text": "if-else语句的正确形式是？", "options": ["A. if(条件) 语句; else 语句;", "B. if 条件 语句; else 语句", "C. if(条件) {语句} else {语句}", "D. if 条件 then 语句 else 语句"], "correct_answer": "A", "explanation": "if-else的标准形式是if(条件) 语句; else 语句;。"},
    ],
    "if_nesting": [
        {"title": "if嵌套", "question_text": "以下关于if语句嵌套的说法，正确的是？", "options": ["A. if语句可以无限嵌套", "B. if语句嵌套层数过多会影响程序可读性", "C. 内层if必须和外层if使用相同的条件", "D. if语句嵌套后else总与最内层匹配"], "correct_answer": "B", "explanation": "if嵌套层数过多会导致代码难以理解和维护。"},
        {"title": "else配对", "question_text": "在C语言中，else与哪个if配对？", "options": ["A. 总是与第一个if配对", "B. 与最接近的尚未配对的if配对", "C. 与最远的if配对", "D. 由程序员指定"], "correct_answer": "B", "explanation": "else总是与离它最近的前一个尚未配对的if配对。"},
    ],
    "conditional_operator": [
        {"title": "条件运算符", "question_text": "条件运算符的正确形式是？", "options": ["A. (条件)?表达式1:表达式2", "B. (条件)?表达式1,表达式2", "C. (条件)表达式1:表达式2", "D. (条件)?表达式1;表达式2"], "correct_answer": "A", "explanation": "条件运算符是C语言中唯一的三目运算符。"},
        {"title": "条件运算符功能", "question_text": "表达式(a>b)?a:b的作用是？", "options": ["A. 比较a和b的大小", "B. 返回a和b中的较大值", "C. 判断a是否大于b", "D. 交换a和b的值"], "correct_answer": "B", "explanation": "当a>b为真时返回a，否则返回b，即返回a和b中的较大值。"},
    ],
    "switch_statement": [
        {"title": "switch基础", "question_text": "switch语句的括号内通常放什么类型的表达式？", "options": ["A. 浮点型", "B. 字符型或整型", "C. 布尔型", "D. 任何类型"], "correct_answer": "B", "explanation": "switch语句的表达式通常是整数或字符类型，不能是浮点型或字符串。"},
        {"title": "switch中break", "question_text": "在switch语句中，break语句的作用是？", "options": ["A. 结束程序运行", "B. 跳出switch语句", "C. 跳过所有case", "D. 返回函数"], "correct_answer": "B", "explanation": "break语句用于跳出switch语句，如果没有break，会继续执行后面的case。"},
    ],
    "for_loop": [
        {"title": "for循环格式", "question_text": "以下哪个是for循环的正确格式？", "options": ["A. for(初始化;条件;更新)", "B. for 初始化;条件;更新", "C. for(初始化,条件,更新)", "D. for[初始化;条件;更新]"], "correct_answer": "A", "explanation": "for循环的标准格式是for(初始化;条件;更新)。"},
        {"title": "for循环执行顺序", "question_text": "for循环的执行顺序是？", "options": ["A. 条件->循环体->更新->条件", "B. 初始化->条件->循环体->更新->条件", "C. 循环体->初始化->条件->更新", "D. 更新->条件->循环体->初始化"], "correct_answer": "B", "explanation": "for循环执行顺序：初始化->条件->循环体->更新->条件。"},
    ],
    "while_loop": [
        {"title": "while循环", "question_text": "while循环的特点是？", "options": ["A. 先执行循环体再判断条件", "B. 先判断条件再执行循环体", "C. 循环体至少执行一次", "D. 循环体最多执行一次"], "correct_answer": "B", "explanation": "while循环先判断条件，条件为真才执行循环体，可能一次都不执行。"},
        {"title": "while循环格式", "question_text": "while循环的正确格式是？", "options": ["A. while 条件 {循环体}", "B. while(条件) {循环体}", "C. while{条件} 循环体", "D. 循环体 while 条件"], "correct_answer": "B", "explanation": "while循环的标准格式是while(条件) {循环体}。"},
    ],
    "do_while_loop": [
        {"title": "do-while循环", "question_text": "do-while循环的特点是？", "options": ["A. 先判断条件再执行循环体", "B. 循环体至少执行一次", "C. 循环体可能不执行", "D. 循环次数固定"], "correct_answer": "B", "explanation": "do-while循环先执行循环体再判断条件，所以循环体至少执行一次。"},
        {"title": "do-while格式", "question_text": "do-while循环的正确格式是？", "options": ["A. do {循环体} while(条件)", "B. while(条件) do {循环体}", "C. do 循环体 while 条件", "D. do{循环体} while 条件"], "correct_answer": "A", "explanation": "do-while的标准格式是do {循环体} while(条件);。"},
    ],
    "loop_nesting": [
        {"title": "循环嵌套", "question_text": "以下关于循环嵌套的说法，正确的是？", "options": ["A. 循环嵌套只能两层", "B. 外层循环执行一次，内层循环执行完整一轮", "C. 内外层循环变量不能相同", "D. 循环嵌套不影响程序效率"], "correct_answer": "B", "explanation": "循环嵌套时，外层循环每执行一次，内层循环完成完整的一轮迭代。"},
        {"title": "嵌套循环执行次数", "question_text": "双重循环中，外层循环5次，内层循环3次，总执行多少次循环体？", "options": ["A. 8次", "B. 15次", "C. 5次", "D. 3次"], "correct_answer": "B", "explanation": "双重循环总执行次数是外层次数乘以内层次数：5 x 3 = 15次。"},
    ],
    "break_continue": [
        {"title": "break语句", "question_text": "break语句的作用是？", "options": ["A. 结束整个程序", "B. 跳出当前循环", "C. 跳过本次循环剩余语句", "D. 结束当前函数"], "correct_answer": "B", "explanation": "break语句用于跳出当前循环。"},
        {"title": "continue语句", "question_text": "continue语句的作用是？", "options": ["A. 结束整个循环", "B. 跳出循环体", "C. 跳过本次循环剩余语句，开始下一次循环", "D. 结束程序"], "correct_answer": "C", "explanation": "continue语句跳过本次循环剩余语句，直接进入下一次循环。"},
    ],
    "function_definition": [
        {"title": "函数定义", "question_text": "以下哪个是函数定义的正确格式？", "options": ["A. int func() { }", "B. func int() { }", "C. int func { }", "D. func() int { }"], "correct_answer": "A", "explanation": "函数定义格式：返回类型 函数名(参数列表) { 函数体 }。"},
        {"title": "函数返回类型", "question_text": "如果函数不需要返回值，应该使用什么返回类型？", "options": ["A. int", "B. void", "C. null", "D. empty"], "correct_answer": "B", "explanation": "void表示空类型，用于表示函数不返回任何值。"},
    ],
    "function_call": [
        {"title": "函数调用", "question_text": "以下哪个是正确的函数调用？", "options": ["A. func;", "B. func()", "C. call func", "D. func"], "correct_answer": "B", "explanation": "函数调用需要使用括号，如func()。"},
    ],
    "macro_definition": [
        {"title": "宏定义", "question_text": "#define MAX 100 这行代码的作用是？", "options": ["A. 定义一个变量MAX等于100", "B. 定义一个符号常量MAX值为100", "C. 声明一个函数", "D. 包含头文件"], "correct_answer": "B", "explanation": "#define是宏定义，用来定义符号常量，在编译前进行文本替换。"},
        {"title": "宏定义与const", "question_text": "宏定义和const常量有什么区别？", "options": ["A. 没有区别", "B. 宏定义在编译前处理，const在编译时处理", "C. const在编译前处理", "D. 两者处理时机相同"], "correct_answer": "B", "explanation": "宏定义在预处理阶段进行文本替换，const在编译阶段处理，const有类型检查。"},
    ],
    "conditional_compilation": [
        {"title": "条件编译", "question_text": "#ifdef DEBUG的作用是？", "options": ["A. 如果定义了DEBUG，则编译后面的代码", "B. 取消定义DEBUG", "C. 结束DEBUG", "D. 声明DEBUG"], "correct_answer": "A", "explanation": "#ifdef表示如果已定义该标识符，则编译后面的代码块。"},
        {"title": "条件编译指令", "question_text": "以下哪个不是条件编译指令？", "options": ["A. #ifdef", "B. #ifndef", "C. #defined", "D. #ifnot"], "correct_answer": "D", "explanation": "条件编译指令包括#ifdef、#ifndef、#elif等，没有#ifnot。"},
    ],
    "one_dimensional_array": [
        {"title": "数组定义", "question_text": "以下哪个是定义含有5个整数的数组的正确方式？", "options": ["A. int arr(5);", "B. int arr[5];", "C. int[5] arr;", "D. array int arr[5];"], "correct_answer": "B", "explanation": "C语言中数组定义的正确格式是：类型 数组名[元素个数];。"},
        {"title": "数组下标", "question_text": "数组arr[5]的元素下标范围是？", "options": ["A. 1-5", "B. 0-4", "C. 0-5", "D. 1-4"], "correct_answer": "B", "explanation": "C语言数组下标从0开始，所以arr[5]的元素是arr[0]到arr[4]。"},
    ],
    "two_dimensional_array": [
        {"title": "二维数组定义", "question_text": "定义一个3行4列的二维整型数组，正确的是？", "options": ["A. int arr[3,4];", "B. int arr[3][4];", "C. int[3,4] arr;", "D. arr int[3][4];"], "correct_answer": "B", "explanation": "二维数组定义格式：类型 数组名[行数][列数];。"},
        {"title": "二维数组存储", "question_text": "二维数组在内存中是如何存储的？", "options": ["A. 按行存储", "B. 按列存储", "C. 随机存储", "D. 树形存储"], "correct_answer": "A", "explanation": "二维数组在内存中按行存储。"},
    ],
    "string_basics": [
        {"title": "字符串结束符", "question_text": "C语言中，字符串的结束标志是什么？", "options": ["A. 空格", "B. 换行符", "C. '\\0'或0", "D. 字符串长度"], "correct_answer": "C", "explanation": "C语言中字符串以'\\0'（空字符）作为结束标志。"},
        {"title": "字符串存储", "question_text": "字符串\"hello\"需要占用多少字节？", "options": ["A.5", "B.6", "C.7", "D.4"], "correct_answer": "B", "explanation": "\"hello\"有5个字符，加上结束符'\\0'，共6个字节。"},
    ],
    "string_functions": [
        {"title": "字符串长度函数", "question_text": "strlen(\"abc\")的返回值是？", "options": ["A.2", "B.3", "C.4", "D.abc"], "correct_answer": "B", "explanation": "strlen返回字符串长度，不包括结束符'\\0'。"},
        {"title": "字符串复制函数", "question_text": "strcpy(s1,s2)函数的作用是？", "options": ["A. 比较s1和s2", "B. 将s2复制到s1", "C. 连接s1和s2", "D. 计算s1和s2的长度"], "correct_answer": "B", "explanation": "strcpy用于将s2的内容复制到s1中。"},
    ],
    "pointer_variable": [
        {"title": "指针定义", "question_text": "以下哪个是定义整型指针变量的正确方式？", "options": ["A. int *p;", "B. pointer int p;", "C. int p*;", "D. *int p;"], "correct_answer": "A", "explanation": "定义指针变量使用类型*变量名的格式。"},
        {"title": "取地址运算符", "question_text": "如果int a=10; &a表示什么？", "options": ["A. a的值", "B. a的地址", "C. a的引用", "D. a的指针"], "correct_answer": "B", "explanation": "&是取地址运算符，&a表示变量a在内存中的地址。"},
    ],
    "pointer_arithmetic": [
        {"title": "指针运算", "question_text": "如果int *p; p+1会移动多少字节？", "options": ["A.1字节", "B.2字节", "C.4字节", "D.取决于类型"], "correct_answer": "D", "explanation": "指针运算中，p+1移动的字节数取决于指针指向的数据类型。"},
        {"title": "指针比较", "question_text": "两个指针可以进行比较运算吗？", "options": ["A.不可以", "B.可以，但只能在同一数组内", "C.可以，任何指针都行", "D.只有整型指针可以"], "correct_answer": "B", "explanation": "同类型指针可以在同一数组内进行比较。"},
    ],
    "pointer_array": [
        {"title": "数组名作为指针", "question_text": "数组名作为右值时，表示什么？", "options": ["A.数组第一个元素的副本", "B.数组第一个元素的地址", "C.数组所有元素", "D.数组长度"], "correct_answer": "B", "explanation": "数组名作为右值时表示数组首元素的地址（指针常量）。"},
        {"title": "指针与数组关系", "question_text": "arr[i]与*(arr+i)的关系是？", "options": ["A. arr[i]更快", "B. *(arr+i)更快", "C.两者等价", "D.没有关系"], "correct_answer": "C", "explanation": "arr[i]和*(arr+i)在C语言中是等价的。"},
    ],
    "pointer_string": [
        {"title": "字符指针与字符串", "question_text": "char *s=\"hello\"; s指向什么？", "options": ["A.字符h", "B.字符串hello", "C.字符h的地址", "D.字符串首地址"], "correct_answer": "D", "explanation": "字符指针s指向字符串\"hello\"的首字符地址。"},
    ],
    "pointer_parameter": [
        {"title": "指针作为参数", "question_text": "在函数中修改主调函数变量，需要使用什么？", "options": ["A. 值传递", "B. 指针或引用", "C. 全局变量", "D. 静态变量"], "correct_answer": "B", "explanation": "C语言中函数参数是值传递，要修改主调函数变量需要传递指针。"},
        {"title": "指针参数作用", "question_text": "void swap(int *a, int *b)函数的作用是？", "options": ["A. 交换a和b的值", "B. 交换*a和*b的值", "C. 什么都不做", "D. 比较a和b"], "correct_answer": "B", "explanation": "传递指针后，函数通过*a和*b可以访问和修改主调函数中的实际变量值。"},
    ],
    "pointer_return": [
        {"title": "返回指针", "question_text": "函数可以返回指针吗？", "options": ["A.不可以", "B.可以，但返回的必须是静态或动态内存", "C.可以返回任何指针", "D.只能返回整数"], "correct_answer": "B", "explanation": "函数可以返回指针，但返回的指针必须指向有效的内存区域。"},
    ],
    "struct_definition": [
        {"title": "结构体定义", "question_text": "定义结构体的关键字是？", "options": ["A. union", "B. struct", "C. enum", "D. typedef"], "correct_answer": "B", "explanation": "struct用于定义结构体类型。"},
        {"title": "结构体大小", "question_text": "结构体的大小等于各成员大小之和吗？", "options": ["A.总是等于", "B.不一定，由于内存对齐可能更大", "C.总是更大", "D.总是更小"], "correct_answer": "B", "explanation": "由于内存对齐，结构体大小可能大于各成员大小之和。"},
    ],
    "struct_variable": [
        {"title": "结构体变量定义", "question_text": "根据已定义的结构体struct Student，如何定义变量？", "options": ["A. student s;", "B. struct Student s;", "C. Student s;", "D. struct s;"], "correct_answer": "B", "explanation": "定义结构体变量需要使用struct关键字。"},
        {"title": "结构体成员访问", "question_text": "结构体变量s的成员age，应该如何访问？", "options": ["A. s.age", "B. s->age", "C. *s.age", "D. s[age]"], "correct_answer": "A", "explanation": "结构体变量使用点运算符访问成员。"},
    ],
    "struct_array": [
        {"title": "结构体数组", "question_text": "定义结构体数组的正确方式是？", "options": ["A. struct Student[10];", "B. struct Student students[10];", "C. Student[10] students;", "D. students[10] struct;"], "correct_answer": "B", "explanation": "定义结构体数组：struct Student students[10];。"},
    ],
    "struct_pointer": [
        {"title": "结构体指针", "question_text": "struct Student *p; p->age等价于？", "options": ["A. p.age", "B. (*p).age", "C. *p.age", "D. p[age]"], "correct_answer": "B", "explanation": "结构体指针p使用->访问成员，等价于(*p).age。"},
    ],
    "union_type": [
        {"title": "联合体", "question_text": "联合体与结构体的主要区别是？", "options": ["A.联合体成员共享同一块内存", "B.联合体可以包含更多成员", "C.结构体成员共享内存", "D.没有区别"], "correct_answer": "A", "explanation": "联合体的所有成员共享同一块内存。"},
        {"title": "联合体大小", "question_text": "联合体的大小由什么决定？", "options": ["A.所有成员大小之和", "B.最大成员的大小", "C.最小成员的大小", "D.成员数量"], "correct_answer": "B", "explanation": "联合体大小由最大成员的大小决定。"},
    ],
    "enum_type": [
        {"title": "枚举类型", "question_text": "enum COLOR {RED, GREEN, BLUE}; RED的值是？", "options": ["A.0", "B.1", "C.2", "D.没有值"], "correct_answer": "A", "explanation": "枚举值默认从0开始。"},
        {"title": "枚举使用", "question_text": "枚举类型的主要作用是？", "options": ["A.节省内存", "B.提高代码可读性", "C.加快运行速度", "D.方便输入输出"], "correct_answer": "B", "explanation": "枚举用于定义一组命名的整型常量，提高代码可读性。"},
    ],
    "file_open_close": [
        {"title": "文件打开函数", "question_text": "fopen函数的返回值类型是？", "options": ["A.int", "B.FILE *", "C.char *", "D.void *"], "correct_answer": "B", "explanation": "fopen返回FILE类型的指针。"},
        {"title": "文件打开模式", "question_text": "以文本方式读取文件，应该使用什么模式？", "options": ["A.\"r\"", "B.\"rb\"", "C.\"w\"", "D.\"a\""], "correct_answer": "A", "explanation": "\"r\"表示以文本方式读取。"},
    ],
    "file_read_write": [
        {"title": "fprintf函数", "question_text": "fprintf的作用是？", "options": ["A. 从文件读取数据", "B. 向文件写入数据", "C. 关闭文件", "D. 打开文件"], "correct_answer": "B", "explanation": "fprintf用于向文件写入数据。"},
        {"title": "fscanf函数", "question_text": "fscanf的作用是？", "options": ["A. 从文件读取格式化数据", "B. 向文件写入数据", "C. 判断文件结束", "D. 文件定位"], "correct_answer": "A", "explanation": "fscanf用于从文件读取格式化数据。"},
    ],
    "file_position": [
        {"title": "文件定位函数", "question_text": "fseek函数的作用是？", "options": ["A. 读取文件", "B. 写入文件", "C. 移动文件指针位置", "D. 关闭文件"], "correct_answer": "C", "explanation": "fseek用于移动文件指针到指定位置。"},
        {"title": "ftell函数", "question_text": "ftell函数返回什么？", "options": ["A. 文件大小", "B. 当前文件指针位置（从文件开始的偏移量）", "C. 文件行数", "D. 文件字符数"], "correct_answer": "B", "explanation": "ftell返回当前文件指针位置相对于文件开头的偏移量。"},
    ],
    "file_error": [
        {"title": "feof函数", "question_text": "feof函数的作用是？", "options": ["A. 关闭文件", "B. 打开文件", "C. 判断文件是否结束", "D. 创建新文件"], "correct_answer": "C", "explanation": "feof用于判断文件是否已经到达结束位置。"},
    ],
    "algorithm_flowchart": [
        {"title": "算法特性", "question_text": "算法的特性不包括以下哪一项？", "options": ["A. 有穷性", "B. 确定性", "C. 无限性", "D. 可行性"], "correct_answer": "C", "explanation": "算法必须具有有穷性、确定性、可行性。"},
        {"title": "流程图符号", "question_text": "在流程图中，菱形框表示什么？", "options": ["A. 开始/结束", "B. 输入/输出", "C. 处理", "D. 判断"], "correct_answer": "D", "explanation": "流程图中菱形表示判断。"},
    ],
    "modular_design": [
        {"title": "模块化设计", "question_text": "模块化程序设计的优点是？", "options": ["A. 程序更小", "B. 易于维护和扩展", "C. 运行更快", "D. 减少内存使用"], "correct_answer": "B", "explanation": "模块化设计将程序分成独立模块，提高可维护性、可扩展性。"},
    ],
    "student_management": [
        {"title": "学生管理系统功能", "question_text": "学生管理系统通常不包括以下哪个功能？", "options": ["A. 添加学生信息", "B. 删除学生信息", "C. 修改学生信息", "D. 自动批改作业"], "correct_answer": "D", "explanation": "学生管理系统主要管理学生信息，不包括自动批改作业。"},
    ],
}

# 填空题模板
FILLBLANK_TEMPLATES = {
    "c_program_structure": [
        {"title": "C程序入口", "question_text": "C语言程序的执行入口是______函数。", "correct_answer": "main", "explanation": "C语言规定，程序的执行从main函数开始。"},
        {"title": "语句结束符", "question_text": "C语言中，每条语句以______作为结束标志。", "correct_answer": ";", "explanation": "分号是C语言语句的结束标志。"},
    ],
    "data_type": [
        {"title": "基本数据类型", "question_text": "C语言的基本数据类型包括int、float、double和______。", "correct_answer": "char", "explanation": "C语言四种基本数据类型。"},
        {"title": "整型大小", "question_text": "在大多数系统上，int类型通常占用______个字节。", "correct_answer": "4", "explanation": "int类型通常占用4个字节。"},
    ],
    "printf_format": [
        {"title": "格式符", "question_text": "printf中输出整数使用______格式符。", "correct_answer": "%d", "explanation": "%d用于输出整数。"},
        {"title": "换行符", "question_text": "printf中表示换行的转义字符是______。", "correct_answer": "\\n", "explanation": "\\n表示换行。"},
    ],
    "variable_constant": [
        {"title": "常量关键字", "question_text": "定义常量应使用______关键字。", "correct_answer": "const", "explanation": "const用于定义常量。"},
        {"title": "宏定义", "question_text": "#define是______定义，用于定义符号常量。", "correct_answer": "宏", "explanation": "#define是宏定义。"},
    ],
    "relational_operator": [
        {"title": "关系运算符", "question_text": "大于等于运算符是______。", "correct_answer": ">=", "explanation": ">=表示大于等于。"},
        {"title": "相等运算符", "question_text": "判断相等的运算符是______。", "correct_answer": "==", "explanation": "==是相等比较运算符。"},
    ],
    "logical_operator": [
        {"title": "逻辑与", "question_text": "逻辑与运算符是______。", "correct_answer": "&&", "explanation": "&&是逻辑与运算符。"},
        {"title": "逻辑或", "question_text": "逻辑或运算符是______。", "correct_answer": "||", "explanation": "||是逻辑或运算符。"},
    ],
    "if_statement": [
        {"title": "if格式", "question_text": "if语句的条件需要放在______括号中。", "correct_answer": "圆", "explanation": "if语句使用圆括号包围条件。"},
    ],
    "for_loop": [
        {"title": "for循环格式", "question_text": "for循环的三个表达式以______分隔。", "correct_answer": "分号", "explanation": "for(初始化;条件;更新)。"},
    ],
    "while_loop": [
        {"title": "while循环特点", "question_text": "while循环是______判断再执行循环体。", "correct_answer": "先", "explanation": "while先判断条件再执行。"},
        {"title": "do-while特点", "question_text": "do-while循环的循环体至少执行______次。", "correct_answer": "1", "explanation": "do-while先执行再判断，所以至少执行一次。"},
    ],
    "break_continue": [
        {"title": "break作用", "question_text": "break语句用于跳出当前______。", "correct_answer": "循环", "explanation": "break用于跳出循环。"},
        {"title": "continue作用", "question_text": "continue语句跳过本次循环的______语句。", "correct_answer": "剩余", "explanation": "continue跳过剩余语句进入下次循环。"},
    ],
    "function_definition": [
        {"title": "函数定义格式", "question_text": "函数定义需要指定返回类型、函数名和______列表。", "correct_answer": "参数", "explanation": "函数定义需要参数列表。"},
    ],
    "macro_definition": [
        {"title": "宏定义", "question_text": "#define用于______定义，在编译前处理。", "correct_answer": "宏", "explanation": "#define是宏定义。"},
    ],
    "one_dimensional_array": [
        {"title": "数组定义", "question_text": "定义数组需要指定元素______。", "correct_answer": "个数", "explanation": "数组定义需要指定元素个数。"},
        {"title": "数组下标", "question_text": "数组下标从______开始。", "correct_answer": "0", "explanation": "C语言数组下标从0开始。"},
    ],
    "two_dimensional_array": [
        {"title": "二维数组定义", "question_text": "二维数组定义需要指定行数和______数。", "correct_answer": "列", "explanation": "二维数组需要指定行列数。"},
    ],
    "string_basics": [
        {"title": "字符串结束符", "question_text": "C语言中字符串以______作为结束标志。", "correct_answer": "\\0", "explanation": "字符串以\\0结束。"},
    ],
    "pointer_variable": [
        {"title": "指针定义", "question_text": "定义指针变量需要使用______运算符。", "correct_answer": "*", "explanation": "指针定义使用*号。"},
        {"title": "取地址", "question_text": "&是______运算符，用于获取变量地址。", "correct_answer": "取地址", "explanation": "&用于取地址。"},
    ],
    "struct_definition": [
        {"title": "结构体关键字", "question_text": "定义结构体使用______关键字。", "correct_answer": "struct", "explanation": "struct用于定义结构体。"},
    ],
    "union_type": [
        {"title": "联合体特点", "question_text": "联合体的所有成员共享______块内存。", "correct_answer": "同一", "explanation": "联合体成员共享内存。"},
    ],
    "enum_type": [
        {"title": "枚举默认值", "question_text": "枚举值默认从______开始。", "correct_answer": "0", "explanation": "枚举值默认从0开始。"},
    ],
    "file_open_close": [
        {"title": "文件打开函数", "question_text": "fopen返回______类型的指针。", "correct_answer": "FILE", "explanation": "fopen返回FILE*。"},
    ],
    "file_position": [
        {"title": "文件定位", "question_text": "fseek用于移动文件______的位置。", "correct_answer": "指针", "explanation": "fseek移动文件指针。"},
    ],
}

DEFAULT_CHOICE_TEMPLATE = {"title": "基本概念", "question_text": "以下关于该知识点的说法，正确的是？", "options": ["A. 正确", "B. 错误", "C. 不确定", "D. 以上都不对"], "correct_answer": "A", "explanation": "请根据课堂所学知识进行判断。"}
DEFAULT_FILLBLANK_TEMPLATE = {"title": "基本概念", "question_text": "请填写正确答案：______。", "correct_answer": "答案", "explanation": "请根据知识填写。"}


def get_template_key(kp_name):
    """根据知识点名称获取模板key"""
    kp_lower = kp_name.lower()

    if "c程序的基本结构" in kp_lower or "main函数" in kp_lower:
        return "c_program_structure"
    elif "语句与注释" in kp_lower:
        return "statement_comment"
    elif "基本数据类型" in kp_lower:
        return "data_type"
    elif "标识符" in kp_lower:
        return "identifier"
    elif "变量与常量" in kp_lower:
        return "variable_constant"
    elif "printf" in kp_lower:
        return "printf_format"
    elif "算法" in kp_lower or "流程图" in kp_lower:
        return "algorithm_flowchart"
    elif "模块化" in kp_lower or "程序设计流程" in kp_lower:
        return "modular_design"
    elif "学生管理" in kp_lower:
        return "student_management"
    elif "关系运算符" in kp_lower:
        return "relational_operator"
    elif "逻辑运算符" in kp_lower:
        return "logical_operator"
    elif "if语句基本形式" in kp_lower:
        return "if_statement"
    elif "if语句嵌套" in kp_lower:
        return "if_nesting"
    elif "条件运算符" in kp_lower:
        return "conditional_operator"
    elif "switch" in kp_lower:
        return "switch_statement"
    elif "for循环" in kp_lower:
        return "for_loop"
    elif "while循环" in kp_lower:
        return "while_loop"
    elif "do-while" in kp_lower:
        return "do_while_loop"
    elif "循环嵌套" in kp_lower:
        return "loop_nesting"
    elif "break" in kp_lower or "continue" in kp_lower:
        return "break_continue"
    elif "函数定义" in kp_lower or "函数声明" in kp_lower or "函数调用" in kp_lower:
        return "function_definition"
    elif "宏定义" in kp_lower:
        return "macro_definition"
    elif "条件编译" in kp_lower:
        return "conditional_compilation"
    elif "一维数组" in kp_lower:
        return "one_dimensional_array"
    elif "二维数组" in kp_lower:
        return "two_dimensional_array"
    elif "字符串基础" in kp_lower:
        return "string_basics"
    elif "字符串函数" in kp_lower:
        return "string_functions"
    elif "指针变量" in kp_lower:
        return "pointer_variable"
    elif "指针运算" in kp_lower:
        return "pointer_arithmetic"
    elif "指针与一维数组" in kp_lower or "指针与数组" in kp_lower:
        return "pointer_array"
    elif "指针与字符串" in kp_lower:
        return "pointer_string"
    elif "指针作为参数" in kp_lower or "指针与函数" in kp_lower:
        return "pointer_parameter"
    elif "指针作为返回值" in kp_lower:
        return "pointer_return"
    elif "结构体定义" in kp_lower:
        return "struct_definition"
    elif "结构体变量" in kp_lower:
        return "struct_variable"
    elif "结构体数组" in kp_lower:
        return "struct_array"
    elif "结构体指针" in kp_lower:
        return "struct_pointer"
    elif "联合体" in kp_lower:
        return "union_type"
    elif "枚举" in kp_lower:
        return "enum_type"
    elif "文件打开" in kp_lower or "文件关闭" in kp_lower:
        return "file_open_close"
    elif "文件读写" in kp_lower:
        return "file_read_write"
    elif "文件定位" in kp_lower:
        return "file_position"
    elif "文件错误" in kp_lower:
        return "file_error"
    else:
        return None


def generate_question(kp_name, difficulty, q_type, order):
    """生成一道题目"""
    key = get_template_key(kp_name)

    if q_type == "choice":
        templates = CHOICE_TEMPLATES.get(key, [DEFAULT_CHOICE_TEMPLATE])
        template = templates[order % len(templates)]
        return {
            "title": template["title"],
            "question_text": template["question_text"],
            "options": template["options"],
            "correct_answer": template["correct_answer"],
            "explanation": template["explanation"],
            "difficulty": difficulty,
            "question_type": "choice",
            "knowledge_points": [kp_name]
        }
    else:  # fill_blank
        templates = FILLBLANK_TEMPLATES.get(key, [DEFAULT_FILLBLANK_TEMPLATE])
        template = templates[order % len(templates)]
        return {
            "title": template["title"],
            "question_text": template["question_text"],
            "options": None,
            "correct_answer": template["correct_answer"],
            "explanation": template["explanation"],
            "difficulty": difficulty,
            "question_type": "fill_blank",
            "knowledge_points": [kp_name]
        }


async def main():
    """主函数"""
    # 读取所有配置文件
    config_dir = Path(__file__).parent / "习题数量配置"
    config_files = sorted(config_dir.glob("第*节_*.json"))

    print(f"找到 {len(config_files)} 个小节配置文件")

    # 建立数据库连接
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # 查询章节和小节映射
    async with async_session() as db:
        from app.models.course import Course

        # 先找到课程
        course_result = await db.execute(select(Course).where(Course.code == COURSE_CODE))
        course = course_result.scalar_one_or_none()

        if not course:
            print(f"错误: 找不到代码为 {COURSE_CODE} 的课程")
            return

        print(f"找到课程: {course.code} - {course.name} (id={course.id})")

        # 查询该课程下的章节
        chapter_result = await db.execute(select(Chapter).where(Chapter.course_id == course.id))
        chapters = {c.order_index: c.id for c in chapter_result.scalars().all()}
        print(f"找到 {len(chapters)} 个章节")

        # 查询所有章节下的小节
        section_result = await db.execute(select(Section).where(Section.chapter_id.in_(chapters.values())))
        sections = section_result.scalars().all()

        # 建立 (chapter_index, section_index) -> section_id 映射
        # chapter_index = Chapter.order_index (1-9)
        # section_index = Section.order_index within chapter (1-3)
        section_map = {}
        for s in sections:
            # section.order_index is the section_index within the chapter
            key = (s.chapter_id, s.order_index)
            section_map[key] = s.id

        # 辅助：用chapter id查找order_index
        chapter_id_to_order = {v: k for k, v in chapters.items()}

        print(f"找到 {len(sections)} 个小节")

    all_questions = []
    total_choice = 0
    total_fillblank = 0

    for config_file in config_files:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        chapter_index = config["chapter_index"]
        section_index = config["section_index"]
        section_title = config["section_title"]
        base_questions_count = config["base_questions_count"]
        knowledge_points = config["knowledge_points"]

        # 获取 chapter_db_id
        chapter_db_id = chapters.get(chapter_index)
        if not chapter_db_id:
            print(f"警告: 找不到chapter_index={chapter_index}对应的chapter，跳过")
            continue

        # 获取 section_id
        section_id = section_map.get((chapter_db_id, section_index))
        if not section_id:
            print(f"警告: 找不到章节({chapter_index}, {section_index})对应的section_id，跳过")
            continue

        chapter_id = chapter_db_id

        print(f"\n处理: 第{chapter_index}章第{section_index}节 - {section_title} (section_id={section_id})")
        print(f"  需生成 {base_questions_count} 道题")

        # 计算每个知识点需要的题目数
        kp_exercises = {}
        for kp in knowledge_points:
            kp_exercises[kp["name"]] = kp.get("exercises_needed", 2)

        # 生成题目
        questions = []
        q_order = 1

        for kp in knowledge_points:
            kp_name = kp["name"]
            difficulty = kp["difficulty"]
            exercises_needed = kp_exercises[kp_name]

            # 60% 选择题, 40% 填空题
            choice_count = int(exercises_needed * 0.6)
            fillblank_count = exercises_needed - choice_count

            if choice_count == 0 and fillblank_count == 0:
                choice_count = 1

            # 生成选择题
            for i in range(choice_count):
                q = generate_question(kp_name, difficulty, "choice", i)
                q["section_id"] = section_id
                q["chapter_id"] = chapter_id
                q["order_index"] = q_order
                questions.append(q)
                q_order += 1

            # 生成填空题
            for i in range(fillblank_count):
                q = generate_question(kp_name, difficulty, "fill_blank", i)
                q["section_id"] = section_id
                q["chapter_id"] = chapter_id
                q["order_index"] = q_order
                questions.append(q)
                q_order += 1

        # 调整数量
        while len(questions) < base_questions_count:
            kp = knowledge_points[len(questions) % len(knowledge_points)]
            q = generate_question(kp["name"], kp["difficulty"], "choice", 0)
            q["section_id"] = section_id
            q["chapter_id"] = chapter_id
            q["order_index"] = q_order
            questions.append(q)
            q_order += 1

        while len(questions) > base_questions_count:
            questions.pop()

        choice_count = sum(1 for q in questions if q["question_type"] == "choice")
        fillblank_count = sum(1 for q in questions if q["question_type"] == "fill_blank")

        print(f"  实际生成: {len(questions)} 道题 (选择题: {choice_count}, 填空题: {fillblank_count})")

        total_choice += choice_count
        total_fillblank += fillblank_count
        all_questions.extend(questions)

    print(f"\n========================================")
    print(f"总计生成: {len(all_questions)} 道题")
    print(f"  选择题: {total_choice} 道")
    print(f"  填空题: {total_fillblank} 道")
    print(f"========================================")

    # 导入数据库
    print("\n开始导入数据库...")

    async with async_session() as db:
        db_objects = []
        for q in all_questions:
            db_obj = SectionBaseQuestion(
                section_id=q["section_id"],
                chapter_id=q["chapter_id"],
                question_source="base",
                order_index=q["order_index"],
                question_type=q["question_type"],
                title=q["title"],
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                knowledge_points=q["knowledge_points"],
                difficulty=q["difficulty"],
                user_id=None,  # 基础题，所有用户共享
            )
            db_objects.append(db_obj)

        db.add_all(db_objects)
        await db.commit()
        print(f"成功导入 {len(db_objects)} 道题目到数据库！")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
