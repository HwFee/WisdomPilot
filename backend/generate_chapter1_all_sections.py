"""Generate Chapter 1 all sections content for C language course"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint
from app.models.section_base_question import SectionBaseQuestion


# 第一章小节数据
CHAPTER_1_DATA = {
    "chapter": {
        "title": "简单C程序设计",
        "description": "学习C语言的基本概念，包括程序结构、数据类型、输入输出等基础知识",
        "content": """本章介绍C语言的基本概念，包括：
1. C程序的基本结构
2. 基本数据类型
3. 变量与常量
4. 格式化输入输出

通过本章学习，学生能够编写简单的C程序。""",
        "order_index": 1,
        "estimated_minutes": 120,
        "difficulty_tags": ["基础", "入门"],
        "skill_tags": ["程序结构", "数据类型", "输入输出"]
    },
    "sections": [
        {
            "title": "C程序入门",
            "description": "通过实例学习，掌握C程序的基本结构",
            "order_index": 1,
            "estimated_minutes": 20,
            "knowledge_points": [
                {
                    "name": "C程序的基本结构",
                    "order_index": 1,
                    "content": """## C程序的基本结构

C程序主要由三部分组成：

### 1. 预处理指令
以 `#` 开头的指令，在编译前处理。用于引入头文件、定义宏等。

```c
#include <stdio.h>  // 引入标准输入输出头文件
```

### 2. main函数
程序执行的入口点，每个C程序必须且只能有一个main函数。

```c
int main() {
    // 程序代码写在这里
    return 0;
}
```

### 3. 语句
以分号 `;` 结尾，每条语句完成特定的操作。

```c
printf("Hello World");  // 输出语句
```

### 完整示例
```c
#include <stdio.h>

int main() {
    printf("Hello World");
    return 0;
}
```""",
                    "summary": "C程序由预处理指令、main函数和语句三部分组成",
                    "code_example": """#include <stdio.h>

