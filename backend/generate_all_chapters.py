"""Generate all chapters content for C language course (without questions)"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint


# 全部9章内容数据
ALL_CHAPTERS_DATA = [
    # ========== 第1章 ==========
    {
        "chapter": {
            "title": "简单C程序设计",
            "description": "学习C语言的基本概念，包括程序结构、数据类型、输入输出等基础知识",
            "content": "本章介绍C语言的基本概念，包括：C程序的基本结构、基本数据类型、变量与常量、格式化输入输出。通过本章学习，学生能够编写简单的C程序。",
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
- 常量全大写""",
                        "summary": "标识符由字母、数字、下划线组成，必须以字母或下划线开头",
                        "code_example": """// 合法的标识符
int maxScore = 100;
int student_age;

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
| 定义方式 | 数据类型 变量名 | const/宏定义 |""",
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
| 说明符 | 含义 |
|--------|------|
| %d | 输出整数 |
| %f | 输出浮点数 |
| %.2f | 输出保留2位小数 |
| %c | 输出字符 |
| %s | 输出字符串 |
| %% | 输出百分号% |

### 转义字符
| 字符 | 含义 |
|------|------|
| \\n | 换行 |
| \\t | 制表符 |
| \\\" | 双引号 |
| \\\\ | 反斜杠 |""",
                        "summary": "printf用于格式化输出，支持多种格式说明符和转义字符",
                        "code_example": """#include <stdio.h>

