"""迁移脚本：C语言程序设计完整课程数据

执行方式：python init_db.py 后运行
python -m migrations.004_add_c_course_data

数据包括：
- 章节 (Chapter)
- 小节 (Section)
- 知识点 (SectionKnowledgePoint)
- 基础题 (SectionBaseQuestion) - 每小节10道
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal, engine
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_base_question import SectionBaseQuestion
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload


# ==================== 课程信息 ====================
COURSE_CODE = "C"
COURSE_NAME = "C语言程序设计"

# ==================== 章节和小节数据 ====================
CHAPTERS_DATA = [
    {
        "title": "第1章 程序设计和C语言",
        "description": "了解C语言的基本概念、程序结构以及上机步骤",
        "order_index": 1,
        "estimated_minutes": 30,
        "learning_objectives": ["理解程序和计算机语言的概念", "了解C语言的发展历史和特点", "掌握简单C语言程序的构成", "掌握上机运行C程序的步骤"],
        "difficulty_tags": ["入门"],
        "skill_tags": ["记忆理解"],
        "sections": [
            {
                "title": "1.1 什么是计算机程序",
                "description": "认识程序的基本概念",
                "order_index": 1,
                "estimated_minutes": 10,
                "content": "计算机程序是指令的集合，用于告诉计算机做什么。程序就像菜谱，详细描述了制作一道菜所需的步骤。",
                "learning_objectives": ["理解程序的概念", "了解程序的作用"],
            },
            {
                "title": "1.2 什么是计算机语言",
                "description": "认识计算机语言的分类",
                "order_index": 2,
                "estimated_minutes": 15,
                "content": "计算机语言分为机器语言、汇编语言和高级语言。C语言是一种高级语言，接近自然语言但又严格遵守语法规则。",
                "learning_objectives": ["理解计算机语言的分类", "了解机器语言、汇编语言、高级语言的区别"],
            },
            {
                "title": "1.3 C语言的发展及其特点",
                "description": "了解C语言的历史和特性",
                "order_index": 3,
                "estimated_minutes": 20,
                "content": "C语言于1972年由丹尼斯·里奇在美国贝尔实验室开发。最流行的C语言标准是ANSI C（C89/C90）。C语言特点：简洁紧凑、运算符丰富、数据类型多、控制语句结构化、语法限制少、编译式语言、指针操作直接。",
                "learning_objectives": ["了解C语言的起源", "理解C语言的主要特点", "了解ANSI C标准"],
            },
            {
                "title": "1.4 最简单的C语言程序",
                "description": "编写第一个C程序",
                "order_index": 4,
                "estimated_minutes": 30,
                "content": "最简单的C程序必须包含main函数，它是程序执行的入口点。程序结构包括：预处理指令、全局声明、main函数、其它函数。stdio.h是标准输入输出头文件，printf用于输出。",
                "learning_objectives": ["掌握main函数的作用", "理解程序的基本结构", "学会使用printf输出函数", "理解语句结束符分号的重要性", "理解头文件的作用"],
            },
            {
                "title": "1.5 运行C程序的步骤与方法",
                "description": "掌握程序开发流程",
                "order_index": 5,
                "estimated_minutes": 20,
                "content": "C程序运行步骤：1.编辑（编写源代码）2.编译（生成目标文件）3.连接（生成可执行文件）4.运行。常用开发环境有Visual C++、Dev C++、Code::Blocks等。",
                "learning_objectives": ["掌握C程序的上机步骤", "了解编辑、编译、连接、运行的过程", "熟悉常见的C语言开发环境"],
            },
            {
                "title": "1.6 程序设计的任务",
                "description": "了解程序设计的基本任务",
                "order_index": 6,
                "estimated_minutes": 15,
                "content": "程序设计的主要任务包括：分析问题、确定算法、绘制流程图、编写程序、调试程序。结构化程序设计方法主张使用顺序、选择、循环三种基本结构。",
                "learning_objectives": ["理解程序设计的基本任务", "了解结构化程序设计思想"],
            },
        ]
    },
    {
        "title": "第2章 算法——程序的灵魂",
        "description": "理解算法的概念、特性以及表示方法",
        "order_index": 2,
        "estimated_minutes": 45,
        "learning_objectives": ["理解算法的概念", "了解算法的特性", "掌握用自然语言和流程图表示算法", "理解结构化程序设计方法"],
        "difficulty_tags": ["算法基础"],
        "skill_tags": ["逻辑思维"],
        "sections": [
            {
                "title": "2.1 程序=算法+数据结构",
                "description": "理解算法与数据结构的关系",
                "order_index": 1,
                "estimated_minutes": 15,
                "content": "著名公式：程序 = 算法 + 数据结构。算法解决\"做什么\"和\"怎么做\"的问题，数据结构描述数据的形式和关系。",
                "learning_objectives": ["理解算法的定义", "理解数据结构的重要性", "理解算法和数据结构的关系"],
            },
            {
                "title": "2.2 什么是算法",
                "description": "认识算法的概念",
                "order_index": 2,
                "estimated_minutes": 15,
                "content": "算法是对特定问题求解步骤的描述，是有穷规则的集合。算法具有输入、输出、有穷性、确定性和可行性特性。",
                "learning_objectives": ["理解算法的定义", "掌握算法的五个特征"],
            },
            {
                "title": "2.3 算法的特性",
                "description": "理解算法的五大特性",
                "order_index": 3,
                "estimated_minutes": 20,
                "content": "算法的特性：有穷性（有限步骤结束）、确定性（每一步有明确定义）、可行性（能执行）、输入（零个或多个输入）、输出（至少一个输出）。",
                "learning_objectives": ["掌握有穷性的含义", "掌握确定性的含义", "掌握可行性的含义", "理解输入和输出的重要性"],
            },
            {
                "title": "2.4 怎样表示一个算法",
                "description": "学习算法的表示方法",
                "order_index": 4,
                "estimated_minutes": 30,
                "content": "算法表示方法：1.自然语言 2.流程图（用图形符号表示）3.N-S流程图 4.伪代码。自然语言直观但易歧义，流程图清晰但修改麻烦。",
                "learning_objectives": ["掌握用自然语言描述算法", "了解传统流程图的基本符号", "了解N-S流程图", "了解伪代码"],
            },
            {
                "title": "2.5 结构化程序设计方法",
                "description": "理解结构化程序设计",
                "order_index": 5,
                "estimated_minutes": 25,
                "content": "结构化程序设计主张三种基本结构：顺序结构（按顺序执行）、选择结构（条件分支）、循环结构（重复执行）。目标是使程序结构清晰、易于维护。",
                "learning_objectives": ["理解三种基本控制结构", "理解结构化程序设计的基本思想", "了解结构化程序设计的优点"],
            },
        ]
    },
    {
        "title": "第3章 简单的C程序设计——顺序程序设计",
        "description": "学习顺序结构程序设计，掌握基本数据类型和运算",
        "order_index": 3,
        "estimated_minutes": 90,
        "learning_objectives": ["掌握常量和变量的定义", "理解各种数据类型的区别", "掌握运算符和表达式的使用", "掌握赋值语句", "掌握格式输入输出函数"],
        "difficulty_tags": ["数据类型", "表达式"],
        "skill_tags": ["语法理解", "表达式计算"],
        "sections": [
            {
                "title": "3.1 顺序程序设计举例",
                "description": "了解顺序结构程序的特点",
                "order_index": 1,
                "estimated_minutes": 20,
                "content": "顺序结构是最简单的程序结构，按照语句出现的先后顺序依次执行。顺序结构不需要控制语句，是所有程序的基础。",
                "learning_objectives": ["理解顺序结构的特点", "理解程序执行的顺序性"],
            },
            {
                "title": "3.2 数据的表现形式及其运算",
                "description": "学习常量和变量",
                "order_index": 2,
                "estimated_minutes": 35,
                "content": "数据分为常量和变量。常量：整型常量（100,-50）、浮点型常量（3.14,-2.5）、字符常量（'a','\\n'）、字符串常量（\"hello\"）。变量必须先定义后使用，变量名由字母、数字、下划线组成且首字符不能是数字。",
                "learning_objectives": ["掌握整型常量的表示", "掌握浮点型常量的表示", "掌握字符常量的表示", "掌握字符串常量的表示", "掌握变量的定义和使用", "理解变量名的命名规则", "理解标识符的概念"],
            },
            {
                "title": "3.3 运算符和表达式",
                "description": "学习各种运算符",
                "order_index": 3,
                "estimated_minutes": 35,
                "content": "C语言运算符：算术运算符（+ - * / %）、赋值运算符（=及其复合形式+= -=等）、逗号运算符、自增自减运算符（++ --）、sizeof运算符。表达式由运算符和操作数组成。",
                "learning_objectives": ["掌握算术运算符的使用", "掌握赋值运算符的使用", "理解自增自减运算符的区别（前缀++i和后缀i++）", "理解复合赋值运算符", "掌握sizeof运算符", "理解运算符的优先级和结合性"],
            },
            {
                "title": "3.4 C语句",
                "description": "学习C语言的语句分类",
                "order_index": 4,
                "estimated_minutes": 25,
                "content": "C语句分为五类：1.表达式语句（表达式+分号）2.函数调用语句 3.控制语句（if,switch,while,for等）4.复合语句（用{}括起来的语句块）5.空语句（只有一个分号）。",
                "learning_objectives": ["掌握表达式语句的构成", "理解函数调用语句", "理解控制语句的作用", "掌握复合语句的使用", "理解空语句的使用"],
            },
            {
                "title": "3.5 数据的输入输出",
                "description": "学习格式输入输出函数",
                "order_index": 5,
                "estimated_minutes": 40,
                "content": "格式输出函数printf：printf(\"格式控制字符串\", 输出列表)。常用格式符：%d（整型）、%f（浮点型）、%c（字符）、%s（字符串）、%lf（双精度）。格式输入函数scanf：scanf(\"格式控制字符串\", &地址列表)。",
                "learning_objectives": ["掌握printf函数的基本使用", "掌握各种格式符的使用", "掌握scanf函数的基本使用", "理解地址列表中取地址符&的作用", "掌握字符输入输出函数getchar和putchar"],
            },
        ]
    },
    {
        "title": "第4章 选择结构程序设计",
        "description": "学习分支结构，掌握条件判断和switch语句",
        "order_index": 4,
        "estimated_minutes": 60,
        "learning_objectives": ["掌握if语句的三种形式", "理解关系运算符和逻辑运算符", "掌握条件运算符的使用", "掌握switch语句"],
        "difficulty_tags": ["分支结构"],
        "skill_tags": ["逻辑判断"],
        "sections": [
            {
                "title": "4.1 选择结构和条件判断",
                "description": "理解选择结构的作用",
                "order_index": 1,
                "estimated_minutes": 15,
                "content": "选择结构根据条件判断结果选择执行不同的代码路径。这是程序具有\"智能\"表现的基础，让程序能够做出决策。",
                "learning_objectives": ["理解选择结构的作用", "理解条件判断在程序中的意义"],
            },
            {
                "title": "4.2 if语句实现选择结构",
                "description": "学习if语句的三种形式",
                "order_index": 2,
                "estimated_minutes": 30,
                "content": "if语句三种形式：1.if(条件)语句 2.if(条件)语句1 else 语句2 3.if(条件1)语句1 else if(条件2)语句2 else 语句3。条件成立时执行紧跟的语句，非零值视为真。",
                "learning_objectives": ["掌握单分支if语句", "掌握双分支if-else语句", "掌握多分支if-else if-else语句", "理解条件的真假判断"],
            },
            {
                "title": "4.3 关系运算符和关系表达式",
                "description": "学习关系运算",
                "order_index": 3,
                "estimated_minutes": 20,
                "content": "关系运算符：<(小于)、>(大于)、<=(小于等于)、>=(大于等于)、==(等于)、!=(不等于)。关系表达式结果为真(1)或假(0)。注意==与=的区别。",
                "learning_objectives": ["掌握六种关系运算符", "理解关系表达式的值", "注意==和=的区别"],
            },
            {
                "title": "4.4 逻辑运算符和逻辑表达式",
                "description": "学习逻辑运算",
                "order_index": 4,
                "estimated_minutes": 25,
                "content": "逻辑运算符：&&(逻辑与)、||(逻辑或)、!(逻辑非)。&&要求两边都为真结果才为真；||要求至少一边为真；!取反。短路求值：第一条件已能确定结果时不计算第二条件。",
                "learning_objectives": ["掌握逻辑与运算符&&", "掌握逻辑或运算符||", "掌握逻辑非运算符!", "理解短路求值的特性"],
            },
            {
                "title": "4.5 条件运算符和条件表达式",
                "description": "学习三元运算符",
                "order_index": 5,
                "estimated_minutes": 15,
                "content": "条件运算符：表达式1?表达式2:表达式3。先求表达式1，若为真则求表达式2作为结果，否则求表达式3。用于简化简单的if-else语句。",
                "learning_objectives": ["掌握条件运算符的使用", "理解条件运算符与if-else的关系"],
            },
            {
                "title": "4.6 switch语句",
                "description": "学习多分支switch语句",
                "order_index": 6,
                "estimated_minutes": 25,
                "content": "switch语句用于多分支选择。语法：switch(表达式){case 常量1:语句组1;break;case 常量2:语句组2;break;...default:语句组n;}。表达式和case常量必须是整型或字符型。break语句使程序跳出switch。",
                "learning_objectives": ["掌握switch语句的基本结构", "理解break语句的作用", "掌握default子句的使用", "理解switch与if-else的区别和使用场景"],
            },
        ]
    },
    {
        "title": "第5章 循环结构程序设计",
        "description": "学习循环结构，掌握各种循环语句和控制语句",
        "order_index": 5,
        "estimated_minutes": 75,
        "learning_objectives": ["掌握while语句", "掌握do-while语句", "掌握for语句", "理解循环嵌套", "掌握break和continue"],
        "difficulty_tags": ["循环结构"],
        "skill_tags": ["循环控制"],
        "sections": [
            {
                "title": "5.1 循环结构概述",
                "description": "理解循环的重要性",
                "order_index": 1,
                "estimated_minutes": 10,
                "content": "循环结构允许重复执行一段代码，是程序设计中最重要的结构之一。计算机擅长做大量重复性的工作。",
                "learning_objectives": ["理解循环结构的作用", "了解循环在程序设计中的重要性"],
            },
            {
                "title": "5.2 while语句",
                "description": "学习while循环",
                "order_index": 2,
                "estimated_minutes": 20,
                "content": "while循环语法：while(条件){循环体语句;}。先判断条件，条件为真时执行循环体，为假时结束循环。注意确保循环最终会结束，否则为死循环。",
                "learning_objectives": ["掌握while循环的执行流程", "理解while循环的注意事项", "避免死循环"],
            },
            {
                "title": "5.3 do...while语句",
                "description": "学习do-while循环",
                "order_index": 3,
                "estimated_minutes": 15,
                "content": "do-while循环语法：do{循环体语句;}while(条件);。先执行一次循环体，再判断条件。无论条件是否为真，循环体至少执行一次。",
                "learning_objectives": ["掌握do-while循环的执行流程", "理解do-while与while的区别"],
            },
            {
                "title": "5.4 for语句",
                "description": "学习for循环",
                "order_index": 4,
                "estimated_minutes": 25,
                "content": "for循环语法：for(初始化;条件;更新){循环体;}。初始化只执行一次，然后判断条件，条件为真时执行循环体，循环体执行完后执行更新，再判断条件。for循环最灵活，可替代while。",
                "learning_objectives": ["掌握for循环的执行流程", "理解for循环三个表达式的省略", "掌握for循环的灵活使用"],
            },
            {
                "title": "5.5 循环的嵌套",
                "description": "学习多重循环",
                "order_index": 5,
                "estimated_minutes": 25,
                "content": "循环嵌套指在一个循环内部再包含一个循环。外层循环执行一次，内层循环执行完整的一圈。常见应用：九九乘法表、矩阵处理等。",
                "learning_objectives": ["理解循环嵌套的概念", "掌握双重循环的执行顺序", "能分析简单的双重循环"],
            },
            {
                "title": "5.6 break和continue语句",
                "description": "学习循环控制语句",
                "order_index": 6,
                "estimated_minutes": 20,
                "content": "break语句：跳出整个循环体，提前结束循环。continue语句：结束本次循环，跳过循环体中尚未执行的语句，接着进行下一次循环条件的判定。break用于终止循环，continue用于跳过本次循环的剩余语句。",
                "learning_objectives": ["掌握break语句的作用", "掌握continue语句的作用", "理解break和continue的区别"],
            },
        ]
    },
    {
        "title": "第6章 利用数组处理批量数据",
        "description": "学习一维数组、二维数组和字符数组",
        "order_index": 6,
        "estimated_minutes": 75,
        "learning_objectives": ["掌握一维数组的定义和使用", "掌握二维数组的定义和使用", "掌握字符数组和字符串处理"],
        "difficulty_tags": ["数组"],
        "skill_tags": ["批量数据处理"],
        "sections": [
            {
                "title": "6.1 一维数组",
                "description": "学习一维数组",
                "order_index": 1,
                "estimated_minutes": 35,
                "content": "一维数组定义：类型说明符 数组名[常量表达式];。数组元素按下标访问，下标从0开始。数组必须先定义后使用，可以整体初始化（int a[5]={1,2,3,4,5};）或部分初始化。数组名表示数组首地址。",
                "learning_objectives": ["掌握一维数组的定义", "理解数组元素下标的访问方式", "掌握一维数组的初始化", "理解数组名作为地址"],
            },
            {
                "title": "6.2 二维数组",
                "description": "学习二维数组",
                "order_index": 2,
                "estimated_minutes": 30,
                "content": "二维数组定义：类型说明符 数组名[行常量][列常量];。二维数组元素按行存储，可以用行列下标访问。初始化方式：int a[2][3]={{1,2,3},{4,5,6}};或int a[2][3]={1,2,3,4,5,6};。",
                "learning_objectives": ["掌握二维数组的定义", "理解二维数组的存储方式", "掌握二维数组的初始化", "掌握用行列下标访问元素"],
            },
            {
                "title": "6.3 字符数组与字符串",
                "description": "学习字符数组和字符串",
                "order_index": 3,
                "estimated_minutes": 40,
                "content": "字符数组：存储字符的数组，如char c[10];。字符串以'\\0'结尾。字符串常量如\"hello\"自动包含'\\0'。字符串处理函数：strlen(求长度)、strcpy(字符串复制)、strcmp(字符串比较)、strcat(字符串连接)。",
                "learning_objectives": ["掌握字符数组的定义和使用", "理解字符串结束标志'\\0'", "掌握常用字符串处理函数的使用"],
            },
        ]
    },
    {
        "title": "第7章 函数",
        "description": "学习函数的定义、调用和参数传递",
        "order_index": 7,
        "estimated_minutes": 90,
        "learning_objectives": ["掌握函数的定义和调用", "理解函数参数传递方式", "掌握递归函数", "理解变量的作用域和存储类别"],
        "difficulty_tags": ["函数"],
        "skill_tags": ["模块化编程"],
        "sections": [
            {
                "title": "7.1 函数的定义",
                "description": "学习如何定义函数",
                "order_index": 1,
                "estimated_minutes": 25,
                "content": "函数定义形式：返回值类型 函数名(参数列表){函数体}。参数列表要说明参数类型和参数名。无返回值时用void。函数要先定义后使用，或先声明后使用。",
                "learning_objectives": ["掌握函数定义的基本形式", "理解参数列表的作用", "掌握无参函数和有参函数的定义", "理解函数返回值的处理"],
            },
            {
                "title": "7.2 函数的调用",
                "description": "学习如何调用函数",
                "order_index": 2,
                "estimated_minutes": 25,
                "content": "函数调用形式：函数名(实参列表)。函数调用方式：语句调用（不关心返回值）、表达式调用（返回值参与运算）、参数调用（作为其它函数的参数）。",
                "learning_objectives": ["掌握函数调用的基本方式", "理解函数调用的三种形式", "掌握函数声明的作用"],
            },
            {
                "title": "7.3 函数参数传递",
                "description": "学习参数传递机制",
                "order_index": 3,
                "estimated_minutes": 30,
                "content": "C语言参数传递是值传递（副本传递）。基本类型参数传递的是值的副本，数组名作为参数时传递的是地址（引用传递的概念）。被调函数修改形参不影响实参本身。",
                "learning_objectives": ["理解值传递的机制", "理解数组作为参数的传递方式", "掌握指针作为函数参数"],
            },
            {
                "title": "7.4 函数的嵌套调用和递归",
                "description": "学习递归函数",
                "order_index": 4,
                "estimated_minutes": 35,
                "content": "函数不能嵌套定义，但可以嵌套调用（在一个函数中调用另一个函数）。递归函数是函数直接或间接调用自身。递归要有终止条件，否则会无限递归。典型例子：阶乘、斐波那契数列。",
                "learning_objectives": ["理解函数的嵌套调用", "掌握递归函数的概念", "掌握递归函数的设计方法", "理解递归的终止条件"],
            },
            {
                "title": "7.5 变量的作用域和存储类别",
                "description": "学习变量作用域",
                "order_index": 5,
                "estimated_minutes": 35,
                "content": "变量作用域：局部变量（在函数内部定义，只在函数内有效）、全局变量（在函数外部定义，整个文件有效）。存储类别：auto（自动）、static（静态）、register（寄存器）、extern（外部引用）。static局部变量保留上次值。",
                "learning_objectives": ["理解局部变量的作用范围", "理解全局变量的作用范围", "掌握static修饰符的作用", "理解不同存储类别的特点"],
            },
        ]
    },
    {
        "title": "第8章 指针",
        "description": "学习指针的概念和指针的使用",
        "order_index": 8,
        "estimated_minutes": 90,
        "learning_objectives": ["理解指针的概念", "掌握指针变量的定义和使用", "掌握指针与数组的关系", "理解指针与函数"],
        "difficulty_tags": ["指针"],
        "skill_tags": ["地址操作"],
        "sections": [
            {
                "title": "8.1 指针的概念",
                "description": "理解指针的基础概念",
                "order_index": 1,
                "estimated_minutes": 25,
                "content": "指针是变量的地址，指针变量是存储地址的变量。定义形式：类型 *指针变量名;。&运算符取地址，*运算符取地址指向的内容。指针大小在32位系统是4字节，64位系统是8字节。",
                "learning_objectives": ["理解指针的概念", "掌握指针变量的定义", "掌握&和*运算符的使用", "理解不同类型指针的差异"],
            },
            {
                "title": "8.2 指针与数组",
                "description": "学习指针与数组的关系",
                "order_index": 2,
                "estimated_minutes": 35,
                "content": "数组名是指向首元素的常量指针。指针可以像数组一样用下标访问。*(p+i)等同于p[i]。指针运算：加减整数（移动指针）、两个指针相减（距离）。",
                "learning_objectives": ["理解数组名作为指针常量", "掌握通过指针访问数组元素", "掌握指针算术运算", "理解指针与数组名的区别"],
            },
            {
                "title": "8.3 指针与函数",
                "description": "学习指针作为函数参数",
                "order_index": 3,
                "estimated_minutes": 30,
                "content": "指针作为函数参数可以实现双向通信（引用调用效果）。返回指针值的函数叫指针函数。注意不要返回局部变量的地址。指向函数的指针叫函数指针。",
                "learning_objectives": ["掌握指针作为函数参数", "理解指针参数实现引用传递", "掌握指针函数的定义和使用", "了解函数指针的概念"],
            },
            {
                "title": "8.4 动态内存分配",
                "description": "学习内存管理",
                "order_index": 4,
                "estimated_minutes": 30,
                "content": "动态内存分配函数：malloc(字节数)、free(指针)、calloc(个数,字节数)、realloc(指针,新大小)。动态分配的内存在堆区，需要手动free释放。内存分配失败返回NULL。",
                "learning_objectives": ["掌握malloc和free的使用", "掌握calloc的使用", "理解动态内存分配的重要性", "掌握避免内存泄漏的方法"],
            },
        ]
    },
    {
        "title": "第9章 用户自己建立数据类型",
        "description": "学习结构体、共用体、枚举和typedef",
        "order_index": 9,
        "estimated_minutes": 75,
        "learning_objectives": ["掌握结构体类型的定义和使用", "掌握结构体数组和指针", "理解链表的概念", "了解共用体和枚举"],
        "difficulty_tags": ["自定义类型"],
        "skill_tags": ["数据抽象"],
        "sections": [
            {
                "title": "9.1 结构体类型的定义",
                "description": "学习结构体",
                "order_index": 1,
                "estimated_minutes": 25,
                "content": "结构体是不同类型数据的集合。定义形式：struct 结构体名{成员列表;};。成员可以是不同类型。定义结构体变量：struct 结构体名 变量名;。",
                "learning_objectives": ["掌握结构体类型的定义", "掌握结构体变量的定义", "理解结构体与数组的区别"],
            },
            {
                "title": "9.2 结构体变量的引用",
                "description": "学习结构体变量的使用",
                "order_index": 2,
                "estimated_minutes": 20,
                "content": "结构体变量引用成员用点运算符(.)：变量名.成员名。如果是指针变量，用箭头运算符(->)：指针变量->成员名。",
                "learning_objectives": ["掌握结构体变量成员的引用方式", "掌握结构体指针的使用", "理解.和->运算符的区别"],
            },
            {
                "title": "9.3 结构体数组",
                "description": "学习结构体数组",
                "order_index": 3,
                "estimated_minutes": 20,
                "content": "结构体数组是指数组元素为结构体类型的数组。定义：struct Student stu[50];。可以存放50个学生信息。初始化时用花括号包含每个元素的成员值。",
                "learning_objectives": ["掌握结构体数组的定义", "掌握结构体数组的初始化", "掌握结构体数组的使用"],
            },
            {
                "title": "9.4 链表",
                "description": "学习链表的概念和操作",
                "order_index": 4,
                "estimated_minutes": 35,
                "content": "链表是一种动态数据结构，由节点组成，每个节点包含数据和指向下一个节点的指针。单向链表：节点包含数据和next指针。链表的优点是可以动态分配内存，不需要连续空间。",
                "learning_objectives": ["理解链表的概念", "掌握链表节点的定义", "掌握链表的基本操作（创建、遍历、插入、删除）"],
            },
            {
                "title": "9.5 共用体和枚举",
                "description": "学习共用体和枚举类型",
                "order_index": 5,
                "estimated_minutes": 25,
                "content": "共用体(union)：不同类型成员共享同一段内存，大小等于最大成员。枚举(enum)：一一列举的整型常量，默认从0开始。typedef：为已有类型定义别名。",
                "learning_objectives": ["理解共用体的概念和使用场景", "掌握枚举类型的定义和使用", "掌握typedef的使用方法"],
            },
        ]
    },
    {
        "title": "第10章 文件操作",
        "description": "学习文件的基本操作",
        "order_index": 10,
        "estimated_minutes": 60,
        "learning_objectives": ["理解文件的基本概念", "掌握文件的打开和关闭", "掌握文件的读写函数", "了解文件定位"],
        "difficulty_tags": ["文件IO"],
        "skill_tags": ["数据持久化"],
        "sections": [
            {
                "title": "10.1 文件的基本概念",
                "description": "了解文件的分类",
                "order_index": 1,
                "estimated_minutes": 15,
                "content": "文件是存储在外部介质上的数据集合。C语言把文件看作字节流，分为ASCII文件（文本文件）和二进制文件。文件类型指针FILE *fp用于标识文件。",
                "learning_objectives": ["理解文件和文件指针的概念", "了解文本文件和二进制文件的区别", "理解缓冲文件系统的概念"],
            },
            {
                "title": "10.2 文件的打开与关闭",
                "description": "学习文件操作",
                "order_index": 2,
                "estimated_minutes": 15,
                "content": "fopen函数用于打开文件：FILE *fp=fopen(\"filename\",\"mode\");。打开模式：r(读)、w(写)、a(追加)、rb、wb、ab、r+、w+、a+等。fclose函数用于关闭文件：fclose(fp);。",
                "learning_objectives": ["掌握fopen函数的使用", "掌握各种文件打开模式的区别", "掌握fclose函数"],
            },
            {
                "title": "10.3 文件的读写",
                "description": "学习文件读写函数",
                "order_index": 3,
                "estimated_minutes": 30,
                "content": "字符读写：fgetc、fputc。字符串读写：fgets、fputs。格式化读写：fscanf、fprintf。二进制读写：fread、fwrite（用于二进制文件）。",
                "learning_objectives": ["掌握字符读写函数", "掌握字符串读写函数", "掌握格式化读写函数", "掌握二进制读写函数fread和fwrite"],
            },
            {
                "title": "10.4 文件的定位",
                "description": "学习文件定位操作",
                "order_index": 4,
                "estimated_minutes": 20,
                "content": "文件位置指针：rewind使位置指针回到文件开头。fseek移动位置指针：fseek(fp, offset, origin)。origin可以是SEEK_SET(0)、SEEK_CUR(1)、SEEK_END(2)。ftell返回当前位置。",
                "learning_objectives": ["掌握rewind函数", "掌握fseek函数的使用", "掌握ftell函数"],
            },
        ]
    },
]

# ==================== 知识点数据 ====================
# 每个小节的知识点列表
SECTION_KNOWLEDGE_POINTS = {
    # 第1章
    "1.1": ["程序", "计算机程序", "程序的作用"],
    "1.2": ["计算机语言", "机器语言", "汇编语言", "高级语言", "C语言"],
    "1.3": ["C语言历史", "C语言特点", "ANSI C标准"],
    "1.4": ["main函数", "程序入口", "函数", "头文件", "stdio.h", "printf函数", "语句结束符", "预处理指令", "程序结构", "注释"],
    "1.5": ["程序开发步骤", "编辑", "编译", "连接", "运行", "开发环境"],
    "1.6": ["程序设计任务", "结构化程序设计"],

    # 第2章
    "2.1": ["算法", "数据结构", "程序=算法+数据结构"],
    "2.2": ["算法的定义", "算法的有穷性"],
    "2.3": ["算法的特性", "可行性", "确定性", "输入", "输出"],
    "2.4": ["算法的表示", "自然语言", "流程图", "N-S流程图", "伪代码"],
    "2.5": ["顺序结构", "选择结构", "循环结构", "结构化程序设计"],

    # 第3章
    "3.1": ["顺序结构", "程序执行顺序"],
    "3.2": ["常量", "整型常量", "浮点型常量", "字符常量", "字符串常量", "变量", "标识符", "变量命名规则", "数据类型"],
    "3.3": ["算术运算符", "赋值运算符", "自增运算符", "自减运算符", "复合赋值运算符", "sizeof运算符", "逗号运算符", "表达式", "运算符优先级", "运算符结合性"],
    "3.4": ["表达式语句", "函数调用语句", "控制语句", "复合语句", "空语句", "语句分类"],
    "3.5": ["printf函数", "格式控制字符串", "格式符", "scanf函数", "getchar", "putchar", "输入输出"],

    # 第4章
    "4.1": ["选择结构", "条件判断"],
    "4.2": ["if语句", "单分支if", "双分支if", "多分支if", "条件判断"],
    "4.3": ["关系运算符", "关系表达式", "大于", "小于", "等于"],
    "4.4": ["逻辑运算符", "逻辑与", "逻辑或", "逻辑非", "逻辑表达式", "短路求值"],
    "4.5": ["条件运算符", "三元运算符", "?:"],
    "4.6": ["switch语句", "case子句", "break语句", "default子句", "多分支选择"],

    # 第5章
    "5.1": ["循环结构", "重复执行"],
    "5.2": ["while语句", "while循环", "循环条件", "死循环"],
    "5.3": ["do-while语句", "do-while循环", "先执行后判断"],
    "5.4": ["for语句", "for循环", "循环初始化", "循环更新", "省略for表达式"],
    "5.5": ["循环嵌套", "多重循环", "嵌套循环执行顺序"],
    "5.6": ["break语句", "continue语句", "循环控制语句", "跳出循环", "跳过本次循环"],

    # 第6章
    "6.1": ["一维数组", "数组定义", "数组元素", "数组下标", "数组初始化", "数组名作为地址"],
    "6.2": ["二维数组", "数组定义", "行下标", "列下标", "数组初始化", "按行存储"],
    "6.3": ["字符数组", "字符串", "字符串结束标志", "strlen函数", "strcpy函数", "strcmp函数", "strcat函数", "字符串处理函数"],

    # 第7章
    "7.1": ["函数定义", "函数返回值", "函数参数", "函数声明"],
    "7.2": ["函数调用", "函数声明", "嵌套调用", "语句调用", "表达式调用"],
    "7.3": ["参数传递", "值传递", "地址传递", "指针参数"],
    "7.4": ["递归函数", "函数递归", "递归调用", "递归终止条件", "间接递归"],
    "7.5": ["局部变量", "全局变量", "作用域", "auto变量", "static变量", "register变量", "extern变量", "存储类别"],

    # 第8章
    "8.1": ["指针", "指针变量", "取地址运算符", "取内容运算符", "指针类型", "指针大小"],
    "8.2": ["指针与数组", "数组名作为指针", "指针算术运算", "指针下标", "指针与数组区别"],
    "8.3": ["指针作为函数参数", "引用传递", "返回指针的函数", "函数指针", "指针函数"],
    "8.4": ["动态内存分配", "malloc函数", "free函数", "calloc函数", "realloc函数", "堆内存", "内存泄漏"],

    # 第9章
    "9.1": ["结构体", "struct", "结构体类型定义", "结构体变量定义"],
    "9.2": ["结构体成员引用", "点运算符", "箭头运算符", "结构体指针"],
    "9.3": ["结构体数组", "结构体数组定义", "结构体数组初始化"],
    "9.4": ["链表", "单向链表", "节点", "指针域", "数据域", "链表操作", "动态数据结构"],
    "9.5": ["共用体", "union", "共用体内存共享", "枚举", "enum", "枚举常量", "typedef", "类型别名"],

    # 第10章
    "10.1": ["文件", "文件指针", "FILE类型", "文本文件", "二进制文件", "缓冲文件系统"],
    "10.2": ["fopen函数", "fclose函数", "文件打开模式", "r模式", "w模式", "a模式"],
    "10.3": ["fgetc函数", "fputc函数", "fgets函数", "fputs函数", "fscanf函数", "fprintf函数", "fread函数", "fwrite函数", "文件读写"],
    "10.4": ["rewind函数", "fseek函数", "ftell函数", "文件位置指针", "文件定位"],
}


# ==================== 基础题模板 ====================
# 每小节10道基础题
def generate_base_questions(section_key: str, section_id: int, chapter_id: int) -> list:
    """根据小节生成基础题"""

    # 定义题目模板库（按知识点）
    question_templates = {
        # 第1章
        "main函数": [
            {"title": "C程序入口函数", "text": "C语言程序中，哪个函数是程序执行的入口点？", "options": ["input", "main", "start", "program"], "answer": "B", "explanation": "main函数是C语言的入口函数，每个C程序都必须包含一个main函数。", "difficulty": 1},
            {"title": "main函数返回值", "text": "C语言中，main函数的返回类型通常是什么？", "options": ["void", "int", "char", "float"], "answer": "B", "explanation": "main函数通常返回int类型，表示程序退出状态。", "difficulty": 1},
        ],
        "printf函数": [
            {"title": "printf函数功能", "text": "以下哪个函数用于在屏幕上输出信息？", "options": ["scanf", "printf", "getchar", "gets"], "answer": "B", "explanation": "printf函数用于格式化输出到屏幕，scanf用于从键盘输入。", "difficulty": 1},
            {"title": "printf格式符", "text": "在printf中，使用哪个格式符输出整数？", "options": ["%f", "%c", "%d", "%s"], "answer": "C", "explanation": "%d用于输出整型，%f用于浮点型，%c用于字符，%s用于字符串。", "difficulty": 1},
        ],
        "语句结束符": [
            {"title": "语句结束符号", "text": "C语言中，每个语句必须以什么符号结束？", "options": ["，", "；", "。", "："], "answer": "B", "explanation": "C语言中语句必须以分号(;)结束，这是C语言的语法要求。", "difficulty": 1},
        ],
        "注释": [
            {"title": "注释符号", "text": "C语言中，单行注释用什么符号表示？", "options": ["/* */", "//", "#", "--"], "answer": "B", "explanation": "//是C99标准引入的单行注释符号，/* */是多行注释。", "difficulty": 1},
        ],
        "头文件": [
            {"title": "头文件作用", "text": "#include <stdio.h>的作用是什么？", "options": ["定义main函数", "引入标准输入输出库", "声明数学函数", "定义字符串类型"], "answer": "B", "explanation": "stdio.h是标准输入输出头文件，提供了printf、scanf等函数声明。", "difficulty": 1},
        ],
        "程序结构": [
            {"title": "程序基本结构", "text": "C语言程序的基本结构不包括以下哪部分？", "options": ["预处理指令", "main函数", "输入输出语句", "循环语句"], "answer": "D", "explanation": "C程序基本结构包括预处理指令、全局声明、main函数、其它函数，循环语句不是必需的。", "difficulty": 1},
        ],

        # 第3章 - 变量和数据类型
        "常量": [
            {"title": "整型常量识别", "text": "以下哪个是合法的整型常量？", "options": ["3.14", "100", "a"], "answer": "B", "explanation": "整型常量是不带小数点的整数。3.14是浮点型，a是字符，\"100\"是字符串。", "difficulty": 1},
            {"title": "浮点型常量", "text": "以下哪个是合法的浮点型常量？", "options": ["314", "3.14", "'3'"], "answer": "C", "explanation": "浮点型常量必须包含小数点，如3.14。", "difficulty": 1},
            {"title": "字符常量", "text": "字符常量'a'在内存中存储的是什么？", "options": ["字符a", "字符a的ASCII码值97", "字母a的位置"], "answer": "B", "explanation": "字符常量存储的是字符的ASCII码值，'a'的ASCII码是97。", "difficulty": 1},
        ],
        "变量": [
            {"title": "变量定义", "text": "以下哪个是正确的变量定义？", "options": ["int 123name;", "float $price;", "int age;", "double height;"], "answer": "C", "explanation": "变量名必须以字母或下划线开头，不能以数字开头。$不是合法字符。", "difficulty": 1},
            {"title": "变量命名规则", "text": "以下哪个不能作为变量名？", "options": ["name1", "_total", "int", "sum2"], "answer": "C", "explanation": "int是C语言关键字，不能作为变量名。", "difficulty": 1},
        ],
        "数据类型": [
            {"title": "基本数据类型", "text": "C语言的基本数据类型不包括？", "options": ["整型", "浮点型", "数组型", "字符型"], "answer": "C", "explanation": "C语言基本数据类型包括整型、浮点型、字符型，数组不是基本数据类型。", "difficulty": 1},
        ],
        "算术运算符": [
            {"title": "除法运算符", "text": "在C语言中，10/3的结果是多少？", "options": ["3.333", "3", "4", "3.0"], "answer": "B", "explanation": "整数除法结果还是整数，10/3=3（截断小数部分）。", "difficulty": 1},
            {"title": "取模运算符", "text": "表达式10%3的值是多少？", "options": ["3", "1", "0", "3.33"], "answer": "B", "explanation": "%是取模（取余）运算符，10%3=1（10除以3余1）。", "difficulty": 1},
            {"title": "自增运算符", "text": "执行int a=5; printf(\"%d\", ++a);后，a的值和输出结果分别是？", "options": ["5, 5", "6, 6", "6, 5", "5, 6"], "answer": "B", "explanation": "++a是前缀自增，先自增再使用，所以a变成6，输出6。", "difficulty": 2},
            {"title": "后缀自增", "text": "int i=5; printf(\"%d\", i++);输出结果是什么？", "options": ["5", "6", "4", "7"], "answer": "A", "explanation": "i++是后缀自增，先使用再自增，所以输出5，之后i变成6。", "difficulty": 2},
            {"title": "复合赋值", "text": "int a=10; a+=5; 执行后a的值是？", "options": ["5", "10", "15", "50"], "answer": "C", "explanation": "a+=5等同于a=a+5，所以a=10+5=15。", "difficulty": 1},
        ],
        "运算符优先级": [
            {"title": "优先级判断", "text": "表达式3+4*5的值是多少？", "options": ["35", "23", "47", "45"], "answer": "B", "explanation": "*优先级高于+，所以等价于3+(4*5)=3+20=23。", "difficulty": 1},
        ],
        "scanf函数": [
            {"title": "scanf参数", "text": "使用scanf输入整数时，参数应该传递什么？", "options": ["变量名", "变量的地址", "变量的值", "字符串"], "answer": "B", "explanation": "scanf需要知道变量的地址才能写入数据，所以要传递&变量名。", "difficulty": 1},
        ],

        # 第4章 - 选择结构
        "if语句": [
            {"title": "if语句基本形式", "text": "if(x>0) printf(\"正数\"); else printf(\"非正数\"); 当x=0时输出什么？", "options": ["正数", "非正数", "什么都不输出", "程序出错"], "answer": "B", "explanation": "x=0时条件x>0不成立(假)，执行else分支，输出\"非正数\"。", "difficulty": 1},
            {"title": "if-else嵌套", "text": "以下代码的输出是？\nif(5>3) if(2>4) printf(\"A\"); else printf(\"B\");", "options": ["A", "B", "AB", "什么都不输出"], "answer": "B", "explanation": "5>3为真，进入内层if；2>4为假，所以执行else，输出B。", "difficulty": 2},
        ],
        "关系运算符": [
            {"title": "关系运算结果", "text": "表达式5==5的结果是？", "options": ["5", "真(1)", "假(0)", "语法错误"], "answer": "B", "explanation": "==是关系运算符，相等结果为真，即1。", "difficulty": 1},
            {"title": "==与=的区别", "text": "下面哪个if条件能正确判断x是否等于0？", "options": ["if(x=0)", "if(x==0)", "if(!x)", "B和C都正确"], "answer": "D", "explanation": "x==0是相等判断，!x表示x为假（即x==0）。x=0是赋值语句，永远为假。", "difficulty": 2},
        ],
        "逻辑运算符": [
            {"title": "逻辑与", "text": "表达式(5>3)&&(2<4)的结果是？", "options": ["0", "1", "5>3&&2<4", "语法错误"], "answer": "B", "explanation": "5>3为真(1)，2<4为真(1)，逻辑与结果为真(1)。", "difficulty": 1},
            {"title": "逻辑或", "text": "表达式(5>3)||(2>4)的结果是？", "options": ["0", "1", "假", "错误"], "answer": "B", "explanation": "5>3为真，逻辑或只要一边为真结果就为真，所以是1。", "difficulty": 1},
            {"title": "逻辑非", "text": "表达式!(5>3)的结果是？", "options": ["1", "0", "真", "5<3"], "answer": "B", "explanation": "5>3为真，!真=假，即0。", "difficulty": 1},
        ],
        "switch语句": [
            {"title": "switch基本用法", "text": "switch语句的表达式类型不能是？", "options": ["整型", "字符型", "浮点型", "枚举型"], "answer": "C", "explanation": "switch表达式的值必须是整型、字符型或枚举型，不能是浮点型。", "difficulty": 1},
            {"title": "break的作用", "text": "switch语句中，break语句的作用是？", "options": ["结束程序", "跳出switch结构", "暂停执行", "返回调用函数"], "answer": "B", "explanation": "break使程序跳出switch，继续执行switch后面的语句。", "difficulty": 1},
        ],

        # 第5章 - 循环结构
        "while语句": [
            {"title": "while循环执行次数", "text": "int i=0; while(i<3){ printf(\"%d\",i); i++; } 输出结果是？", "options": ["012", "123", "0123", "321"], "answer": "A", "explanation": "i从0开始，循环3次，输出012。", "difficulty": 1},
            {"title": "while循环条件", "text": "以下哪个可能导致while死循环？", "options": ["while(1){i++;}", "while(i<10){i++;}", "while(i>0){i--;}", "while(i!=0){i=0;}"], "answer": "A", "explanation": "while(1)是死循环，因为条件永远为真。", "difficulty": 1},
        ],
        "do-while语句": [
            {"title": "do-while特点", "text": "do-while循环与while循环的主要区别是？", "options": ["do-while循环速度更快", "do-while至少执行一次", "while循环不能嵌套", "do-while不需要条件"], "answer": "B", "explanation": "do-while先执行一次循环体再判断条件，所以至少执行一次。", "difficulty": 1},
        ],
        "for语句": [
            {"title": "for循环执行次数", "text": "for(i=0;i<3;i++) printf(\"%d\",i); 输出结果是？", "options": ["012", "123", "0123", "321"], "answer": "A", "explanation": "i从0到2循环3次，输出012。", "difficulty": 1},
            {"title": "for循环省略", "text": "for(;i<5;){i++;} 这是合法的for循环吗？", "options": ["不合法", "合法，只是省略了初始化和更新", "缺少语法错误", "只省略了初始化"], "answer": "B", "explanation": "for循环的三个表达式都可以省略，但分号不能省略。", "difficulty": 1},
        ],
        "break语句": [
            {"title": "break跳出", "text": "循环for(i=0;i<10;i++){ if(i==5) break; }结束后，i的值是？", "options": ["4", "5", "6", "10"], "answer": "B", "explanation": "当i==5时执行break，break执行后立即跳出循环，i保持为5。", "difficulty": 1},
        ],
        "continue语句": [
            {"title": "continue跳过后续语句", "text": "for(i=0;i<3;i++){ if(i==1) continue; printf(\"%d\",i); } 输出结果是？", "options": ["012", "02", "01", "123"], "answer": "B", "explanation": "当i==1时continue，跳过后面的printf，执行下一次循环，所以输出02。", "difficulty": 1},
        ],

        # 第6章 - 数组
        "一维数组": [
            {"title": "数组下标", "text": "int a[5]={1,2,3,4,5}; printf(\"%d\",a[2]);输出结果是？", "options": ["1", "2", "3", "4"], "answer": "C", "explanation": "数组下标从0开始，a[2]是第3个元素，值为3。", "difficulty": 1},
            {"title": "数组初始化", "text": "int a[5]={1,2}; 数组a的前三个元素是？", "options": ["1,2,0", "1,2,随机值", "1,2,2", "0,0,0"], "answer": "A", "explanation": "部分初始化时，未初始化的元素自动为0。", "difficulty": 1},
            {"title": "数组越界", "text": "int a[3]; printf(\"%d\",a[3]); 会发生什么？", "options": ["输出0", "输出随机值", "编译错误", "输出3"], "answer": "B", "explanation": "a[3]是数组越界访问，访问的是未知内存，输出随机值。", "difficulty": 1},
            {"title": "数组名", "text": "关于数组名，以下说法正确的是？", "options": ["数组名可以改变", "数组名代表数组首地址", "数组名可以自增", "数组名是一个指针变量"], "answer": "B", "explanation": "数组名是常量指针，表示数组首元素的地址，不能改变。", "difficulty": 1},
        ],
        "二维数组": [
            {"title": "二维数组访问", "text": "int a[2][3]={{1,2,3},{4,5,6}}; printf(\"%d\",a[1][2]);", "options": ["3", "4", "5", "6"], "answer": "D", "explanation": "a[1][2]是第2行第3列的元素，值为6。", "difficulty": 1},
            {"title": "二维数组存储", "text": "二维数组在内存中是如何存储的？", "options": ["按行存储", "按列存储", "随机存储", "索引存储"], "answer": "A", "explanation": "C语言二维数组按行存储，先存第一行，再存第二行。", "difficulty": 1},
        ],
        "字符数组": [
            {"title": "字符串结束标志", "text": "字符串\"hello\"在内存中占多少字节？", "options": ["5", "6", "10", "1"], "answer": "B", "explanation": "字符串以'\\0'结尾，所以\"hello\"占6个字节：h,e,l,l,o,\\0。", "difficulty": 1},
            {"title": "字符数组输入", "text": "char str[10]; scanf(\"%s\",str); 以下输入哪个会导致问题？", "options": ["hello", "hi", "programming", "ok"], "answer": "C", "explanation": "数组大小为10，\"programming\"长度为11，超过数组容量，会导致缓冲区溢出。", "difficulty": 2},
        ],

        # 第7章 - 函数
        "函数定义": [
            {"title": "函数返回值", "text": "下面哪个函数定义是正确的？", "options": ["void sum(int a,b)", "int sum(int a, int b)", "sum(int a,int b)int", "int sum(int a; int b)"], "answer": "B", "explanation": "函数定义格式：返回值类型 函数名(参数类型 参数名)。", "difficulty": 1},
            {"title": "函数参数类型", "text": "函数参数的类型可以省略吗？", "options": ["可以省略", "不能省略", "可以只写参数名", "无所谓"], "answer": "B", "explanation": "C语言要求函数参数必须声明类型，不能省略。", "difficulty": 1},
        ],
        "函数调用": [
            {"title": "函数调用方式", "text": "以下哪个不是函数的调用方式？", "options": ["sum(a,b);", "c=sum(a,b);", "sum;"], "answer": "C", "explanation": "函数调用必须带括号，单独写函数名不调用。", "difficulty": 1},
        ],
        "递归函数": [
            {"title": "递归终止条件", "text": "递归函数必须包含什么？", "options": ["for循环", "while循环", "终止条件", "数组参数"], "answer": "C", "explanation": "递归函数必须要有终止条件，否则会无限递归导致栈溢出。", "difficulty": 1},
            {"title": "递归计算", "text": "int fact(int n){if(n<=1)return 1;return n*fact(n-1);} fact(4)返回多少？", "options": ["4", "10", "24", "12"], "answer": "C", "explanation": "4*3*2*1=24", "difficulty": 2},
        ],
        "变量作用域": [
            {"title": "局部变量作用域", "text": "在函数内部定义的变量，其作用域是？", "options": ["整个程序", "定义该变量的函数内部", "所有文件", "全局"], "answer": "B", "explanation": "局部变量只在定义它的函数内部有效。", "difficulty": 1},
            {"title": "static变量特性", "text": "static修饰的局部变量有什么特点？", "options": ["每次调用都重新初始化", "程序结束才释放内存", "可以被其他函数访问", "不能定义在函数内"], "answer": "B", "explanation": "static局部变量只初始化一次，程序结束才释放，保留函数调用间的值。", "difficulty": 1},
        ],

        # 第8章 - 指针
        "指针": [
            {"title": "指针定义", "text": "int *p; 其中p是什么？", "options": ["整型变量", "指向整型的指针", "整型地址", "整型引用"], "answer": "B", "explanation": "int *p定义了一个指向int类型的指针变量p。", "difficulty": 1},
            {"title": "取地址运算符", "text": "int a=10; &a的值是？", "options": ["10", "a的地址", "&a", "错误"], "answer": "B", "explanation": "&是取地址运算符，&a表示变量a的内存地址。", "difficulty": 1},
            {"title": "指针使用", "text": "int a=10; int *p=&a; *p的值是？", "options": ["10", "a的地址", "p的地址", "不确定"], "answer": "A", "explanation": "*p表示p指向的内存的内容，即a的值10。", "difficulty": 1},
            {"title": "指针大小", "text": "在64位系统上，一个指针占用多少字节？", "options": ["4", "8", "16", "32"], "answer": "B", "explanation": "64位系统中指针大小为8字节，32位系统为4字节。", "difficulty": 1},
        ],
        "指针与数组": [
            {"title": "数组名作为指针", "text": "int a[5]; &a[0]等于？", "options": ["a", "&a", "a+1", "*a"], "answer": "A", "explanation": "数组名a就是数组首元素&a[0]的地址。", "difficulty": 1},
            {"title": "指针算术运算", "text": "int a[5]; a+1表示什么？", "options": ["a的值加1", "指向a[1]的地址", "数组首地址加1字节", "错误"], "answer": "B", "explanation": "指针加整数表示向前移动相应数量的元素位置，a+1指向a[1]。", "difficulty": 1},
        ],
        "指针作为函数参数": [
            {"title": "指针参数实现交换", "text": "使用指针作为函数参数可以实现什么效果？", "options": ["加快程序运行速度", "减少内存使用", "在函数内修改实参的值", "减少参数数量"], "answer": "C", "explanation": "指针参数传递的是地址，可以实现引用传递，在被调函数中修改实参。", "difficulty": 1},
        ],
        "动态内存分配": [
            {"title": "malloc返回值", "text": "malloc函数成功分配内存后返回什么？", "options": ["void*", "NULL", "0", "随机地址"], "answer": "A", "explanation": "malloc返回void*类型指针，需要类型转换后使用。分配失败返回NULL。", "difficulty": 1},
            {"title": "free使用", "text": "free函数的作用是？", "options": ["删除指针变量本身", "释放动态分配的内存", "关闭文件", "终止程序"], "answer": "B", "explanation": "free用于释放malloc等函数动态分配的内存，防止内存泄漏。", "difficulty": 1},
        ],

        # 第9章 - 结构体
        "结构体": [
            {"title": "结构体定义", "text": "以下哪个是合法的结构体定义？", "options": ["struct{int x;};", "struct Student{};", "struct{int x,y;} s;", "以上都对"], "answer": "D", "explanation": "三种都是合法的结构体定义方式。", "difficulty": 1},
            {"title": "结构体成员访问", "text": "struct Student s; 要访问s的age成员，正确写法是？", "options": ["Student.age", "s.age", "Student->age", "*s.age"], "answer": "B", "explanation": "用.运算符访问结构体变量的成员，格式为：结构体变量.成员名。", "difficulty": 1},
            {"title": "结构体指针访问", "text": "struct Student *p; 要访问p指向的结构体的age成员，正确写法是？", "options": ["p.age", "(*p).age", "p->age", "B和C都正确"], "answer": "D", "explanation": "(*p).age和p->age都能访问指针指向结构体的成员，->更常用。", "difficulty": 1},
        ],
        "共用体": [
            {"title": "共用体特点", "text": "共用体所有成员共享什么？", "options": ["同一段内存", "不同内存", "栈空间", "堆空间"], "answer": "A", "explanation": "共用体的特点是有个成员共享同一段内存，大小等于最大成员。", "difficulty": 1},
        ],
        "枚举": [
            {"title": "枚举默认值", "text": "enum Color{RED,GREEN,BLUE}; RED的值是多少？", "options": ["RED", "0", "1", "错误"], "answer": "B", "explanation": "枚举常量默认从0开始，RED=0, GREEN=1, BLUE=2。", "difficulty": 1},
        ],

        # 第10章 - 文件
        "文件": [
            {"title": "文件打开模式", "text": "以写入方式打开文件，若文件存在会怎样？", "options": ["追加到文件末尾", "报错", "清空文件内容", "保持不变"], "answer": "C", "explanation": "w模式打开已存在文件会清空其内容，需谨慎使用。", "difficulty": 1},
            {"title": "fopen返回值", "text": "fopen函数成功打开文件后返回什么？", "options": ["int", "FILE*", "char*", "void*"], "answer": "B", "explanation": "fopen返回FILE*类型的文件指针，用于后续文件操作。", "difficulty": 1},
            {"title": "feof函数", "text": "feof函数的作用是？", "options": ["判断文件是否结束", "关闭文件", "打开文件", "删除文件"], "answer": "A", "explanation": "feof(fp)用于检测文件是否到达末尾，到达末尾返回非零值。", "difficulty": 1},
        ],
        "文件读写": [
            {"title": "字符读取函数", "text": "从文件读取一个字符，应该使用哪个函数？", "options": ["fscanf", "fgetc", "fread", "gets"], "answer": "B", "explanation": "fgetc用于从文件读取一个字符，fputc用于写入一个字符。", "difficulty": 1},
            {"title": "格式化写入", "text": "要将数据格式化写入文件，应使用哪个函数？", "options": ["fputs", "fputc", "fprintf", "fwrite"], "answer": "C", "explanation": "fprintf与printf类似，但输出到文件，用于格式化写入。", "difficulty": 1},
        ],
    }

    # 通用基础题（不针对特定知识点）
    common_questions = [
        {"title": "基本语法", "text": "以下哪个是正确的C语言语句结束标志？", "options": [",", ";", ".", ":"], "answer": "B", "explanation": "C语言中语句必须以分号(;)结束。", "difficulty": 1},
        {"title": "注释格式", "text": "以下哪个是C语言的多行注释符号？", "options": ["//", "/* */", "#", "--"], "answer": "B", "explanation": "/* */是C语言的多行注释，//是单行注释。", "difficulty": 1},
        {"title": "基本输出", "text": "在屏幕上输出\"Hello\"，正确的语句是？", "options": ["printf(Hello);", "print(Hello);", "echo Hello;"], "answer": "B", "explanation": "printf需要用双引号括起要输出的字符串常量。", "difficulty": 1},
        {"title": "变量定义", "text": "定义一个整型变量a，正确的写法是？", "options": ["int a;", "integer a;", "int a", "a int;"], "answer": "A", "explanation": "C语言变量定义格式：类型名 变量名;。", "difficulty": 1},
        {"title": "头文件包含", "text": "使用标准输入输出函数需要包含哪个头文件？", "options": ["math.h", "string.h", "stdio.h", "stdlib.h"], "answer": "C", "explanation": "stdio.h是标准输入输出头文件，提供printf、scanf等函数。", "difficulty": 1},
    ]

    questions = []
    order = 1

    # 获取该小节对应的知识点
    section_kps = SECTION_KNOWLEDGE_POINTS.get(section_key, [])

    # 如果有特定知识点的题目模板，从中选题
    for kp in section_kps:
        if kp in question_templates:
            for q in question_templates[kp]:
                if order <= 10:
                    questions.append({
                        "section_id": section_id,
                        "chapter_id": chapter_id,
                        "order_index": order,
                        "question_source": "base",
                        "question_type": "choice",
                        "title": q["title"],
                        "question_text": q["text"],
                        "options": q["options"],
                        "correct_answer": q["answer"],
                        "explanation": q["explanation"],
                        "knowledge_points": [kp],
                        "difficulty": q["difficulty"],
                    })
                    order += 1

    # 如果还不够10道，用通用题补充
    for q in common_questions:
        if order <= 10:
            questions.append({
                "section_id": section_id,
                "chapter_id": chapter_id,
                "order_index": order,
                "question_source": "base",
                "question_type": "choice",
                "title": q["title"],
                "question_text": q["text"],
                "options": q["options"],
                "correct_answer": q["answer"],
                "explanation": q["explanation"],
                "knowledge_points": section_kps[:3] if section_kps else ["C语言基础"],
                "difficulty": q["difficulty"],
            })
            order += 1

    return questions


# ==================== 主函数 ====================
async def migrate():
    """执行迁移"""
    print("=" * 60)
    print("开始迁移：C语言程序设计完整课程数据")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # 1. 删除旧C语言课程（如存在）并创建新课程
            print("\n[1/4] 处理课程信息...")

            # 使用同步SQLite删除旧数据（避免外键约束问题）
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.db")
            sync_conn = sqlite3.connect(db_path)
            sync_conn.execute("PRAGMA foreign_keys=OFF")

            # 查找旧课程
            cursor = sync_conn.execute("SELECT id FROM courses WHERE code = ?", (COURSE_CODE,))
            old_course_row = cursor.fetchone()

            if old_course_row:
                old_course_id = old_course_row[0]
                # 删除相关数据（按依赖顺序）
                sync_conn.execute("DELETE FROM section_base_questions WHERE chapter_id IN (SELECT id FROM chapters WHERE course_id = ?)", (old_course_id,))
                sync_conn.execute("DELETE FROM sections WHERE chapter_id IN (SELECT id FROM chapters WHERE course_id = ?)", (old_course_id,))
                sync_conn.execute("DELETE FROM chapters WHERE course_id = ?", (old_course_id,))
                sync_conn.execute("DELETE FROM courses WHERE id = ?", (old_course_id,))
                sync_conn.commit()
                print(f"  已删除旧课程 (ID: {old_course_id})")
            sync_conn.close()
            await db.flush()

            # 创建新课程
            course = Course(
                code=COURSE_CODE,
                name=COURSE_NAME,
                description="C语言程序设计完整教材版，包含10章49节，涵盖数据类型、运算符、输入输出、控制结构、循环、数组、函数、指针、结构体、文件等全部知识点。",
                difficulty_level=1
            )
            db.add(course)
            await db.flush()
            print(f"  创建课程: {course.name} (ID: {course.id})")

            # 2. 创建章节和小节
            print("\n[2/4] 创建章节和小节...")
            total_sections = 0
            section_keys_map = {}  # (chapter_order, section_order) -> section_id

            for chapter_data in CHAPTERS_DATA:
                # 创建章节
                chapter = Chapter(
                    course_id=course.id,
                    title=chapter_data["title"],
                    description=chapter_data["description"],
                    order_index=chapter_data["order_index"],
                    estimated_minutes=chapter_data["estimated_minutes"],
                    learning_objectives=chapter_data["learning_objectives"],
                    difficulty_tags=chapter_data.get("difficulty_tags"),
                    skill_tags=chapter_data.get("skill_tags"),
                )
                db.add(chapter)
                await db.flush()
                print(f"  创建章节: {chapter.title} (ID: {chapter.id})")

                # 创建小节
                for section_data in chapter_data["sections"]:
                    section = Section(
                        chapter_id=chapter.id,
                        title=section_data["title"],
                        description=section_data["description"],
                        order_index=section_data["order_index"],
                        content=section_data.get("content", ""),
                        learning_objectives=section_data.get("learning_objectives", []),
                        estimated_minutes=section_data.get("estimated_minutes", 15),
                    )
                    db.add(section)
                    await db.flush()

                    # 生成小节key用于查找知识点，如 "1.1", "3.2"
                    section_key = f"{chapter_data['order_index']}.{section_data['order_index']}"
                    section_keys_map[section_key] = {
                        "section_id": section.id,
                        "chapter_id": chapter.id
                    }
                    total_sections += 1
                    print(f"    创建小节: {section.title} (ID: {section.id})")

            print(f"  共创建 {total_sections} 个小节")

            # 3. 为每个小节生成基础题
            print("\n[3/4] 生成基础题（每小节10道）...")
            total_questions = 0

            for section_key, ids in section_keys_map.items():
                section_id = ids["section_id"]
                chapter_id = ids["chapter_id"]

                questions = generate_base_questions(section_key, section_id, chapter_id)

                for q_data in questions:
                    question = SectionBaseQuestion(
                        section_id=q_data["section_id"],
                        chapter_id=q_data["chapter_id"],
                        order_index=q_data["order_index"],
                        question_source=q_data["question_source"],
                        question_type=q_data["question_type"],
                        title=q_data["title"],
                        question_text=q_data["question_text"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"],
                        knowledge_points=q_data["knowledge_points"],
                        difficulty=q_data["difficulty"],
                    )
                    db.add(question)
                    total_questions += 1

            print(f"  共创建 {total_questions} 道基础题")

            # 提交事务
            await db.commit()
            print("\n" + "=" * 60)
            print("迁移完成！")
            print("=" * 60)
            print(f"课程: {course.name}")
            print(f"章节数: {len(CHAPTERS_DATA)}")
            print(f"小节数: {total_sections}")
            print(f"基础题数: {total_questions}")
            print("\n知识点已关联到每道基础题。")
            print("强化题由学生在学习过程中实时生成。")

        except Exception as e:
            await db.rollback()
            print(f"\n迁移失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