int main() {
    printf("Hello World");
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "这是最简单的C程序结构：包含头文件、main函数入口、输出语句、返回语句",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["main函数", "预处理指令", "语句"],
                    "tips": ["一个C程序必须有且只能有一个main函数", "main函数是程序执行的起点"],
                    "common_mistakes": ["把main函数名拼写错误", "忘记写return语句"]
                },
                {
                    "name": "main函数",
                    "order_index": 2,
                    "content": """## main函数

main函数是C程序的入口点，程序从main函数开始执行。

### 基本格式
```c
int main() {
    // 程序代码
    return 0;
}
```

### 说明
- `int` 表示返回值类型为整数
- `main` 是函数名，是程序执行的入口
- `return 0;` 表示程序正常结束

### 注意事项
- main函数不能被其他函数调用
- 每个C程序必须包含一个main函数
- 不要写成 `void main()` 或 `main(void)`（不标准）""",
                    "summary": "main函数是C程序的入口点，程序从这里开始执行",
                    "code_example": """int main() {
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "标准的main函数格式，返回0表示程序正常结束",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["C程序的基本结构", "return语句"],
                    "tips": ["main函数是程序执行的唯一入口", "返回0表示程序执行成功"],
                    "common_mistakes": ["写成void main()（不标准）", "忘记写return语句"]
                },
                {
                    "name": "语句与注释",
                    "order_index": 3,
                    "content": """## 语句与注释

### 语句
语句是C程序的基本执行单元，每条语句以分号 `;` 结尾。

```c
printf("Hello");  // 这是一条输出语句
a = 10;          // 这是一条赋值语句
```

### 注释
注释用于说明代码功能，不参与程序执行。

**单行注释**：`// 注释内容`
```c
int age = 20;  // 定义年龄变量
```

**多行注释**：`/* 注释内容 */`
```c
/*
 * 这是多行注释
 * 可以写多行说明
 */
```

### 注意事项
- 注释不会影响程序运行
- 养成写注释的好习惯
- 不要在语句末尾忘记分号""",
                    "summary": "语句以分号结尾，注释用于说明代码不参与执行",
                    "code_example": """#include <stdio.h>

int main() {
    // 这是单行注释
    printf("Hello");  // 输出Hello

    /*
     * 这是多行注释
     */
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了单行注释和多行注释的用法",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["C程序的基本结构", "语句"],
                    "tips": ["注释要清晰说明代码功能", "不要过度注释"],
                    "common_mistakes": ["忘记在语句末尾加分号", "注释嵌套使用错误"]
                }
            ],
            "base_questions": [
                {
                    "order_index": 1,
                    "question_type": "choice",
                    "title": "C程序入口函数",
                    "question_text": "C语言程序的执行入口是哪个函数？",
                    "options": ["A. main()", "B. start()", "C. run()", "D. printf()"],
                    "correct_answer": "A",
                    "explanation": "C语言规定，程序的执行从main函数开始。每个C程序必须有且只能有一个main函数作为程序入口。",
                    "knowledge_points": ["main函数"],
                    "difficulty": 1
                },
                {
                    "order_index": 2,
                    "question_type": "choice",
                    "title": "语句结束符",
                    "question_text": "C语言中，每条语句应该以什么符号结尾？",
                    "options": ["A. 冒号 :", "B. 逗号 ,", "C. 分号 ;", "D. 句号 ."],
                    "correct_answer": "C",
                    "explanation": "C语言中，分号(;)是语句的结束符。每条可执行语句都必须以分号结尾，这是C语言的语法规定。",
                    "knowledge_points": ["语句与注释"],
                    "difficulty": 1
                },
                {
                    "order_index": 3,
                    "question_type": "choice",
                    "title": "注释的作用",
                    "question_text": "以下关于C语言注释的说法正确的是？",
                    "options": [
                        "A. 注释会被编译器执行",
                        "B. 注释对程序运行没有影响",
                        "C. 注释只能写在代码后面",
                        "D. 注释不能多行"
                    ],
                    "correct_answer": "B",
                    "explanation": "注释是给程序员看的说明文字，不参与程序编译和执行，对程序运行没有任何影响。",
                    "knowledge_points": ["语句与注释"],
                    "difficulty": 1
                },
                {
                    "order_index": 4,
                    "question_type": "choice",
                    "title": "预处理指令作用",
                    "question_text": "#include <stdio.h> 这行代码的作用是什么？",
                    "options": [
                        "A. 定义一个变量",
                        "B. 包含标准输入输出头文件",
                        "C. 声明一个函数",
                        "D. 输出文字"
                    ],
                    "correct_answer": "B",
                    "explanation": "#include是预处理指令，<stdio.h>是标准输入输出库的头文件，告诉编译器包含这些内容以便使用printf等函数。",
                    "knowledge_points": ["C程序的基本结构"],
                    "difficulty": 1
                },
                {
                    "order_index": 5,
                    "question_type": "choice",
                    "title": "程序结构组成",
                    "question_text": "以下哪个不是C程序的基本组成部分？",
                    "options": ["A. 预处理指令", "B. main函数", "C. 注释", "D. 变量定义"],
                    "correct_answer": "D",
                    "explanation": "C程序的基本组成部分是预处理指令、main函数和语句。变量定义是语句的一种，但不是必须的组成部分。注释是辅助说明，不是程序运行的必需部分。",
                    "knowledge_points": ["C程序的基本结构"],
                    "difficulty": 2
                }
            ]
        },
        {
            "title": "基本数据类型与变量",
            "description": "C语言的基本数据类型、标识符、变量和常量、格式化输出函数",
            "order_index": 2,
            "estimated_minutes": 25,
            "knowledge_points": [
                {
                    "name": "基本数据类型",
                    "order_index": 1,
                    "content": """## 基本数据类型

C语言的基本数据类型包括：

### 1. 整型 (int)
用于表示整数，通常占用4个字节。

```c
int age = 20;       // 整型变量
int score = 100;    // 整型变量
```

### 2. 字符型 (char)
用于表示单个字符，通常占用1个字节。

```c
char grade = 'A';   // 字符变量，用单引号
char name = 'C';    // 字符变量
```

### 3. 浮点型 (float/double)
用于表示实数（小数）。

```c
float height = 175.5f;    // 单精度浮点型
double pi = 3.14159;      // 双精度浮点型
```

### 4. 各类型占用空间
| 类型 | 占用空间 | 用途 |
|------|---------|------|
| int | 4字节 | 整数 |
| float | 4字节 | 单精度小数 |
| double | 8字节 | 双精度小数 |
| char | 1字节 | 单个字符 |""",
                    "summary": "C语言基本数据类型包括整型、字符型、浮点型",
                    "code_example": """int age = 20;
char grade = 'A';
float height = 175.5f;
double pi = 3.14159;""",
                    "code_language": "c",
                    "code_explanation": "展示了四种基本数据类型的变量声明和初始化",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["变量与常量", "printf格式化输出"],
                    "tips": ["选择合适的数据类型", "浮点常量默认是double类型"],
                    "common_mistakes": ["混淆int和float的区别", "忘记给浮点数字加小数点"]
                },
                {
                    "name": "标识符",
                    "order_index": 2,
                    "content": """## 标识符

标识符是用来命名变量、函数、数组等的名称。

### 命名规则
1. 由字母、数字和下划线组成
2. 必须以字母或下划线开头
3. 不能使用关键字（如int、if、for等）
4. 区分大小写

### 合法标识符
```c
int age;           // 合法
int student_age;   // 合法，以下划线分隔
int _value;        // 合法，以下划线开头
int maxScore;      // 合法，驼峰命名
```

### 非法标识符
```c
int 2name;         // 非法，不能以数字开头
int my-age;        // 非法，不能使用连字符
int int;           // 非法，不能使用关键字
int my name;       // 非法，不能包含空格
```

### 命名建议
- 使用有意义的名称（用age表示年龄，不要用a）
- 变量名用小写字母
- 常量全大写
- 多个单词用下划线分隔或驼峰命名""",
                    "summary": "标识符由字母、数字、下划线组成，必须以字母或下划线开头",
                    "code_example": """// 合法的标识符
int maxScore = 100;
int student_age;
double item_price;

// 不合法的标识符
int 2ndPlace;    // 错误：不能以数字开头
int my-age;      // 错误：不能使用连字符""",
                    "code_language": "c",
                    "code_explanation": "展示了合法和不合法标识符的对比",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["变量与常量", "基本数据类型"],
                    "tips": ["用有意义的名字命名", "保持命名风格一致"],
                    "common_mistakes": ["使用中文命名", "以数字开头", "包含特殊字符"]
                },
                {
                    "name": "变量与常量",
                    "order_index": 3,
                    "content": """## 变量与常量

### 变量
在程序运行过程中可以改变的量。

```c
int age;        // 声明整型变量
age = 20;       // 给变量赋值
int score = 95; // 声明时初始化
```

### 常量
在程序运行过程中不能改变的量。

**const常量**
```c
const int MAX_SCORE = 100;  // 常量，不能修改
```

**宏常量**
```c
#define PI 3.14159          // 宏常量
```

### 变量与常量的区别
| 特性 | 变量 | 常量 |
|------|------|------|
| 值可否改变 | 可以 | 不可以 |
| 定义方式 | 数据类型 变量名 | const/宏定义 |
| 内存 | 占用内存 | 不占用内存（宏常量） |

### 注意事项
- 变量使用前必须先声明
- 习惯给常量加const保护
- 宏常量没有类型检查，慎用""",
                    "summary": "变量是可变化的量，常量是不可变化的量",
                    "code_example": """#include <stdio.h>
#define PI 3.14159

int main() {
    int radius = 5;
    const int MAX_RADIUS = 100;

    radius = 10;  // 变量可以修改
    // MAX_RADIUS = 20;  // 错误！常量不能修改

    printf("Area: %.2f\\n", PI * radius * radius);
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了变量可以修改，常量不能修改的特性",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["基本数据类型", "标识符"],
                    "tips": ["习惯给常量加const保护", "宏常量没有类型检查"],
                    "common_mistakes": ["修改常量的值", "混淆常量和变量的用法"]
                },
                {
                    "name": "printf格式化输出",
                    "order_index": 4,
                    "content": """## printf格式化输出

printf是C语言中最常用的输出函数。

### 基本语法
```c
printf("格式控制字符串", 参数列表);
```

### 常用格式说明符
| 说明符 | 含义 | 示例 |
|--------|------|------|
| %d | 输出整数 | printf("%d", 10); |
| %f | 输出浮点数 | printf("%f", 3.14); |
| %.2f | 输出保留2位小数 | printf("%.2f", 3.1415); |
| %c | 输出字符 | printf("%c", 'A'); |
| %s | 输出字符串 | printf("%s", "Hello"); |
| %% | 输出百分号% | printf("100%%"); |

### 转义字符
| 字符 | 含义 |
|------|------|
| \\n | 换行 |
| \\t | 制表符 |
| \\\" | 双引号 |
| \\\\ | 反斜杠 |

### 示例
```c
int age = 20;
printf("年龄：%d岁\\n", age);
printf("成绩：%.1f\\n", 95.5);
```""",
                    "summary": "printf用于格式化输出，支持多种格式说明符和转义字符",
                    "code_example": """#include <stdio.h>

int main() {
    int age = 20;
    float height = 175.5f;
    char grade = 'A';

    printf("姓名：张三\\n");
    printf("年龄：%d岁\\n", age);
    printf("身高：%.1fcm\\n", height);
    printf("等级：%c\\n", grade);
    printf("比例：100%%\\n");

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了printf函数的各种格式说明符和转义字符的使用",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["基本数据类型", "变量与常量"],
                    "tips": ["格式字符串要用双引号", "参数个数要和格式说明符匹配"],
                    "common_mistakes": ["忘记在格式说明符前加%", "整数用%f输出", "忘记换行"]
                }
            ],
            "base_questions": [
                {
                    "order_index": 1,
                    "question_type": "choice",
                    "title": "基本数据类型",
                    "question_text": "以下哪个不是C语言的基本数据类型？",
                    "options": ["A. int", "B. float", "C. array", "D. char"],
                    "correct_answer": "C",
                    "explanation": "C语言的基本数据类型包括int（整型）、float（浮点型）、char（字符型）。array（数组）是复合数据类型，不属于基本数据类型。",
                    "knowledge_points": ["基本数据类型"],
                    "difficulty": 1
                },
                {
                    "order_index": 2,
                    "question_type": "choice",
                    "title": "标识符命名规则",
                    "question_text": "以下哪个标识符是合法的C语言变量名？",
                    "options": ["A. 2name", "B. my-name", "C. student_name", "D. my name"],
                    "correct_answer": "C",
                    "explanation": "标识符命名规则：必须以字母或下划线开头，可以包含字母、数字和下划线。student_name符合规则，其他都不合法。",
                    "knowledge_points": ["标识符"],
                    "difficulty": 1
                },
                {
                    "order_index": 3,
                    "question_type": "choice",
                    "title": "变量与常量区分",
                    "question_text": "下列关于变量的说法正确的是？",
                    "options": [
                        "A. 变量在程序运行过程中不能改变",
                        "B. 变量使用前必须先声明",
                        "C. 变量名可以是关键字",
                        "D. 变量只能存放字符类型数据"
                    ],
                    "correct_answer": "B",
                    "explanation": "变量是在程序运行过程中可以改变的量，使用前必须先声明。选项A说反了，常量才是不能改变的；选项C错误，关键字不能用作变量名；选项D错误，变量可以存放多种类型的数据。",
                    "knowledge_points": ["变量与常量"],
                    "difficulty": 2
                },
                {
                    "order_index": 4,
                    "question_type": "choice",
                    "title": "printf格式说明符",
                    "question_text": "如果要输出一个整数，应该使用哪个格式说明符？",
                    "options": ["A. %f", "B. %c", "C. %d", "D. %s"],
                    "correct_answer": "C",
                    "explanation": "%d用于输出整数（decimal），%f用于输出浮点数，%c用于输出字符，%s用于输出字符串。",
                    "knowledge_points": ["printf格式化输出"],
                    "difficulty": 1
                },
                {
                    "order_index": 5,
                    "question_type": "choice",
                    "title": "printf转义字符",
                    "question_text": "想在输出中换行，应该在格式字符串中使用什么？",
                    "options": ["A. %n", "B. \\n", "C. /n", "D. _n"],
                    "correct_answer": "B",
                    "explanation": "\\n是转义字符，表示换行。%n不是转义字符，是格式说明符的一种（用于输出字符数）。",
                    "knowledge_points": ["printf格式化输出"],
                    "difficulty": 1
                }
            ]
        },
        {
            "title": "程序设计基础",
            "description": "基本功能设计、程序设计描述的方法、程序实现及常见错误分析及编程风格",
            "order_index": 3,
            "estimated_minutes": 25,
            "knowledge_points": [
                {
                    "name": "算法与流程图",
                    "order_index": 1,
                    "content": """## 算法与流程图

### 算法
算法是解决问题的步骤和方法，是程序设计的核心。

### 算法的特性
1. **有穷性**：执行有限步骤后结束
2. **确定性**：每一步都有明确定义
3. **可行性**：能够执行
4. **输入**：有零个或多个输入
5. **输出**：有一个或多个输出

### 流程图
流程图是用图形表示算法执行过程的方法。

### 流程图符号
| 符号 | 名称 | 用途 |
|------|------|------|
| 椭圆 | 开始/结束 | 表示程序开始或结束 |
| 平行四边形 | 输入/输出 | 表示输入或输出操作 |
| 矩形 | 处理 | 表示处理或运算 |
| 菱形 | 判断 | 表示条件判断 |
| 箭头 | 流程线 | 表示执行方向 |

### 示例：求两个数最大值
```
开始 → 输入a,b → a>b? → 是 → 输出a
                  ↓否
              输出b → 结束
```""",
                    "summary": "算法是解决问题的步骤，流程图是描述算法的图形工具",
                    "code_example": """#include <stdio.h>

int main() {
    int a, b, max;

    printf("请输入两个整数：");
    scanf("%d %d", &a, &b);

    if (a > b) {
        max = a;
    } else {
        max = b;
    }

    printf("最大值是：%d\\n", max);
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了求两个数最大值的算法实现",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["程序设计描述方法"],
                    "tips": ["先画流程图再写代码", "算法要清晰明了"],
                    "common_mistakes": ["算法步骤不完整", "忽略边界条件"]
                },
                {
                    "name": "程序设计描述方法",
                    "order_index": 2,
                    "content": """## 程序设计描述方法

### 常用描述方法
1. **自然语言描述**：用日常语言描述算法步骤
2. **流程图描述**：用图形符号描述算法
3. **伪代码描述**：介于自然语言和编程语言之间的描述

### 自然语言描述示例（求和问题）
1. 定义变量sum = 0
2. 定义变量i = 1
3. 如果i <= 100，转第4步，否则转第7步
4. sum = sum + i
5. i = i + 1
6. 转回第3步
7. 输出sum的值

### 伪代码示例（求最大值）
```
输入 a, b
如果 a > b
    输出 a
否则
    输出 b
```

### 各种方法的特点
| 方法 | 优点 | 缺点 |
|------|------|------|
| 自然语言 | 容易理解 | 可能不精确 |
| 流程图 | 直观清晰 | 修改麻烦 |
| 伪代码 | 接近代码 | 需要学习 |""",
                    "summary": "程序设计描述方法包括自然语言、流程图和伪代码",
                    "code_example": """// 求1+2+...+100的伪代码
sum = 0
for i = 1 to 100
    sum = sum + i
输出 sum""",
                    "code_language": "c",
                    "code_explanation": "展示了求和算法的伪代码描述",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["算法与流程图"],
                    "tips": ["选择合适的描述方式", "描述要清晰无歧义"],
                    "common_mistakes": ["描述过于简略", "步骤顺序错误"]
                },
                {
                    "name": "常见错误分析",
                    "order_index": 3,
                    "content": """## 常见错误分析

### 语法错误
违反C语言语法规则的错误，编译器会报错。

**示例1：忘记分号**
```c
int a = 10  // 错误：缺少分号
int b = 20; // 正确
```

**示例2：变量未声明**
```c
x = 10;  // 错误：x未声明
int x = 10;  // 正确
```

**示例3：括号不匹配**
```c
if (a > b {  // 错误：缺少右括号
    max = a;
}  // 正确
```

### 逻辑错误
程序能正常运行，但结果不正确。

**示例：求平均值**
```c
// 错误：整数除法
int avg = a + b / 2;  // 错误写法

// 正确：应该先加后除
int avg = (a + b) / 2;  // 正确写法
```

### 常见错误汇总
| 错误类型 | 例子 | 解决方法 |
|----------|------|----------|
| 少分号 | `int a = 10` | 检查每条语句 |
| 括号不匹配 | `if (a > b` | 使用IDE括号匹配 |
| 变量未声明 | `x = 10` | 先声明后使用 |
| 整数除法 | `a / b` | 强制转换或用浮点 |""",
                    "summary": "常见错误分为语法错误和逻辑错误，需要仔细排查",
                    "code_example": """// 常见错误示例

// 错误1：忘记分号
int a = 10  // 缺少分号
    ;

// 错误2：变量未声明
x = 10;     // x未声明

// 错误3：整数除法
int avg = 5 / 2;  // 结果是2，不是2.5

// 正确写法
int a = 10;
int x = 10;  // 先声明
int avg = (a + 0) / 2;  // 或使用浮点除法""",
                    "code_language": "c",
                    "code_explanation": "展示了常见语法错误和逻辑错误",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["算法与流程图"],
                    "tips": ["学会阅读编译错误信息", "养成调试习惯"],
                    "common_mistakes": ["忘记分号", "整数除法丢失精度", "变量名拼写错误"]
                },
                {
                    "name": "编程风格",
                    "order_index": 4,
                    "content": """## 编程风格

### 好的编程风格

**1. 缩进一致**
```c
// 好的缩进
int main() {
    int a = 10;
    if (a > 0) {
        printf("positive");
    }
    return 0;
}
```

**2. 变量命名有意义**
```c
// 好的命名
int student_age = 20;
int score = 95;

// 不好的命名
int a = 20;  // 不知道a代表什么
int s = 95;  // 不知道s代表什么
```

**3. 添加注释**
```c
// 计算圆的面积
double radius = 5.0;
double area = 3.14159 * radius * radius;
```

**4. 代码分行**
```c
// 好的写法
int max = (a > b) ? a : b;

// 不好的写法
int max=(a>b)?a:b;
```

### 编程风格建议
- 缩进使用4个空格或Tab
- 每行不超过80个字符
- 函数之间加空行
- 变量名要有意义
- 合理添加注释
- 常量使用宏定义或const""",
                    "summary": "良好的编程风格包括合理缩进、有意义命名、适当注释",
                    "code_example": """#include <stdio.h>
#define PI 3.14159

int main() {
    // 好的编程风格示例
    int radius = 5;           // 有意义的变量名
    double area;               // 变量声明

    // 计算圆的面积
    area = PI * radius * radius;

    printf("半径：%d\\n", radius);
    printf("面积：%.2f\\n", area);

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "展示了良好编程风格的示例",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["常见错误分析"],
                    "tips": ["保持代码风格一致", "代码要整洁清晰"],
                    "common_mistakes": ["不缩进或缩进混乱", "变量名无意义", "不写注释"]
                }
            ],
            "base_questions": [
                {
                    "order_index": 1,
                    "question_type": "choice",
                    "title": "算法的特性",
                    "question_text": "算法必须具有的特性不包括以下哪一项？",
                    "options": ["A. 有穷性", "B. 确定性", "C. 可逆性", "D. 可行性"],
                    "correct_answer": "C",
                    "explanation": "算法必须具有：有穷性（有限步骤结束）、确定性（每步明确定义）、可行性（能够执行）。可逆性不是算法的基本特性。",
                    "knowledge_points": ["算法与流程图"],
                    "difficulty": 1
                },
                {
                    "order_index": 2,
                    "question_type": "choice",
                    "title": "流程图符号",
                    "question_text": "在流程图中，菱形符号表示什么？",
                    "options": ["A. 开始/结束", "B. 输入/输出", "C. 处理", "D. 判断"],
                    "correct_answer": "D",
                    "explanation": "流程图中：椭圆表示开始/结束，平行四边形表示输入/输出，矩形表示处理，菱形表示判断。",
                    "knowledge_points": ["算法与流程图"],
                    "difficulty": 1
                },
                {
                    "order_index": 3,
                    "question_type": "choice",
                    "title": "常见语法错误",
                    "question_text": "以下哪个是C语言的语法错误？",
                    "options": ["A. int a = 10;", "B. int a = 10", "C. a = 10;", "D. printf(\"%d\", a);"],
                    "correct_answer": "B",
                    "explanation": "C语言中每条语句必须以分号结尾。选项B缺少分号，是语法错误。",
                    "knowledge_points": ["常见错误分析"],
                    "difficulty": 1
                },
                {
                    "order_index": 4,
                    "question_type": "choice",
                    "title": "逻辑错误",
                    "question_text": "程序能正常运行但结果不正确，这种错误称为什么错误？",
                    "options": ["A. 语法错误", "B. 逻辑错误", "C. 运行错误", "D. 编译错误"],
                    "correct_answer": "B",
                    "explanation": "语法错误是违反语言规则的错误，编译器会报错。程序能运行但结果不对是逻辑错误，程序本身没有语法问题。",
                    "knowledge_points": ["常见错误分析"],
                    "difficulty": 1
                },
                {
                    "order_index": 5,
                    "question_type": "choice",
                    "title": "编程风格",
                    "question_text": "以下哪种做法不符合良好的编程风格？",
                    "options": [
                        "A. 代码缩进一致",
                        "B. 变量名有意义",
                        "C. 不写注释",
                        "D. 合理使用空行"
                    ],
                    "correct_answer": "C",
                    "explanation": "良好的编程风格要求：代码缩进一致、变量名有意义、合理使用空行、适当添加注释。不写注释不符合良好编程风格。",
                    "knowledge_points": ["编程风格"],
                    "difficulty": 1
                }
            ]
        }
    ]
}


async def clear_chapter_1():
    """删除第一章的所有数据"""
    from sqlalchemy import select, delete, text

    async with AsyncSessionLocal() as db:
        await db.execute(text("PRAGMA foreign_keys=OFF"))

        try:
            result = await db.execute(select(Course).where(Course.code == "C"))
            course = result.scalar_one_or_none()

            if not course:
                print("C语言课程不存在")
                return None

            result = await db.execute(
                select(Chapter).where(Chapter.course_id == course.id).where(Chapter.order_index == 1)
            )
            chapter = result.scalar_one_or_none()

            if not chapter:
                print("第一章不存在")
                return course

            result = await db.execute(select(Section).where(Section.chapter_id == chapter.id))
            sections = result.scalars().all()
            section_ids = [s.id for s in sections]

            print(f"找到并删除第1章，包含 {len(sections)} 个小节...")

            for section_id in section_ids:
                await db.execute(text("DELETE FROM section_mastery WHERE section_id = :sid"), {"sid": section_id})
                await db.execute(text("DELETE FROM knowledge_point_mastery WHERE section_id = :sid"), {"sid": section_id})
                await db.execute(text("DELETE FROM section_knowledge_points WHERE section_id = :sid"), {"sid": section_id})
                await db.execute(text("DELETE FROM section_base_questions WHERE section_id = :sid"), {"sid": section_id})

            await db.execute(text("DELETE FROM answer_history WHERE chapter_id = :cid"), {"cid": chapter.id})
            await db.execute(text("DELETE FROM mastery_exercise_progress WHERE chapter_id = :cid"), {"cid": chapter.id})
            await db.execute(text("DELETE FROM wrong_questions WHERE chapter_id = :cid"), {"cid": chapter.id})
            await db.execute(text("DELETE FROM chapter_mastery WHERE chapter_id = :cid"), {"cid": chapter.id})
            await db.execute(text("DELETE FROM exercises WHERE chapter_id = :cid"), {"cid": chapter.id})

            for section in sections:
                await db.delete(section)
            await db.delete(chapter)

            await db.commit()
            print("第1章已删除")

        finally:
            await db.execute(text("PRAGMA foreign_keys=ON"))

        return course


async def generate_chapter_1():
    """生成第一章所有小节的内容"""
    course = await clear_chapter_1()
    if not course:
        return

    async with AsyncSessionLocal() as db:
        # 创建第一章
        chapter = Chapter(
            course_id=course.id,
            title=CHAPTER_1_DATA["chapter"]["title"],
            description=CHAPTER_1_DATA["chapter"]["description"],
            content=CHAPTER_1_DATA["chapter"]["content"],
            order_index=CHAPTER_1_DATA["chapter"]["order_index"],
            estimated_minutes=CHAPTER_1_DATA["chapter"]["estimated_minutes"],
            difficulty_tags=CHAPTER_1_DATA["chapter"]["difficulty_tags"],
            skill_tags=CHAPTER_1_DATA["chapter"]["skill_tags"]
        )
        db.add(chapter)
        await db.flush()
        print(f"创建章节: {chapter.title} (ID: {chapter.id})")

        total_kp = 0
        total_q = 0

        # 创建小节
        for section_data in CHAPTER_1_DATA["sections"]:
            section = Section(
                chapter_id=chapter.id,
                title=section_data["title"],
                description=section_data["description"],
                order_index=section_data["order_index"],
                estimated_minutes=section_data["estimated_minutes"]
            )
            db.add(section)
            await db.flush()
            print(f"  创建小节: {section.title} (ID: {section.id})")

            # 创建知识点
            for kp_data in section_data["knowledge_points"]:
                kp = SectionKnowledgePoint(
                    section_id=section.id,
                    name=kp_data["name"],
                    order_index=kp_data["order_index"],
                    content=kp_data["content"],
                    summary=kp_data["summary"],
                    code_example=kp_data["code_example"],
                    code_language=kp_data.get("code_language", "c"),
                    code_explanation=kp_data["code_explanation"],
                    difficulty=kp_data["difficulty"],
                    importance=kp_data["importance"],
                    related_points=kp_data["related_points"],
                    tips=kp_data["tips"],
                    common_mistakes=kp_data["common_mistakes"]
                )
                db.add(kp)
            total_kp += len(section_data["knowledge_points"])
            print(f"    创建 {len(section_data['knowledge_points'])} 个知识点")

            # 创建测试题
            for q_data in section_data["base_questions"]:
                question = SectionBaseQuestion(
                    section_id=section.id,
                    chapter_id=chapter.id,
                    question_source="base",
                    order_index=q_data["order_index"],
                    question_type=q_data["question_type"],
                    title=q_data["title"],
                    question_text=q_data["question_text"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation"),
                    knowledge_points=q_data["knowledge_points"],
                    difficulty=q_data["difficulty"]
                )
                db.add(question)
            total_q += len(section_data["base_questions"])
            print(f"    创建 {len(section_data['base_questions'])} 道测试题")

        await db.commit()
        print(f"\n第一章内容生成完成！")
        print(f"  - 章节: 1个")
        print(f"  - 小节: {len(CHAPTER_1_DATA['sections'])}个")
        print(f"  - 知识点: {total_kp}个")
        print(f"  - 测试题: {total_q}道")


if __name__ == "__main__":
    asyncio.run(generate_chapter_1())