int main() {
    int age = 20;
    float height = 175.5f;
    char grade = 'A';

    printf("年龄：%d岁\\n", age);
    printf("身高：%.1fcm\\n", height);
    printf("等级：%c\\n", grade);

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

### 流程图符号
| 符号 | 名称 | 用途 |
|------|------|------|
| 椭圆 | 开始/结束 | 表示程序开始或结束 |
| 平行四边形 | 输入/输出 | 表示输入或输出操作 |
| 矩形 | 处理 | 表示处理或运算 |
| 菱形 | 判断 | 表示条件判断 |
| 箭头 | 流程线 | 表示执行方向 |""",
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

### 伪代码示例
```
输入 a, b
如果 a > b
    输出 a
否则
    输出 b
```""",
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

**忘记分号**
```c
int a = 10  // 错误：缺少分号
```

**变量未声明**
```c
x = 10;  // 错误：x未声明
int x = 10;  // 正确
```

**括号不匹配**
```c
if (a > b {  // 错误：缺少右括号
```

### 逻辑错误
程序能正常运行，但结果不正确。

**整数除法问题**
```c
// 错误：整数除法
int avg = a + b / 2;

// 正确：先加后除
int avg = (a + b) / 2;
```

### 常见错误汇总
| 错误类型 | 例子 | 解决方法 |
|----------|------|----------|
| 少分号 | `int a = 10` | 检查每条语句 |
| 括号不匹配 | `if (a > b` | 使用IDE括号匹配 |
| 整数除法 | `a / b` | 强制转换或用浮点 |""",
                        "summary": "常见错误分为语法错误和逻辑错误，需要仔细排查",
                        "code_example": """// 常见错误示例
// 错误1：忘记分号
int a = 10  // 缺少分号

// 错误2：整数除法
int avg = 5 / 2;  // 结果是2，不是2.5

// 正确写法
int a = 10;
int avg = (5 + 0) / 2;""",
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
```

**3. 添加注释**
```c
// 计算圆的面积
double radius = 5.0;
double area = 3.14159 * radius * radius;
```

### 编程风格建议
- 缩进使用4个空格或Tab
- 每行不超过80个字符
- 函数之间加空行
- 变量名要有意义
- 合理添加注释""",
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
                ]
            }
        ]
    },
    # ========== 第2章 ==========
    {
        "chapter": {
            "title": "选择控制结构与应用",
            "description": "学习C语言的选择控制语句，包括关系运算、条件语句和switch语句",
            "content": "本章介绍C语言的选择控制结构，包括关系运算符、逻辑运算符、if语句和switch语句。通过本章学习，学生能够编写具有选择结构的程序。",
            "order_index": 2,
            "estimated_minutes": 180,
            "difficulty_tags": ["基础", "选择结构"],
            "skill_tags": ["if语句", "switch语句", "关系运算"]
        },
        "sections": [
            {
                "title": "关系运算与逻辑运算",
                "description": "关系运算符、逻辑运算符及表达式",
                "order_index": 1,
                "estimated_minutes": 20,
                "knowledge_points": [
                    {
                        "name": "关系运算符",
                        "order_index": 1,
                        "content": """## 关系运算符

关系运算符用于比较两个值的大小关系，返回真(1)或假(0)。

### 运算符列表
| 运算符 | 含义 | 示例 |
|--------|------|------|
| > | 大于 | a > b |
| < | 小于 | a < b |
| >= | 大于等于 | a >= b |
| <= | 小于等于 | a <= b |
| == | 等于 | a == b |
| != | 不等于 | a != b |

### 示例
```c
int a = 10, b = 20;
printf("%d\\n", a > b);   // 输出0（假）
printf("%d\\n", a < b);   // 输出1（真）
printf("%d\\n", a == 10); // 输出1（真）
```

### 注意事项
- `==` 是比较运算符，不是赋值运算符
- 关系运算的结果是整数1（真）或0（假）""",
                        "summary": "关系运算符用于比较大小，包括>,<,>=,<=,==,!=",
                        "code_example": """int a = 10, b = 20;
printf("a > b = %d\\n", a > b);   // 0
printf("a < b = %d\\n", a < b);   // 1
printf("a == 10 = %d\\n", a == 10); // 1
printf("a != b = %d\\n", a != b);   // 1""",
                        "code_language": "c",
                        "code_explanation": "演示了各种关系运算符的使用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["逻辑运算符", "if语句"],
                        "tips": ["==是比较，不是赋值", "注意=和==的区别"],
                        "common_mistakes": ["混淆=和==", "把比较写成赋值"]
                    },
                    {
                        "name": "逻辑运算符",
                        "order_index": 2,
                        "content": """## 逻辑运算符

逻辑运算符用于组合多个条件。

### 运算符列表
| 运算符 | 含义 | 说明 |
|--------|------|------|
| && | 逻辑与 | 所有条件都为真时结果为真 |
| \\|\\| | 逻辑或 | 任意一个条件为真时结果为真 |
| ! | 逻辑非 | 取反，真变假，假变真 |

### 运算规则
- **&&（与）**：两边都为真结果才为真
  - 1 && 1 = 1, 1 && 0 = 0, 0 && 0 = 0
- **||（或）**：两边有一个为真结果就为真
  - 1 || 1 = 1, 1 || 0 = 1, 0 || 0 = 0
- **!（非）**：真变假，假变真
  - !1 = 0, !0 = 1

### 示例
```c
int a = 10, b = 20;
printf("%d\\n", a > 0 && b > 0);  // 1（都大于0）
printf("%d\\n", a > 0 || b < 0);  // 1（至少一个大于0）
printf("%d\\n", !(a > 0));         // 0（非真）""",
                        "summary": "逻辑运算符包括&&（与）、||（或）、!（非）",
                        "code_example": """int a = 10, b = 20;
printf("a>0 && b>0 = %d\\n", a > 0 && b > 0);  // 1
printf("a>0 || b<0 = %d\\n", a > 0 || b < 0);  // 1
printf("!(a>0) = %d\\n", !(a > 0));             // 0""",
                        "code_language": "c",
                        "code_explanation": "演示了逻辑运算符的使用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["关系运算符", "if语句"],
                        "tips": ["注意短路求值", "&&优先级高于||"],
                        "common_mistakes": ["混淆&和&&", "忽略运算符优先级"]
                    },
                    {
                        "name": "if语句基本形式",
                        "order_index": 3,
                        "content": """## if语句基本形式

### 单分支if语句
```c
if (条件) {
    // 条件为真时执行
}
```

### 双分支if-else语句
```c
if (条件) {
    // 条件为真时执行
} else {
    // 条件为假时执行
}
```

### 示例
```c
int num = 10;
if (num > 0) {
    printf("正数\\n");
} else {
    printf("非正数\\n");
}
```

### 注意事项
- 条件表达式必须用括号括起来
- 推荐使用 `{ }` 包裹多条语句""",
                        "summary": "if语句用于条件判断，有单分支和双分支两种形式",
                        "code_example": """int num = 10;
if (num > 0) {
    printf("正数\\n");
} else {
    printf("非正数\\n");
}""",
                        "code_language": "c",
                        "code_explanation": "演示了if-else双分支语句的使用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["关系运算符", "逻辑运算符"],
                        "tips": ["条件表达式非零即为真", "推荐使用大括号"],
                        "common_mistakes": ["忘记在条件后加分号", "else匹配错误"]
                    }
                ]
            },
            {
                "title": "if语句嵌套与应用",
                "description": "if语句的嵌套、多分支if语句及实用例",
                "order_index": 2,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "if语句嵌套",
                        "order_index": 1,
                        "content": """## if语句嵌套

嵌套是指在if语句的执行分支中再包含if语句。

### 嵌套if语句
```c
if (条件1) {
    if (条件2) {
        // 条件1和条件2都为真
    } else {
        // 条件1为真，条件2为假
    }
} else {
    // 条件1为假
}
```

### 示例：判断成绩等级
```c
int score = 85;
if (score >= 90) {
    printf("优秀\\n");
} else if (score >= 80) {
    printf("良好\\n");
} else if (score >= 60) {
    printf("及格\\n");
} else {
    printf("不及格\\n");
}
```""",
                        "summary": "if语句可以嵌套使用，实现多条件判断",
                        "code_example": """int score = 85;
if (score >= 90) {
    printf("优秀\\n");
} else if (score >= 80) {
    printf("良好\\n");
} else if (score >= 60) {
    printf("及格\\n");
} else {
    printf("不及格\\n");
}""",
                        "code_language": "c",
                        "code_explanation": "演示了多分支if语句判断成绩等级",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["if语句基本形式", "关系运算符"],
                        "tips": ["注意else的匹配规则", "层次要清晰"],
                        "common_mistakes": ["else匹配错误", "条件顺序错误"]
                    },
                    {
                        "name": "条件运算符",
                        "order_index": 2,
                        "content": """## 条件运算符

条件运算符是if-else的简化形式。

### 语法
```c
条件 ? 表达式1 : 表达式2
```

### 说明
- 如果条件为真，返回表达式1的值
- 如果条件为假，返回表达式2的值

### 示例
```c
int a = 10, b = 20;
// 求最大值
int max = (a > b) ? a : b;

// 求绝对值
int x = -5;
int abs_x = (x > 0) ? x : -x;
```

### 注意事项
- 条件运算符是C语言中唯一的三目运算符
- 表达式1和表达式2类型应一致""",
                        "summary": "条件运算符(?:)是if-else的简化形式",
                        "code_example": """int a = 10, b = 20;
// 求最大值
int max = (a > b) ? a : b;
printf("最大值：%d\\n", max);

// 求绝对值
int x = -5;
int abs_x = (x > 0) ? x : -x;
printf("绝对值：%d\\n", abs_x);""",
                        "code_language": "c",
                        "code_explanation": "演示了条件运算符求最大值和绝对值",
                        "difficulty": 1,
                        "importance": 4,
                        "related_points": ["if语句基本形式"],
                        "tips": ["简化if-else赋值语句", "注意表达式类型一致"],
                        "common_mistakes": ["过度使用嵌套", "优先级理解错误"]
                    }
                ]
            },
            {
                "title": "switch语句",
                "description": "switch语句的表达形式及其使用方法和简单的应用实例",
                "order_index": 3,
                "estimated_minutes": 20,
                "knowledge_points": [
                    {
                        "name": "switch语句基础",
                        "order_index": 1,
                        "content": """## switch语句基础

switch语句用于多分支选择，根据表达式的值选择执行不同的代码块。

### 语法
```c
switch (表达式) {
    case 常量1:
        // 语句块1
        break;
    case 常量2:
        // 语句块2
        break;
    default:
        // 默认语句块
}
```

### 示例
```c
int grade = 2;
switch (grade) {
    case 1:
        printf("大一\\n");
        break;
    case 2:
        printf("大二\\n");
        break;
    case 3:
        printf("大三\\n");
        break;
    default:
        printf("大四及以上\\n");
}
```

### 注意事项
- 表达式和case常量必须是整型或字符型
- break语句用于跳出switch
- default可选""",
                        "summary": "switch语句用于多分支选择，根据表达式值选择执行代码",
                        "code_example": """int grade = 2;
switch (grade) {
    case 1:
        printf("大一\\n");
        break;
    case 2:
        printf("大二\\n");
        break;
    case 3:
        printf("大三\\n");
        break;
    default:
        printf("大四及以上\\n");
}""",
                        "code_language": "c",
                        "code_explanation": "演示了switch语句根据年级输出对应描述",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["if语句基本形式"],
                        "tips": ["忘记break会贯穿执行", "case常量要唯一"],
                        "common_mistakes": ["忘记break语句", "忘记default分支"]
                    },
                    {
                        "name": "switch语句深入",
                        "order_index": 2,
                        "content": """## switch语句深入

### case穿透
如果case中没有break语句，会继续执行后面的case。

```c
switch (score / 10) {
    case 10:
    case 9:
        printf("优秀\\n");
        break;
    case 8:
    case 7:
        printf("良好\\n");
        break;
    default:
        printf("继续努力\\n");
}
```

### 注意事项
- case后的值必须是常量表达式
- 不要忘记在每个case后加break
- 可以用case穿透来实现多个值执行同一代码块""",
                        "summary": "switch语句中break用于跳出，缺少break会导致case穿透",
                        "code_example": """int score = 85;
switch (score / 10) {
    case 10:
    case 9:
        printf("优秀\\n");
        break;
    case 8:
    case 7:
        printf("良好\\n");
        break;
    case 6:
        printf("及格\\n");
        break;
    default:
        printf("不及格\\n");
}""",
                        "code_language": "c",
                        "code_explanation": "演示了case穿透实现成绩等级判断",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["switch语句基础"],
                        "tips": ["利用case穿透简化代码", "注意break的作用"],
                        "common_mistakes": ["忘记break导致错误", "case值不是常量"]
                    }
                ]
            }
        ]
    },
    # ========== 第3章 ==========
    {
        "chapter": {
            "title": "循环结构及应用",
            "description": "学习C语言的循环控制语句，包括for、while、do-while循环及循环嵌套",
            "content": "本章介绍C语言的循环结构，包括for循环、while循环、do-while循环以及循环嵌套。通过本章学习，学生能够编写具有循环结构的程序。",
            "order_index": 3,
            "estimated_minutes": 180,
            "difficulty_tags": ["基础", "循环结构"],
            "skill_tags": ["for循环", "while循环", "循环嵌套"]
        },
        "sections": [
            {
                "title": "for循环",
                "description": "for循环的表达形式、流程图绘制方法及应用实例",
                "order_index": 1,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "for循环基本结构",
                        "order_index": 1,
                        "content": """## for循环基本结构

for循环是C语言中最常用的循环结构。

### 语法
```c
for (初始化; 条件; 更新) {
    // 循环体
}
```

### 执行流程
1. 执行初始化（只执行一次）
2. 判断条件
3. 如果条件为真，执行循环体
4. 执行更新
5. 回到第2步

### 示例：计算1到100的和
```c
int sum = 0;
for (int i = 1; i <= 100; i++) {
    sum += i;
}
printf("sum = %d\\n", sum);
```

### 注意事项
- 三个表达式都可以省略，但分号不能省略
- 初始化只执行一次""",
                        "summary": "for循环是最常用的循环结构，由初始化、条件、更新三部分组成",
                        "code_example": """#include <stdio.h>

int main() {
    int sum = 0;
    for (int i = 1; i <= 100; i++) {
        sum += i;
    }
    printf("1+2+...+100 = %d\\n", sum);
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了用for循环计算1到100的和",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["while循环", "循环嵌套"],
                        "tips": ["注意循环变量的取值范围", "避免死循环"],
                        "common_mistakes": ["循环变量作用域错误", "死循环"]
                    },
                    {
                        "name": "for循环变体",
                        "order_index": 2,
                        "content": """## for循环变体

### 多个循环变量
```c
for (int i = 0, j = 10; i < j; i++, j--) {
    printf("%d %d\\n", i, j);
}
```

### 省略部分表达式
```c
int i = 0;
for (; i < 10; i++) {  // 省略初始化
    printf("%d ", i);
}

for (int i = 0; i < 10; ) {  // 省略更新
    printf("%d ", i++);
}
```

### 死循环
```c
for (;;) {  // 无限循环
    // 需要在循环内使用break退出
}
```""",
                        "summary": "for循环的三个表达式都可以省略或使用多个",
                        "code_example": """// 多个循环变量
for (int i = 0, j = 10; i < j; i++, j--) {
    printf("%d %d\\n", i, j);
}

// 死循环
int count = 0;
for (;;) {
    count++;
    if (count >= 10) break;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了for循环的多种变体",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["for循环基本结构"],
                        "tips": ["死循环需要break退出", "注意更新表达式"],
                        "common_mistakes": ["死循环", "更新表达式缺失"]
                    }
                ]
            },
            {
                "title": "while循环",
                "description": "while循环的表达形式、流程图绘制方法及应用实例",
                "order_index": 2,
                "estimated_minutes": 20,
                "knowledge_points": [
                    {
                        "name": "while循环",
                        "order_index": 1,
                        "content": """## while循环

while循环是前测试循环，先判断条件再执行循环体。

### 语法
```c
while (条件) {
    // 循环体
}
```

### 执行流程
1. 判断条件
2. 如果条件为真，执行循环体
3. 回到第1步

### 示例：计算阶乘
```c
int n = 5;
int factorial = 1;
int i = 1;
while (i <= n) {
    factorial *= i;
    i++;
}
printf("%d! = %d\\n", n, factorial);
```

### 注意事项
- 循环体中必须包含改变条件的语句
- 避免死循环""",
                        "summary": "while循环是前测试循环，先判断条件后执行",
                        "code_example": """#include <stdio.h>

int main() {
    int n = 5, factorial = 1, i = 1;
    while (i <= n) {
        factorial *= i;
        i++;
    }
    printf("%d! = %d\\n", n, factorial);
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了用while循环计算5的阶乘",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["for循环", "do-while循环"],
                        "tips": ["先判断后执行", "循环体中必须更新条件"],
                        "common_mistakes": ["死循环", "忘记更新条件变量"]
                    },
                    {
                        "name": "do-while循环",
                        "order_index": 2,
                        "content": """## do-while循环

do-while循环是后测试循环，先执行循环体再判断条件。

### 语法
```c
do {
    // 循环体
} while (条件);
```

### 执行流程
1. 执行循环体
2. 判断条件
3. 如果条件为真，回到第1步

### 与while的区别
- while：先判断后执行，循环体可能一次都不执行
- do-while：先执行后判断，循环体至少执行一次

### 示例
```c
int i = 1;
do {
    printf("%d ", i);
    i++;
} while (i <= 10);
```""",
                        "summary": "do-while循环是后测试循环，循环体至少执行一次",
                        "code_example": """#include <stdio.h>

int main() {
    int i = 1;
    do {
        printf("%d ", i);
        i++;
    } while (i <= 10);
    printf("\\n");
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了do-while循环输出1到10",
                        "difficulty": 1,
                        "importance": 4,
                        "related_points": ["while循环", "for循环"],
                        "tips": ["至少执行一次", "注意while后有分号"],
                        "common_mistakes": ["忘记while后分号", "与while混淆"]
                    }
                ]
            },
            {
                "title": "循环嵌套与控制",
                "description": "循环嵌套、循环控制语句break和continue",
                "order_index": 3,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "循环嵌套",
                        "order_index": 1,
                        "content": """## 循环嵌套

循环嵌套是一个循环内部包含另一个循环。

### 语法
```c
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
        // 内层循环体
    }
}
```

### 示例：打印九九乘法表
```c
for (int i = 1; i <= 9; i++) {
    for (int j = 1; j <= i; j++) {
        printf("%d*%d=%2d ", j, i, i*j);
    }
    printf("\\n");
}
```

### 注意事项
- 外层循环执行一次，内层循环执行完整一轮
- 注意循环变量的作用域""",
                        "summary": "循环嵌套是外层循环包含内层循环，用于处理二维结构",
                        "code_example": """#include <stdio.h>

int main() {
    for (int i = 1; i <= 9; i++) {
        for (int j = 1; j <= i; j++) {
            printf("%d*%d=%2d ", j, i, i*j);
        }
        printf("\\n");
    }
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了用嵌套循环打印九九乘法表",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["for循环", "while循环"],
                        "tips": ["外层控制行数，内层控制列数", "注意循环变量不要冲突"],
                        "common_mistakes": ["循环变量冲突", "内外层循环条件错误"]
                    },
                    {
                        "name": "break与continue",
                        "order_index": 2,
                        "content": """## break与continue

### break语句
- 跳出当前循环
- 只能跳出一层循环
- 用于提前结束循环

```c
for (int i = 1; i <= 10; i++) {
    if (i == 5) {
        break;  // 当i等于5时跳出循环
    }
    printf("%d ", i);  // 输出1 2 3 4
}
```

### continue语句
- 跳过本次循环的剩余部分
- 进入下一次循环

```c
for (int i = 1; i <= 5; i++) {
    if (i == 3) {
        continue;  // 跳过输出3
    }
    printf("%d ", i);  // 输出1 2 4 5
}
```

### 两者的区别
| 语句 | 作用 | 适用范围 |
|------|------|----------|
| break | 跳出循环 | switch、for、while、do-while |
| continue | 跳过本次循环 | for、while、do-while |""",
                        "summary": "break用于跳出循环，continue用于跳过本次循环",
                        "code_example": """#include <stdio.h>

int main() {
    // break示例
    printf("break示例：");
    for (int i = 1; i <= 5; i++) {
        if (i == 3) break;
        printf("%d ", i);  // 输出1 2
    }
    printf("\\n");

    // continue示例
    printf("continue示例：");
    for (int i = 1; i <= 5; i++) {
        if (i == 3) continue;
        printf("%d ", i);  // 输出1 2 4 5
    }
    printf("\\n");

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了break和continue的区别",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["for循环", "while循环"],
                        "tips": ["break跳出一层循环", "continue进入下一次循环"],
                        "common_mistakes": ["混淆break和continue", "break只能跳出一层"]
                    }
                ]
            }
        ]
    },
    # ========== 第4章 ==========
    {
        "chapter": {
            "title": "模块化设计与应用",
            "description": "学习C语言的模块化程序设计，包括函数定义、调用和预处理指令",
            "content": "本章介绍C语言的模块化程序设计，包括函数的定义、声明、调用以及预处理指令。通过本章学习，学生能够编写结构化的程序。",
            "order_index": 4,
            "estimated_minutes": 180,
            "difficulty_tags": ["基础", "函数"],
            "skill_tags": ["函数定义", "函数调用", "预处理指令"]
        },
        "sections": [
            {
                "title": "函数基础",
                "description": "函数的定义、声明、使用",
                "order_index": 1,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "函数定义",
                        "order_index": 1,
                        "content": """## 函数定义

函数是一段完成特定功能的代码块，可以重复调用。

### 语法
```c
返回类型 函数名(参数列表) {
    // 函数体
    return 返回值;
}
```

### 示例：求最大值函数
```c
int max(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}
```

### 函数的组成
- **返回类型**：函数返回值的类型
- **函数名**：标识符，用于调用
- **参数列表**：函数接受的输入
- **函数体**：实现功能的代码""",
                        "summary": "函数定义包括返回类型、函数名、参数列表和函数体",
                        "code_example": """#include <stdio.h>

int max(int a, int b) {
    return (a > b) ? a : b;
}

int main() {
    int result = max(10, 20);
    printf("最大值：%d\\n", result);
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了定义和调用max函数",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["函数调用", "函数声明"],
                        "tips": ["函数要先定义后使用", "注意返回类型"],
                        "common_mistakes": ["忘记return语句", "返回类型不匹配"]
                    },
                    {
                        "name": "函数声明",
                        "order_index": 2,
                        "content": """## 函数声明

函数声明告诉编译器函数的存在及其签名。

### 为什么需要声明
- 如果函数定义在调用之后，需要先声明
- 函数的声明也称为函数原型

### 语法
```c
返回类型 函数名(参数列表);
```

### 示例
```c
int max(int a, int b);  // 函数声明

int main() {
    int result = max(10, 20);  // 调用
    return 0;
}

int max(int a, int b) {  // 函数定义
    return (a > b) ? a : b;
}
```""",
                        "summary": "函数声明用于在调用前告诉编译器函数的存在",
                        "code_example": """#include <stdio.h>

int max(int a, int b);  // 函数声明

int main() {
    int result = max(10, 20);
    printf("最大值：%d\\n", result);
    return 0;
}

int max(int a, int b) {
    return (a > b) ? a : b;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了函数声明和定义的分离",
                        "difficulty": 1,
                        "importance": 4,
                        "related_points": ["函数定义", "函数调用"],
                        "tips": ["声明只是告诉编译器", "参数名可以省略"],
                        "common_mistakes": ["忘记函数声明", "声明和定义不一致"]
                    },
                    {
                        "name": "函数调用",
                        "order_index": 3,
                        "content": """## 函数调用

函数调用是执行已定义函数的过程。

### 语法
```c
函数名(实参列表);
```

### 示例
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int sum = add(10, 20);  // 函数调用
    printf("sum = %d\\n", sum);
    return 0;
}
```

### 参数传递
- 形参：函数定义时的参数
- 实参：函数调用时的参数
- 值传递：实参的值复制给形参""",
                        "summary": "函数调用通过函数名和实参列表执行函数",
                        "code_example": """#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main() {
    int sum = add(10, 20);
    printf("10 + 20 = %d\\n", sum);
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了add函数的定义和调用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["函数定义", "参数传递"],
                        "tips": ["实参和形参要匹配", "注意参数顺序"],
                        "common_mistakes": ["实参形参类型不匹配", "参数顺序错误"]
                    }
                ]
            },
            {
                "title": "预处理指令",
                "description": "预处理指令的使用方法",
                "order_index": 2,
                "estimated_minutes": 20,
                "knowledge_points": [
                    {
                        "name": "宏定义",
                        "order_index": 1,
                        "content": """## 宏定义

宏定义是预处理指令，用符号代替常量或代码片段。

### 无参宏
```c
#define 宏名 常量
#define PI 3.14159
#define MAX_SIZE 100
```

### 带参宏
```c
#define 宏名(参数) 表达式
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
```

### 注意事项
- 宏替换在编译前进行
- 宏没有类型检查
- 建议加括号避免优先级问题

### 优点
- 提高代码可读性
- 方便批量修改
- 提高执行效率""",
                        "summary": "宏定义用于定义常量和代码片段，在编译前替换",
                        "code_example": """#include <stdio.h>

#define PI 3.14159
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

int main() {
    printf("PI = %.5f\\n", PI);
    printf("5的平方 = %d\\n", SQUARE(5));
    printf("较大值 = %d\\n", MAX(10, 20));
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了无参宏和带参宏的使用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["变量与常量", "条件编译"],
                        "tips": ["宏名通常全大写", "表达式加括号"],
                        "common_mistakes": ["忘记括号导致错误", "宏不是函数"]
                    },
                    {
                        "name": "条件编译",
                        "order_index": 2,
                        "content": """## 条件编译

条件编译根据条件选择性地编译代码。

### 常用形式
```c
// 如果定义了宏，编译这段代码
#ifdef DEBUG
    printf("调试信息\\n");
#endif

// 如果条件为真，编译这段代码
#if 0
    printf("这段代码不会编译\\n");
#endif

// 防止头文件重复包含
#ifndef HEADER_H
#define HEADER_H
// 头文件内容
#endif
```

### 用途
- 调试代码
- 跨平台开发
- 防止头文件重复包含""",
                        "summary": "条件编译根据条件选择性地编译代码部分",
                        "code_example": """#include <stdio.h>

#define DEBUG 1

int main() {
    #ifdef DEBUG
        printf("调试模式开启\\n");
    #endif

    #if 0
        printf("这段代码不会编译\\n");
    #endif

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了条件编译的几种形式",
                        "difficulty": 1,
                        "importance": 4,
                        "related_points": ["宏定义"],
                        "tips": ["用于调试和跨平台", "防止头文件重复包含"],
                        "common_mistakes": ["#if和#ifdef混淆", "缺少#endif"]
                    }
                ]
            }
        ]
    },
    # ========== 第5章 ==========
    {
        "chapter": {
            "title": "相同数据类型集合",
            "description": "学习C语言的数组和字符串，包括一维数组、二维数组和字符数组",
            "content": "本章介绍C语言的数组和字符串，包括一维数组、二维数组、字符数组与字符串。通过本章学习，学生能够处理批量数据。",
            "order_index": 5,
            "estimated_minutes": 180,
            "difficulty_tags": ["基础", "数组"],
            "skill_tags": ["一维数组", "二维数组", "字符串"]
        },
        "sections": [
            {
                "title": "一维数组",
                "description": "一维数组的存储形式、定义、初始化及使用方法",
                "order_index": 1,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "一维数组基础",
                        "order_index": 1,
                        "content": """## 一维数组基础

数组是相同类型数据的集合，用连续内存存储。

### 定义
```c
类型 数组名[长度];
int scores[10];      // 定义10个整数的数组
char name[20];      // 定义20个字符的数组
```

### 初始化
```c
// 完全初始化
int a[5] = {1, 2, 3, 4, 5};

// 部分初始化
int b[5] = {1, 2};  // b[0]=1, b[1]=2, b[2]=0, b[3]=0, b[4]=0

// 自动确定长度
int c[] = {1, 2, 3, 4, 5};  // 长度为5
```

### 数组下标
- 从0开始，最大为长度-1
- scores[0] 第一个元素
- scores[9] 第十个元素""",
                        "summary": "数组是相同类型数据的集合，下标从0开始",
                        "code_example": """#include <stdio.h>

int main() {
    int scores[5] = {90, 85, 77, 92, 88};

    // 访问数组元素
    printf("第一个成绩：%d\\n", scores[0]);
    printf("第三个成绩：%d\\n", scores[2]);

    // 遍历数组
    for (int i = 0; i < 5; i++) {
        printf("scores[%d] = %d\\n", i, scores[i]);
    }

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了一维数组的定义、初始化和访问",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["数组遍历", "数组作为函数参数"],
                        "tips": ["下标从0开始", "注意数组长度"],
                        "common_mistakes": ["数组下标越界", "混淆长度和下标"]
                    },
                    {
                        "name": "数组遍历与操作",
                        "order_index": 2,
                        "content": """## 数组遍历与操作

### 遍历数组
```c
int a[5] = {1, 2, 3, 4, 5};

// for循环遍历
for (int i = 0; i < 5; i++) {
    printf("%d ", a[i]);
}
```

### 求和与平均值
```c
int a[5] = {90, 85, 77, 92, 88};
int sum = 0;
for (int i = 0; i < 5; i++) {
    sum += a[i];
}
double avg = sum / 5.0;
```

### 查找最大值
```c
int a[5] = {90, 85, 77, 92, 88};
int max = a[0];
for (int i = 1; i < 5; i++) {
    if (a[i] > max) {
        max = a[i];
    }
}
```""",
                        "summary": "数组常用于遍历、求和、查找等操作",
                        "code_example": """#include <stdio.h>

int main() {
    int scores[5] = {90, 85, 77, 92, 88};
    int sum = 0, max = scores[0];

    for (int i = 0; i < 5; i++) {
        sum += scores[i];
        if (scores[i] > max) {
            max = scores[i];
        }
    }

    printf("总分：%d\\n", sum);
    printf("平均分：%.1f\\n", sum / 5.0);
    printf("最高分：%d\\n", max);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了数组的遍历、求和、查找操作",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["一维数组基础"],
                        "tips": ["注意循环边界", "初始化要找最大值"],
                        "common_mistakes": ["循环边界错误", "下标越界"]
                    }
                ]
            },
            {
                "title": "二维数组",
                "description": "二维数组的存储形式、定义、初始化及使用方法",
                "order_index": 2,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "二维数组基础",
                        "order_index": 1,
                        "content": """## 二维数组基础

二维数组是数组的数组，用于表示矩阵或表格数据。

### 定义
```c
类型 数组名[行数][列数];
int matrix[3][4];  // 3行4列的矩阵
```

### 初始化
```c
// 完全初始化
int a[2][3] = {{1, 2, 3}, {4, 5, 6}};

// 部分初始化
int b[2][3] = {{1, 2}, {3, 4}};  // 其余为0

// 按行初始化
int c[][3] = {1, 2, 3, 4, 5, 6};  // 自动计算行数
```

### 访问元素
```c
a[0][0]  // 第一行第一列
a[1][2]  // 第二行第三列""",
                        "summary": "二维数组是按矩阵形式组织的数组，有行和列两个维度",
                        "code_example": """#include <stdio.h>

int main() {
    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};

    // 遍历二维数组
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了二维数组的定义和遍历",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["一维数组"],
                        "tips": ["注意行和列的顺序", "内存按行存储"],
                        "common_mistakes": ["行列下标混淆", "内存越界"]
                    },
                    {
                        "name": "二维数组应用",
                        "order_index": 2,
                        "content": """## 二维数组应用

### 矩阵运算
```c
// 矩阵相加
int a[2][2] = {{1, 2}, {3, 4}};
int b[2][2] = {{5, 6}, {7, 8}};
int c[2][2];

for (int i = 0; i < 2; i++) {
    for (int j = 0; j < 2; j++) {
        c[i][j] = a[i][j] + b[i][j];
    }
}
```

### 行列求和
```c
int a[3][4];
// 求每行的和
for (int i = 0; i < 3; i++) {
    int row_sum = 0;
    for (int j = 0; j < 4; j++) {
        row_sum += a[i][j];
    }
}
```""",
                        "summary": "二维数组常用于矩阵运算、表格数据处理",
                        "code_example": """#include <stdio.h>

int main() {
    int a[2][2] = {{1, 2}, {3, 4}};
    int b[2][2] = {{5, 6}, {7, 8}};
    int c[2][2];

    // 矩阵相加
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            c[i][j] = a[i][j] + b[i][j];
            printf("%d ", c[i][j]);
        }
        printf("\\n");
    }

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了二维数组的矩阵相加运算",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["二维数组基础"],
                        "tips": ["行列嵌套循环", "注意内存布局"],
                        "common_mistakes": ["循环嵌套顺序错误", "内存越界"]
                    }
                ]
            },
            {
                "title": "字符串与字符数组",
                "description": "字符类型的数组、字符串的概念、字符串与字符类型的区别与联系、字符串处理函数",
                "order_index": 3,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "字符串基础",
                        "order_index": 1,
                        "content": """## 字符串基础

字符串是由字符组成的序列，以'\\0'结尾。

### 字符数组表示字符串
```c
char str1[] = "Hello";    // 自动添加\\0
char str2[6] = {'H', 'e', 'l', 'l', 'o', '\\0'};
```

### 字符串结束标志
- '\\0'（ASCII码0）表示字符串结束
- printf等函数依靠'\\0'判断字符串长度

### 注意事项
- 定义时确定长度要留一位给'\\0'
- "Hello"占6个字节（5个字母+1个结束符）""",
                        "summary": "字符串是以\\0结尾的字符数组",
                        "code_example": """#include <stdio.h>

int main() {
    char str1[] = "Hello";
    char str2[6] = {'H', 'e', 'l', 'l', 'o', '\\0'};

    printf("str1: %s\\n", str1);
    printf("str2: %s\\n", str2);

    // 字符串长度（不包括\\0）
    printf("str1长度: %lu\\n", sizeof(str1) - 1);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了字符串的两种定义方式",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["字符数组", "字符串函数"],
                        "tips": ["字符串以\\0结尾", "定义时留一位给结束符"],
                        "common_mistakes": ["忘记\\0结束符", "长度计算错误"]
                    },
                    {
                        "name": "字符串函数",
                        "order_index": 2,
                        "content": """## 字符串函数

C语言提供了一系列字符串处理函数，使用时需要包含<string.h>。

### 常用函数
```c
strlen(s)   // 返回字符串长度（不包括\\0）
strcpy(s1, s2)  // 复制s2到s1
strcat(s1, s2)  // 将s2连接到s1后面
strcmp(s1, s2)   // 比较两个字符串
```

### 示例
```c
char s1[20] = "Hello";
char s2[] = "World";

// 复制
strcpy(s1, "Hi");
printf("%s\\n", s1);

// 连接
strcat(s1, " World");
printf("%s\\n", s1);

// 比较
printf("%d\\n", strcmp("abc", "abc"));  // 0（相等）
printf("%d\\n", strcmp("abc", "abd"));  // -1（abc < abd）
```""",
                        "summary": "字符串函数包括strlen、strcpy、strcat、strcmp等",
                        "code_example": """#include <stdio.h>
#include <string.h>

int main() {
    char s1[20] = "Hello";
    char s2[] = "World";

    printf("原s1: %s\\n", s1);

    strcat(s1, " ");
    strcat(s1, s2);
    printf("连接后: %s\\n", s1);

    printf("长度: %lu\\n", strlen(s1));

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了字符串连接和长度计算",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["字符串基础"],
                        "tips": ["使用前包含string.h", "注意目标字符串长度"],
                        "common_mistakes": ["目标数组长度不够", "混用strcpy和strcat"]
                    }
                ]
            }
        ]
    },
    # ========== 第6章 ==========
    {
        "chapter": {
            "title": "深入模块化设计与应用",
            "description": "学习排序算法、递归调用、指针在函数中的使用",
            "content": "本章深入模块化设计，包括排序算法、递归调用以及指针和数组在函数中的使用。通过本章学习，学生能够编写更复杂的程序。",
            "order_index": 6,
            "estimated_minutes": 180,
            "difficulty_tags": ["进阶", "算法"],
            "skill_tags": ["排序算法", "递归", "指针"]
        },
        "sections": [
            {
                "title": "排序算法",
                "description": "冒泡排序和选择排序",
                "order_index": 1,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "冒泡排序",
                        "order_index": 1,
                        "content": """## 冒泡排序

冒泡排序是一种简单的排序算法，通过反复交换相邻元素将最大值"冒泡"到序列末端。

### 算法步骤
1. 从第一个元素开始，比较相邻的两个元素
2. 如果前一个大于后一个，交换它们
3. 对每一对相邻元素做同样的工作
4. 重复以上步骤，直到没有需要交换的元素

### 时间复杂度
- 平均：O(n²)
- 最坏：O(n²)
- 最好：O(n)

### 示例
```c
int a[] = {64, 34, 25, 12, 22, 11, 90};
int n = 7;

for (int i = 0; i < n - 1; i++) {
    for (int j = 0; j < n - i - 1; j++) {
        if (a[j] > a[j + 1]) {
            // 交换
            int temp = a[j];
            a[j] = a[j + 1];
            a[j + 1] = temp;
        }
    }
}
```""",
                        "summary": "冒泡排序通过相邻元素比较交换，将最大值逐步冒泡到末端",
                        "code_example": """#include <stdio.h>

void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int a[] = {64, 34, 25, 12, 22, 11, 90};
    int n = 7;
    bubble_sort(a, n);
    for (int i = 0; i < n; i++) {
        printf("%d ", a[i]);
    }
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了冒泡排序算法的实现",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["选择排序", "算法复杂度"],
                        "tips": ["外层i表示已排序个数", "内层j表示比较范围"],
                        "common_mistakes": ["循环边界错误", "交换条件错误"]
                    },
                    {
                        "name": "选择排序",
                        "order_index": 2,
                        "content": """## 选择排序

选择排序是每趟从未排序部分选择最小（或最大）元素放到已排序部分的末尾。

### 算法步骤
1. 在未排序序列中找到最小元素
2. 将它与未排序部分的第一个元素交换
3. 重复以上步骤，直到所有元素排序完成

### 时间复杂度
- 平均：O(n²)
- 最坏：O(n²)
- 最好：O(n²)

### 示例
```c
int a[] = {64, 34, 25, 12, 22, 11, 90};
int n = 7;

for (int i = 0; i < n - 1; i++) {
    int min_idx = i;
    for (int j = i + 1; j < n; j++) {
        if (a[j] < a[min_idx]) {
            min_idx = j;
        }
    }
    // 交换
    int temp = a[i];
    a[i] = a[min_idx];
    a[min_idx] = temp;
}
```""",
                        "summary": "选择排序每趟选择最小元素放到已排序末尾",
                        "code_example": """#include <stdio.h>

void selection_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int min_idx = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[min_idx]) {
                min_idx = j;
            }
        }
        int temp = arr[i];
        arr[i] = arr[min_idx];
        arr[min_idx] = temp;
    }
}

int main() {
    int a[] = {64, 34, 25, 12, 22, 11, 90};
    int n = 7;
    selection_sort(a, n);
    for (int i = 0; i < n; i++) {
        printf("%d ", a[i]);
    }
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了选择排序算法的实现",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["冒泡排序", "算法复杂度"],
                        "tips": ["找到最小元素位置再交换", "减少交换次数"],
                        "common_mistakes": ["min_idx初始化错误", "内层循环范围错误"]
                    }
                ]
            },
            {
                "title": "递归函数",
                "description": "递归调用的定义、设计要点及应用实例",
                "order_index": 2,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "递归基础",
                        "order_index": 1,
                        "content": """## 递归基础

递归是函数调用自身的过程。

### 递归的两个要素
1. **递归出口**：结束递归的条件
2. **递归公式**：将大问题分解为小问题

### 示例：计算阶乘
```c
int factorial(int n) {
    if (n == 0 || n == 1) {
        return 1;  // 递归出口
    }
    return n * factorial(n - 1);  // 递归调用
}
```

### 执行过程
```
factorial(5)
= 5 * factorial(4)
= 5 * 4 * factorial(3)
= 5 * 4 * 3 * factorial(2)
= 5 * 4 * 3 * 2 * factorial(1)
= 5 * 4 * 3 * 2 * 1
= 120
```""",
                        "summary": "递归是函数调用自身，需要递归出口和递归公式",
                        "code_example": """#include <stdio.h>

int factorial(int n) {
    if (n == 0 || n == 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int n = 5;
    printf("%d! = %d\\n", n, factorial(n));
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了递归计算阶乘",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["递归与循环", "函数调用"],
                        "tips": ["必须有递归出口", "注意递归深度"],
                        "common_mistakes": ["缺少递归出口", "递归过深导致栈溢出"]
                    },
                    {
                        "name": "递归与循环",
                        "order_index": 2,
                        "content": """## 递归与循环的比较

### 递归特点
- 代码简洁
- 适合大问题分解为小问题
- 调用开销大，可能栈溢出

### 循环特点
- 效率高
- 适合迭代处理
- 需要手动管理状态

### 示例：求斐波那契数列
```c
// 递归版本
int fib(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fib(n - 1) + fib(n - 2);
}

// 循环版本
int fib_iter(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    int a = 0, b = 1, c;
    for (int i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}
```

### 何时使用递归
- 问题自然地分解为子问题
- 数据结构本身是递归的（树、链表）
- 递归版本更易理解""",
                        "summary": "递归和循环都能实现重复操作，递归简洁但效率较低",
                        "code_example": """#include <stdio.h>

// 循环版本（更高效）
int fib_iter(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    int a = 0, b = 1, c;
    for (int i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main() {
    int n = 10;
    printf("斐波那契数列前%d项：", n);
    for (int i = 0; i < n; i++) {
        printf("%d ", fib_iter(i));
    }
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了斐波那契数列的循环实现",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["递归基础"],
                        "tips": ["能用循环就不用递归", "注意递归效率问题"],
                        "common_mistakes": ["递归效率低", "栈空间耗尽"]
                    }
                ]
            },
            {
                "title": "指针与数组",
                "description": "指针变量、数组在函数设计中的要点",
                "order_index": 3,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "指针基础",
                        "order_index": 1,
                        "content": """## 指针基础

指针是存储变量地址的变量。

### 定义
```c
类型 *指针变量名;
int *p;      // 指向int的指针
char *pc;    // 指向char的指针
```

### 基本操作
```c
int a = 10;
int *p = &a;  // p存储a的地址

printf("%d\\n", a);    // 输出a的值：10
printf("%d\\n", p);    // 输出p的值（a的地址）
printf("%d\\n", *p);   // 输出p指向的变量的值：10
```

### 运算符
- `&`：取地址运算符
- `*`：解引用运算符（间接访问）""",
                        "summary": "指针是存储地址的变量，用*访问指向的值",
                        "code_example": """#include <stdio.h>

int main() {
    int a = 10;
    int *p = &a;

    printf("a的值：%d\\n", a);
    printf("a的地址：%p\\n", &a);
    printf("p的值（a的地址）：%p\\n", p);
    printf("*p的值：%d\\n", *p);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了指针的定义和基本操作",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["指针运算", "指针与数组"],
                        "tips": ["&取地址，*解引用", "指针类型要与指向变量匹配"],
                        "common_mistakes": ["野指针", "指针类型错误"]
                    },
                    {
                        "name": "指针与数组",
                        "order_index": 2,
                        "content": """## 指针与数组

数组名本质上是指向数组首元素的指针。

### 数组名的指针含义
```c
int a[5] = {1, 2, 3, 4, 5};
printf("%p\\n", a);      // 数组首地址
printf("%p\\n", &a[0]);   // 第一个元素的地址（相同）
```

### 指针运算
```c
int a[5] = {10, 20, 30, 40, 50};
int *p = a;  // p指向a[0]

*(p + 0)   // a[0]的值
*(p + 1)   // a[1]的值
*(p + 2)   // a[2]的值
```

### 数组作为函数参数
```c
void print_array(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        printf("%d ", *(arr + i));
    }
}
```""",
                        "summary": "数组名是指向首元素的指针，指针运算可以访问数组元素",
                        "code_example": """#include <stdio.h>

void print_array(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        printf("%d ", *(arr + i));
    }
}

int main() {
    int a[5] = {10, 20, 30, 40, 50};
    print_array(a, 5);
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了用指针访问数组元素",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["指针基础", "一维数组"],
                        "tips": ["数组名是指针常量", "指针运算注意边界"],
                        "common_mistakes": ["指针运算越界", "混淆指针和数组"]
                    }
                ]
            }
        ]
    },
    # ========== 第7章 ==========
    {
        "chapter": {
            "title": "构造数据类型与应用",
            "description": "学习结构体、共用体和枚举类型",
            "content": "本章介绍C语言的构造数据类型，包括结构体、共用体和枚举。通过本章学习，学生能够定义和使用自定义数据类型。",
            "order_index": 7,
            "estimated_minutes": 180,
            "difficulty_tags": ["进阶", "结构体"],
            "skill_tags": ["结构体", "共用体", "枚举"]
        },
        "sections": [
            {
                "title": "结构体",
                "description": "结构体的定义、使用方法",
                "order_index": 1,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "结构体基础",
                        "order_index": 1,
                        "content": """## 结构体基础

结构体是将不同类型的数据组合成一个整体。

### 定义
```c
struct 结构体名 {
    类型1 成员1;
    类型2 成员2;
    ...
};
```

### 示例：学生信息
```c
struct Student {
    char name[20];
    int age;
    float score;
};
```

### 使用
```c
struct Student s1;
s1.age = 20;
s1.score = 95.5f;
```""",
                        "summary": "结构体是将不同类型数据组合成整体的构造类型",
                        "code_example": """#include <stdio.h>
#include <string.h>

struct Student {
    char name[20];
    int age;
    float score;
};

int main() {
    struct Student s1;
    strcpy(s1.name, "张三");
    s1.age = 20;
    s1.score = 95.5f;

    printf("姓名：%s\\n", s1.name);
    printf("年龄：%d\\n", s1.age);
    printf("成绩：%.1f\\n", s1.score);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了结构体的定义和使用",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["结构体数组", "结构体与函数"],
                        "tips": ["成员可以是任意类型", "注意结构体大小"],
                        "common_mistakes": ["类型不匹配", "字符串赋值错误"]
                    },
                    {
                        "name": "结构体数组",
                        "order_index": 2,
                        "content": """## 结构体数组

结构体数组是数组元素为结构体的数组。

### 定义
```c
struct Student students[50];  // 50个学生的数组
```

### 初始化
```c
struct Student stu[3] = {
    {"张三", 20, 95.5f},
    {"李四", 21, 88.0f},
    {"王五", 19, 92.0f}
};
```

### 示例：成绩统计
```c
float sum = 0;
for (int i = 0; i < 3; i++) {
    sum += stu[i].score;
}
printf("平均分：%.1f\\n", sum / 3);
```""",
                        "summary": "结构体数组是包含多个结构体变量的数组",
                        "code_example": """#include <stdio.h>

struct Student {
    char name[20];
    int age;
    float score;
};

int main() {
    struct Student stu[3] = {
        {"张三", 20, 95.5f},
        {"李四", 21, 88.0f},
        {"王五", 19, 92.0f}
    };

    float sum = 0;
    for (int i = 0; i < 3; i++) {
        sum += stu[i].score;
        printf("%s: %.1f\\n", stu[i].name, stu[i].score);
    }
    printf("平均分：%.1f\\n", sum / 3);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了结构体数组的遍历和统计",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["结构体基础", "一维数组"],
                        "tips": ["初始化要匹配类型", "遍历用循环"],
                        "common_mistakes": ["初始化列表不匹配", "下标越界"]
                    }
                ]
            },
            {
                "title": "共用体与枚举",
                "description": "共用体的定义、使用方法，枚举类型的定义及使用方法",
                "order_index": 2,
                "estimated_minutes": 25,
                "knowledge_points": [
                    {
                        "name": "共用体",
                        "order_index": 1,
                        "content": """## 共用体

共用体的所有成员共享同一段内存。

### 定义
```c
union 共用体名 {
    类型1 成员1;
    类型2 成员2;
    ...
};
```

### 示例
```c
union Data {
    int i;
    float f;
    char c;
};

int main() {
    union Data d;
    d.i = 10;
    printf("%d\\n", d.i);   // 输出10

    d.f = 3.14f;
    printf("%f\\n", d.f);   // 输出3.14
    printf("%d\\n", d.i);    // 不可预测，因为共享内存

    return 0;
}
```

### 与结构体的区别
- 结构体：各成员独立，占用内存 = 各成员之和
- 共用体：各成员共享内存，占用内存 = 最大成员""",
                        "summary": "共用体所有成员共享同一段内存，大小为最大成员",
                        "code_example": """#include <stdio.h>

union Data {
    int i;
    float f;
    char c;
};

int main() {
    union Data d;
    printf("共用体大小：%lu\\n", sizeof(d));

    d.i = 65;
    printf("int: %d, char: %c\\n", d.i, d.c);

    d.f = 3.14f;
    printf("float: %f\\n", d.f);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了共用体的使用和内存共享特性",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["结构体基础"],
                        "tips": ["所有成员共享内存", "最后一次赋值有效"],
                        "common_mistakes": ["混淆结构和共用体", "内存覆盖问题"]
                    },
                    {
                        "name": "枚举",
                        "order_index": 2,
                        "content": """## 枚举

枚举将一组整型常量组织成一个新的类型。

### 定义
```c
enum 枚举名 {
    常量1,
    常量2,
    常量3,
    ...
};
```

### 示例：星期
```c
enum Weekday {
    MONDAY,    // 0
    TUESDAY,   // 1
    WEDNESDAY, // 2
    THURSDAY,  // 3
    FRIDAY,    // 4
    SATURDAY,  // 5
    SUNDAY     // 6
};
```

### 使用
```c
enum Weekday today = MONDAY;
printf("%d\\n", today);  // 输出0
```""",
                        "summary": "枚举创建一组命名的整型常量，默认从0开始",
                        "code_example": """#include <stdio.h>

enum Weekday {
    MONDAY = 1,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY,
    SUNDAY
};

int main() {
    enum Weekday today = FRIDAY;
    printf("今天是星期%d\\n", today);

    if (today == FRIDAY) {
        printf("明天是周末！\\n");
    }

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了枚举的定义和使用",
                        "difficulty": 1,
                        "importance": 4,
                        "related_points": ["宏定义", "常量"],
                        "tips": ["第一个常量默认为0", "可以指定值"],
                        "common_mistakes": ["超出枚举范围", "类型不匹配"]
                    }
                ]
            }
        ]
    },
    # ========== 第8章 ==========
    {
        "chapter": {
            "title": "综合设计与应用",
            "description": "学习变量的作用域、存储类别及多维指针",
            "content": "本章综合介绍C语言的高级特性，包括变量的作用域、存储类别、指针的指针以及main函数参数。",
            "order_index": 8,
            "estimated_minutes": 180,
            "difficulty_tags": ["进阶", "综合"],
            "skill_tags": ["作用域", "存储类别", "多维指针"]
        },
        "sections": [
            {
                "title": "变量作用域",
                "description": "变量的作用域、存储类别",
                "order_index": 1,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "作用域与存储类别",
                        "order_index": 1,
                        "content": """## 变量作用域

作用域规定了变量可见（可用）的范围。

### 局部作用域
- 在函数或代码块内部声明
- 只在该范围内有效

```c
void func() {
    int x = 10;  // 只在func内有效
    printf("%d", x);
}
```

### 全局作用域
- 在函数外部声明
- 从声明处到文件结束都有效

```c
int g = 100;  // 全局变量

void func() {
    printf("%d", g);  // 可以访问
}
```

### 作用域规则
- 内层代码块可以访问外层
- 外层不能访问内层（除非通过指针）""",
                        "summary": "局部变量在函数内部，全局变量在整个文件可见",
                        "code_example": """#include <stdio.h>

int g = 100;  // 全局变量

void func() {
    int local = 10;  // 局部变量
    printf("全局变量: %d\\n", g);
    printf("局部变量: %d\\n", local);
}

int main() {
    func();
    printf("全局变量: %d\\n", g);
    // printf("%d", local);  // 错误，local不可见
    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了全局变量和局部变量的作用域",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["存储类别", "生命期"],
                        "tips": ["优先使用局部变量", "全局变量要谨慎使用"],
                        "common_mistakes": ["全局变量滥用", "变量名冲突"]
                    },
                    {
                        "name": "static与const",
                        "order_index": 2,
                        "content": """## static与const

### static关键字

**修饰局部变量**：延长生命周期到程序结束
```c
void count() {
    static int n = 0;  // 只初始化一次
    n++;
    printf("%d\\n", n);
}

int main() {
    count();  // 1
    count();  // 2
    count();  // 3
}
```

**修饰全局变量/函数**：限制作用域为本文件
```c
static int internal_var = 100;  // 只能在本文件访问
```

### const关键字

**修饰变量**：使变量变为常量
```c
const int MAX = 100;
MAX = 200;  // 错误！不能修改
```

**修饰指针**
```c
const int *p1;     // 不能通过p1修改指向的值
int const *p2;     // 同上
int * const p3;    // p3指针本身不能改变
const int * const p4;  // 都不能改变
```""",
                        "summary": "static延长生命周期和限制作用域，const使变量不可修改",
                        "code_example": """#include <stdio.h>

void counter() {
    static int count = 0;
    count++;
    printf("count = %d\\n", count);
}

int main() {
    counter();  // 1
    counter();  // 2
    counter();  // 3

    const double PI = 3.14159;
    // PI = 3.14;  // 错误！
    printf("PI = %.5f\\n", PI);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了static延长生命周期和const定义常量",
                        "difficulty": 2,
                        "importance": 5,
                        "related_points": ["变量作用域", "指针"],
                        "tips": ["static局部变量只初始化一次", "const是编译时约束"],
                        "common_mistakes": ["误解static的含义", "const修饰指针位置错误"]
                    }
                ]
            },
            {
                "title": "多维指针与main参数",
                "description": "一维指针与数组的关系、多维指针、main函数参数",
                "order_index": 2,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "指向指针的指针",
                        "order_index": 1,
                        "content": """## 指向指针的指针

指针的指针是存储指针地址的变量。

### 定义
```c
int value = 10;
int *ptr = &value;      // ptr是指向value的指针
int **pptr = &ptr;      // pptr是指向ptr的指针
```

### 使用
```c
printf("%d\\n", value);    // 10
printf("%d\\n", *ptr);     // 10
printf("%d\\n", **pptr);   // 10
```

### 图示
```
pptr ──→ ptr ──→ value
地址    地址    10
```""",
                        "summary": "指向指针的指针是指针的地址，用于操作指针本身",
                        "code_example": """#include <stdio.h>

int main() {
    int value = 10;
    int *ptr = &value;
    int **pptr = &ptr;

    printf("value = %d\\n", value);     // 10
    printf("*ptr = %d\\n", *ptr);       // 10
    printf("**pptr = %d\\n", **pptr);   // 10

    printf("&value = %p\\n", &value);
    printf("ptr = %p\\n", ptr);
    printf("*pptr = %p\\n", *pptr);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了二级指针的使用",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["指针基础", "指针与数组"],
                        "tips": ["*pptr访问value需要两个*", "常用于二维数组"],
                        "common_mistakes": ["少一个*", "混淆指针级别"]
                    },
                    {
                        "name": "main函数参数",
                        "order_index": 2,
                        "content": """## main函数参数

命令行程序通常使用 argc 和 argv 作为参数。

### 参数说明
```c
int main(int argc, char *argv[]) {
    // argc: 命令行参数个数
    // argv: 命令行参数数组
}
```

### 示例
```c
// 运行程序: ./program hello world
int main(int argc, char *argv[]) {
    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = %s\\n", i, argv[i]);
    }
    return 0;
}
```

### 输出
```
argv[0] = ./program
argv[1] = hello
argv[2] = world
```""",
                        "summary": "main函数接受命令行参数，argc是个数，argv是字符串数组",
                        "code_example": """#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("命令行参数个数: %d\\n", argc);

    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = %s\\n", i, argv[i]);
    }

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了main函数接收命令行参数",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["指针与数组", "字符串基础"],
                        "tips": ["argv[0]是程序名", "注意参数类型是char*"],
                        "common_mistakes": ["忽略argc检查", "类型转换错误"]
                    }
                ]
            }
        ]
    },
    # ========== 第9章 ==========
    {
        "chapter": {
            "title": "数据永久性存储",
            "description": "学习文件的组织方式和基本文件操作",
            "content": "本章介绍C语言的文件操作，包括文本文件和二进制文件的读写操作。",
            "order_index": 9,
            "estimated_minutes": 90,
            "difficulty_tags": ["进阶", "文件"],
            "skill_tags": ["文件操作", "文本文件", "二进制文件"]
        },
        "sections": [
            {
                "title": "文件基础",
                "description": "文件的组织方式、文本文件和二进制文件",
                "order_index": 1,
                "estimated_minutes": 20,
                "knowledge_points": [
                    {
                        "name": "文件类型",
                        "order_index": 1,
                        "content": """## 文件类型

### 文本文件
- 以ASCII字符存储
- 可以用文本编辑器查看
- 例：.txt, .c, .h

### 二进制文件
- 以二进制形式存储
- 不能直接用文本编辑器查看
- 例：.exe, .jpg, .dat

### 文件操作步骤
1. 打开文件
2. 读/写操作
3. 关闭文件

### 打开文件函数
```c
FILE *fopen(const char *filename, const char *mode);
```

### 打开模式
| 模式 | 含义 |
|------|------|
| "r" | 只读，文件必须存在 |
| "w" | 只写，文件不存在则创建 |
| "a" | 追加 |
| "rb" | 二进制只读 |
| "wb" | 二进制只写 |""",
                        "summary": "文件分为文本文件和二进制文件，使用fopen打开",
                        "code_example": """#include <stdio.h>

int main() {
    FILE *fp;

    // 写文本文件
    fp = fopen("test.txt", "w");
    if (fp == NULL) {
        printf("打开文件失败\\n");
        return 1;
    }
    fprintf(fp, "Hello, World!");
    fclose(fp);

    // 读文本文件
    char buffer[100];
    fp = fopen("test.txt", "r");
    fgets(buffer, 100, fp);
    printf("%s\\n", buffer);
    fclose(fp);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了文本文件的创建和读取",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["文件读写函数"],
                        "tips": ["打开后检查NULL", "操作后要关闭文件"],
                        "common_mistakes": ["忘记检查fopen返回值", "忘记fclose"]
                    }
                ]
            },
            {
                "title": "文件读写操作",
                "description": "文件操作的函数",
                "order_index": 2,
                "estimated_minutes": 30,
                "knowledge_points": [
                    {
                        "name": "文本文件读写",
                        "order_index": 1,
                        "content": """## 文本文件读写

### 写入函数
```c
fprintf(fp, "格式", 变量);  // 格式化写入
fputs(str, fp);              // 写入字符串
fputc(ch, fp);              // 写入字符
```

### 读取函数
```c
fscanf(fp, "格式", &变量);  // 格式化读取
fgets(str, n, fp);          // 读取字符串
fgetc(fp);                  // 读取字符
```

### 示例：学生成绩写入和读取
```c
// 写入
fprintf(fp, "%s %d %.1f\\n", "张三", 20, 95.5);

// 读取
char name[20];
int age;
float score;
fscanf(fp, "%s %d %f", name, &age, &score);
```""",
                        "summary": "文本文件读写使用fprintf、fscanf、fgets等函数",
                        "code_example": """#include <stdio.h>

int main() {
    FILE *fp;

    // 写入数据
    fp = fopen("student.txt", "w");
    fprintf(fp, "%s %d %.1f\\n", "张三", 20, 95.5);
    fprintf(fp, "%s %d %.1f\\n", "李四", 21, 88.0);
    fclose(fp);

    // 读取数据
    char name[20];
    int age;
    float score;

    fp = fopen("student.txt", "r");
    while (fscanf(fp, "%s %d %f", name, &age, &score) != EOF) {
        printf("%s %d %.1f\\n", name, age, score);
    }
    fclose(fp);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了学生成绩的写入和读取",
                        "difficulty": 1,
                        "importance": 5,
                        "related_points": ["文件类型", " fprintf/scanf"],
                        "tips": ["注意fscanf返回EOF的判断", "fgets保留换行符"],
                        "common_mistakes": ["忘记检查EOF", "字符串和数字混合读取"]
                    },
                    {
                        "name": "二进制文件操作",
                        "order_index": 2,
                        "content": """## 二进制文件操作

### 读写函数
```c
fread(buffer, size, count, fp);  // 读取
fwrite(buffer, size, count, fp); // 写入
```

### 示例：结构体写入和读取
```c
struct Student {
    char name[20];
    int age;
    float score;
};

struct Student s = {"张三", 20, 95.5f};

// 写入二进制文件
fwrite(&s, sizeof(struct Student), 1, fp);

// 读取二进制文件
struct Student s2;
fread(&s2, sizeof(struct Student), 1, fp);
```

### 文本文件vs二进制文件
| 特性 | 文本文件 | 二进制文件 |
|------|----------|------------|
| 可读性 | 可直接查看 | 不能直接查看 |
| 精度 | 可能有精度损失 | 完全一致 |
| 长度 | 字符串长度明确 | 需要额外存储长度 |""",
                        "summary": "二进制文件使用fread和fwrite，适合存储结构化数据",
                        "code_example": """#include <stdio.h>

struct Student {
    char name[20];
    int age;
    float score;
};

int main() {
    FILE *fp;
    struct Student s = {"张三", 20, 95.5f};

    // 写入二进制文件
    fp = fopen("student.dat", "wb");
    fwrite(&s, sizeof(struct Student), 1, fp);
    fclose(fp);

    // 读取二进制文件
    struct Student s2;
    fp = fopen("student.dat", "rb");
    fread(&s2, sizeof(struct Student), 1, fp);
    fclose(fp);

    printf("%s %d %.1f\\n", s2.name, s2.age, s2.score);

    return 0;
}""",
                        "code_language": "c",
                        "code_explanation": "演示了结构体的二进制文件读写",
                        "difficulty": 2,
                        "importance": 4,
                        "related_points": ["文本文件读写", "结构体"],
                        "tips": ["fread/fwrite按字节操作", "注意数据对齐"],
                        "common_mistakes": ["忘记sizeof", "文件打开模式错误"]
                    }
                ]
            }
        ]
    }
]


async def clear_all_chapters():
    """删除C语言课程的所有章节"""
    from sqlalchemy import select, delete, text

    async with AsyncSessionLocal() as db:
        await db.execute(text("PRAGMA foreign_keys=OFF"))

        try:
            result = await db.execute(select(Course).where(Course.code == "C"))
            course = result.scalar_one_or_none()

            if not course:
                return None

            # 删除所有章节
            result = await db.execute(
                select(Chapter).where(Chapter.course_id == course.id)
            )
            chapters = result.scalars().all()

            for chapter in chapters:
                result = await db.execute(select(Section).where(Section.chapter_id == chapter.id))
                sections = result.scalars().all()
                section_ids = [s.id for s in sections]

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
            print(f"已删除所有旧章节")

        finally:
            await db.execute(text("PRAGMA foreign_keys=ON"))

        return course


async def generate_all_content():
    """生成全部章节内容"""
    course = await clear_all_chapters()
    if not course:
        print("C语言课程不存在")
        return

    async with AsyncSessionLocal() as db:
        total_chapters = 0
        total_sections = 0
        total_kp = 0

        for chapter_data in ALL_CHAPTERS_DATA:
            # 创建章节
            chapter = Chapter(
                course_id=course.id,
                title=chapter_data["chapter"]["title"],
                description=chapter_data["chapter"]["description"],
                content=chapter_data["chapter"]["content"],
                order_index=chapter_data["chapter"]["order_index"],
                estimated_minutes=chapter_data["chapter"]["estimated_minutes"],
                difficulty_tags=chapter_data["chapter"]["difficulty_tags"],
                skill_tags=chapter_data["chapter"]["skill_tags"]
            )
            db.add(chapter)
            await db.flush()
            total_chapters += 1
            print(f"创建章节: {chapter.title}")

            # 创建小节
            for section_data in chapter_data["sections"]:
                section = Section(
                    chapter_id=chapter.id,
                    title=section_data["title"],
                    description=section_data["description"],
                    order_index=section_data["order_index"],
                    estimated_minutes=section_data["estimated_minutes"]
                )
                db.add(section)
                await db.flush()
                total_sections += 1

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
                    total_kp += 1

                print(f"  - {section.title}: {len(section_data['knowledge_points'])}个知识点")

        await db.commit()

        print(f"\n全部9章内容生成完成！")
        print(f"  - 章节: {total_chapters}个")
        print(f"  - 小节: {total_sections}个")
        print(f"  - 知识点: {total_kp}个")


if __name__ == "__main__":
    asyncio.run(generate_all_content())
