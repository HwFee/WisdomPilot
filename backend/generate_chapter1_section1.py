"""Generate Chapter 1 Section 1: C程序入门 - 按教学大纲生成"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint


# 第一章第1节：教学大纲内容
# 1.1 通过实例学习，掌握C程序的基本结构

SECTION_DATA = {
    "section_title": "C程序入门",
    "section_description": "通过实例学习，掌握C程序的基本结构",
    "order_index": 1,
    "estimated_minutes": 20,
    "knowledge_points": [
        {
            "name": "C程序的基本结构",
            "order_index": 1,
            "content": """## C程序的基本结构

C语言程序由预处理指令、主函数和执行语句三部分组成，是学习C语言的基础。

### 一、概述

一个完整的C语言程序通常包含以下三个部分：

1. **预处理指令** - 在编译前由预处理器处理的指令
2. **主函数** - 程序的执行入口点
3. **语句** - 完成具体操作的执行命令

### 二、预处理指令

预处理指令以 `#` 开头，在编译前由预处理器处理。

**文件包含指令 #include**
```c
#include <stdio.h>    // 包含标准输入输出头文件
#include <stdlib.h>   // 包含标准库函数
#include <string.h>  // 包含字符串处理函数
```

**说明：**
- `<stdio.h>` 是Standard Input/Output的缩写
- 包含标准输入输出库，提供printf、scanf等函数
- 尖括号表示从系统目录查找头文件
- 用户自定义头文件用双引号括起来

### 三、主函数 main

main函数是C程序的执行起点，每个C程序必须有且只能有一个main函数。

**标准形式**
```c
int main(void) {
    // 程序代码
    return 0;
}
```

**返回类型 int**
- 表示程序结束时返回一个整数
- `return 0;` 表示程序正常结束
- 非零值表示程序异常结束

**参数 void**
- 表示main函数没有命令行参数
- 也可以写作 `int main()` （C++风格）

### 四、语句

语句是C程序的基本执行单元，每条语句以分号 `;` 结尾。

**语句类型**
```c
int a = 10;           // 声明语句
a = a + 5;            // 赋值语句
printf("Hello");       // 函数调用语句
if (a > 5) { }        // 复合语句
```

### 五、完整示例

```c
#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    return 0;
}
```

**运行结果**
```
Hello, World!
```

### 六、C程序编译运行过程

1. **预处理** → 处理 `#include` 和 `#define` 等指令
2. **编译** → 将C代码翻译成汇编代码
3. **汇编** → 将汇编代码翻译成机器码（目标文件）
4. **链接** → 将目标文件与库文件链接成可执行文件
5. **运行** → 执行生成的可执行文件

### 七、常见集成开发环境

| IDE | 特点 | 适用人群 |
|-----|------|----------|
| Code::Blocks | 轻量级、跨平台、免费 | 初学者 |
| Visual C++ | 功能强大、Windows原生 | Windows开发 |
| Dev-C++ | 简洁、中文界面 | 初学者 |
| CLion | 现代化、付费 | 专业开发 |

### 八、注意事项

1. C语言区分大小写，`main` 和 `Main` 是不同的
2. 每条语句必须以分号结尾
3. 函数体外不能直接写执行语句
4. 注释不参与编译
5. 建议使用英文标点符号""",
            "summary": "C程序由预处理指令、main函数和语句三部分组成，main是程序执行的唯一入口",
            "code_example": """#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    return 0;
}""",
            "code_language": "c",
            "code_explanation": "这是经典的Hello World程序，展示了C程序的基本结构：预处理指令包含头文件、main函数定义、输出语句、返回语句",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["main函数", "预处理指令#include", "语句", "printf函数"],
            "tips": ["一个C程序必须有且只能有一个main函数", "main函数是程序执行的起点", "语句必须以分号结尾"],
            "common_mistakes": ["把main函数名拼写错误", "忘记写return语句", "忘记在语句末尾加分号", "混用中英文标点"]
        },
        {
            "name": "main函数详解",
            "order_index": 2,
            "content": """## main函数详解

main函数是C程序的入口点，程序从main函数开始执行。

### 一、main函数的标准形式

**C89/C99标准**
```c
int main(void) {
    // 程序代码
    return 0;
}
```

**C++风格（省略void）**
```c
int main() {
    // 程序代码
    return 0;
}
```

### 二、main函数的返回类型

**int返回类型**
```c
int main(void) {
    return 0;  // 正常结束
    return 1;  // 异常结束
}
```

**void返回类型（不标准，不推荐）**
```c
void main() {  // 不推荐，不符合C标准
    // ...
}
```

### 三、main函数的参数

**带参数的main函数**
```c
int main(int argc, char *argv[]) {
    // argc: 命令行参数个数
    // argv: 命令行参数数组
    return 0;
}
```

**参数说明**
- `argc` 是参数个数，至少为1（程序名本身）
- `argv[0]` 是程序名
- `argv[1]` 到 `argv[argc-1]` 是实际参数

**使用示例**
```c
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("程序名: %s\\n", argv[0]);
    printf("参数个数: %d\\n", argc);

    for (int i = 1; i < argc; i++) {
        printf("参数%d: %s\\n", i, argv[i]);
    }

    return 0;
}
```

**命令行调用示例**
```
$ ./program hello world
程序名: ./program
参数个数: 3
参数1: hello
参数2: world
```

### 四、main函数的调用特点

1. **自动调用** - 程序运行时由系统自动调用main
2. **唯一入口** - 每个程序只能有一个main函数
3. **不可递归** - main函数不能被递归调用
4. **执行顺序** - 按照代码书写顺序从上到下执行

### 五、exit函数与return的区别

**return语句**
```c
int main(void) {
    if (error) {
        return 1;  // 结束main函数
    }
    return 0;  // 正常结束
}
```

**exit函数**
```c
#include <stdlib.h>

int main(void) {
    if (error) {
        exit(1);  // 结束整个程序
    }
    exit(0);
}
```

**区别**
| 特性 | return | exit() |
|------|--------|--------|
| 作用范围 | 仅结束当前函数 | 结束整个程序 |
| 调用位置 | 任何函数中 | 任何位置 |
| 是否关闭文件 | 否 | 是，自动关闭所有文件 |
| 在main中效果 | 等同于exit | 直接退出 |

### 六、main函数的执行流程

```
程序启动（系统调用main）
    ↓
执行函数体中的静态变量初始化
    ↓
执行函数体中的语句（按顺序）
    ↓
遇到return或函数结束
    ↓
返回退出状态码给系统
    ↓
程序终止
```

### 七、注意事项

1. main函数必须返回int类型（这是C标准的强制要求）
2. 建议显式写出返回类型和参数
3. 返回值建议使用0表示成功，非零表示异常
4. 不要在main函数中省略return语句
5. 避免在main函数中做过于复杂的操作""",
            "summary": "main函数是C程序的入口点，必须返回int类型，程序正常结束返回0",
            "code_example": """#include <stdio.h>
#include <stdlib.h>

int main(void) {
    printf("程序开始执行\\n");

    // 演示exit和return的效果区别
    printf("使用return结束程序\\n");
    return 0;  // 正常返回，程序结束

    // exit永远不会执行
    printf("这行不会执行\\n");
    exit(0);
}""",
            "code_language": "c",
            "code_explanation": "演示了main函数的基本结构，以及return语句结束程序的作用",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["C程序的基本结构", "return语句", "exit函数", "命令行参数"],
            "tips": ["main函数是程序执行的唯一入口", "返回0表示程序执行成功", "exit函数可以在任意位置结束程序"],
            "common_mistakes": ["写成void main()（不标准）", "忘记写return语句", "混淆exit和return的用法"]
        },
        {
            "name": "语句与注释",
            "order_index": 3,
            "content": """## 语句与注释

### 一、语句的基本概念

语句是C程序的基本执行单元，每条语句完成特定的操作。

**语句的组成**
- 表达式语句：由表达式加上分号组成
- 复合语句：用花括号括起来的多条语句
- 控制语句：用于控制程序执行流程

### 二、语句的分类

**表达式语句**
```c
a = 10;           // 赋值语句
a + 5;            // 表达式语句（无实际效果）
printf("Hello");  // 函数调用语句
i++;              // 自增语句
```

**复合语句（语句块）**
```c
{
    int a = 10;       // 声明语句
    a = a * 2;        // 赋值语句
    printf("%d", a);  // 函数调用语句
}
```

**空语句**
```c
;  // 什么都不做，常用于循环体
for(int i=0; i<10; );  // 死循环
```

### 三、注释的作用与类型

注释用于说明代码功能，不参与程序编译和执行。

**单行注释 //**
```c
int age = 20;  // 定义年龄变量
```
适用于简短的说明

**多行注释 /* */**
```c
/*
 * 这是多行注释
 * 可以写多行说明
 * 通常用于较长的解释
 */
```
适用于多行的说明

### 四、注释的使用规范

**好的注释示例**
```c
// 计算圆的面积
double radius = 5.0;
double area = PI * radius * radius;

// 判断成绩等级
if (score >= 90) {
    grade = 'A';
}
```

**过度的注释示例（不推荐）**
```c
int a;  // 声明变量a
a = 10;  // 给a赋值10
```

**错误的注释示例**
```c
// if语句，判断a是否大于0
if (a > 0) {  // 注释和代码重复，没有意义
    printf("%d", a);  // 输出a的值
}
```

### 五、注释的注意事项

1. **不要过度注释** - 代码能说明的问题不要重复注释
2. **保持注释更新** - 修改代码后要及时更新注释
3. **不要废话注释** - 避免写显而易见的注释
4. **注意注释位置** - 注释放在要说明的代码上方或行末
5. **单行注释可嵌套** - `//` 可以嵌套
6. **多行注释不可嵌套** - `/* */` 不能嵌套

### 六、语句的书写规范

**良好格式**
```c
int a = 10;
int b = 20;
int sum = a + b;
printf("sum = %d\\n", sum);
```

**不推荐格式**
```c
int a=10; int b=20; int sum=a+b; printf("sum=%d\\n",sum);  // 太挤了，难以阅读
```

**缩进规范**
```c
// 推荐4空格缩进
if (a > 0) {
    if (b > 0) {
        printf("都是正数\\n");
    }
}
```

### 七、常见错误

```c
// 错误1：忘记分号
int a = 10  // 错误！

// 错误2：多行注释嵌套
/*
 外层注释
 /* 内层注释 */  // 错误！多行注释不能嵌套
*/

// 错误3：注释位置不当
    int a;  // 如果在上面一行注释会更好
```""",
            "summary": "语句以分号结尾，注释用于说明代码功能不参与执行，分为单行注释和多行注释",
            "code_example": """#include <stdio.h>

int main(void) {
    /* 这是一个简单的程序
       演示语句和注释的用法 */

    int score = 85;      // 定义成绩变量
    char grade;          // 定义等级变量

    // 判断成绩等级
    if (score >= 90) {
        grade = 'A';
    } else if (score >= 80) {
        grade = 'B';
    } else if (score >= 60) {
        grade = 'C';
    } else {
        grade = 'D';
    }

    printf("成绩：%d，等级：%c\\n", score, grade);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了多行注释和单行注释的用法，以及if-else语句结构",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["C程序的基本结构", "if语句", "printf函数"],
            "tips": ["注释要清晰说明代码功能", "不要过度注释", "保持代码和注释的一致性"],
            "common_mistakes": ["忘记在语句末尾加分号", "注释嵌套使用错误", "注释位置不当"]
        },
        {
            "name": "格式化输出函数printf",
            "order_index": 4,
            "content": """## 格式化输出函数printf

printf是C语言中最常用的输出函数，用于向屏幕输出信息。

### 一、基本语法

```c
int printf("格式控制字符串", 参数列表);
```

**返回值**：输出字符的个数，错误时返回负数

**格式控制字符串**：用双引号括起来，包含普通字符和格式说明符

**参数列表**：要输出的数据，多个参数用逗号分隔

### 二、常用格式说明符

| 说明符 | 含义 | 示例 |
|--------|------|------|
| %d | 输出十进制整数 | printf("%d", 10); |
| %ld | 输出长整数 | printf("%ld", 1234567890L); |
| %u | 输出无符号整数 | printf("%u", -1); |
| %f | 输出浮点数 | printf("%f", 3.14); |
| %.2f | 输出保留2位小数 | printf("%.2f", 3.14159); |
| %lf | 输出双精度浮点数 | printf("%lf", 3.1415926); |
| %c | 输出单个字符 | printf("%c", 'A'); |
| %s | 输出字符串 | printf("%s", "Hello"); |
| %p | 输出指针地址 | printf("%p", &var); |
| %% | 输出百分号% | printf("%%"); |
| %x | 输出十六进制 | printf("%x", 255); |
| %o | 输出八进制 | printf("%o", 255); |

### 三、转义字符

| 字符 | 含义 |
|------|------|
| \\n | 换行 |
| \\t | 制表符（Tab） |
| \\r | 回车 |
| \\" | 输出双引号 |
| \\' | 输出单引号 |
| \\\\ | 输出反斜杠 |
| \\0 | 空字符（字符串结束标志） |

### 四、示例程序

```c
#include <stdio.h>

int main(void) {
    // 输出整数
    int age = 20;
    printf("年龄：%d岁\\n", age);

    // 输出浮点数
    double height = 175.5;
    printf("身高：%.1fcm\\n", height);

    // 输出字符
    char grade = 'A';
    printf("等级：%c\\n", grade);

    // 输出字符串
    printf("Hello %s\\n", "World");

    // 同时输出多个值
    printf("%d + %d = %d\\n", 1, 2, 1+2);

    // 输出百分号
    printf("完成度：100%%\\n");

    return 0;
}
```

**运行结果**
```
年龄：20岁
身高：175.5cm
等级：A
Hello World
1 + 2 = 3
完成度：100%
```

### 五、格式说明符的修饰

**指定宽度**
```c
printf("%5d", 123);    // 输出：  123（右对齐）
printf("%-5d", 123);   // 输出：123  （左对齐）
printf("%05d", 123);   // 输出：00123（补零）
```

**指定精度**
```c
printf("%.2f", 3.14159);    // 输出：3.14
printf("%.4f", 3.14);      // 输出：3.1400
printf("%.2s", "Hello");   // 输出：He
```

### 六、注意事项

1. 格式说明符前必须加 `%`
2. 参数个数要和格式说明符个数匹配
3. 参数类型要和格式说明符匹配
4. 整数用 `%d`，不要用 `%f`
5. 字符串结束标志 `'\\0'` 不算在长度内
6. 建议在输出末尾加 `\\n` 换行

### 七、常见错误

```c
// 错误1：忘记%
printf("年龄：d岁", age);  // 输出：年龄：d岁

// 错误2：类型不匹配
printf("%d", 3.14);  // 输出不确定！

// 错误3：个数不匹配
printf("%d %d", 10);  // 错误！

// 错误4：忘记换行
printf("第一行");
printf("第二行");  // 不会换行，输出：第一行第二行
```""",
            "summary": "printf是格式化输出函数，用于向屏幕输出信息，支持多种格式说明符和转义字符",
            "code_example": """#include <stdio.h>

int main(void) {
    int age = 20;
    float height = 175.5f;
    char grade = 'A';

    // 基本输出
    printf("年龄：%d岁\\n", age);
    printf("身高：%.1fcm\\n", height);
    printf("等级：%c\\n", grade);

    // 指定宽度输出
    printf("%5d\\n", 123);    // 输出宽度为5，右对齐
    printf("%-5d\\n", 123);   // 左对齐
    printf("%05d\\n", 123);   // 补零

    // 复合输出
    printf("%s的年龄是%d岁\\n", "小明", age);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了printf函数的各种格式说明符使用方法，包括整数、浮点数、字符、字符串的输出",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["基本数据类型", "变量与常量", "转义字符"],
            "tips": ["格式字符串要用双引号", "参数个数要和格式说明符匹配", "整数用%d，浮点数用%f"],
            "common_mistakes": ["忘记在格式说明符前加%", "整数用%f输出", "忘记\\n换行", "参数类型不匹配"]
        },
        {
            "name": "格式化输入函数scanf",
            "order_index": 5,
            "content": """## 格式化输入函数scanf

scanf是C语言中最常用的输入函数，用于从键盘读取数据。

### 一、基本语法

```c
int scanf("格式控制字符串", 参数列表);
```

**返回值**：成功读取的数据项个数，到达文件末尾时返回EOF

**格式控制字符串**：包含格式说明符和分隔符

**参数列表**：要存储读取数据的变量地址

### 二、常用格式说明符

| 说明符 | 含义 |
|--------|------|
| %d | 读取十进制整数 |
| %ld | 读取长整数 |
| %f | 读取浮点数（float） |
| %lf | 读取双精度浮点数（double） |
| %c | 读取单个字符 |
| %s | 读取字符串（遇空白字符停止） |
| %x | 读取十六进制 |
| %o | 读取八进制 |

### 三、基本使用示例

```c
#include <stdio.h>

int main(void) {
    int age;
    float height;
    char name[20];

    printf("请输入年龄：");
    scanf("%d", &age);

    printf("请输入身高：");
    scanf("%f", &height);

    printf("请输入姓名：");
    scanf("%s", name);  // 字符串不需要&符号

    printf("\\n年龄：%d岁\\n", age);
    printf("身高：%.1fcm\\n", height);
    printf("姓名：%s\\n", name);

    return 0;
}
```

**运行结果**
```
请输入年龄：20
请输入身高：175.5
请输入姓名：张三

年龄：20岁
身高：175.5cm
姓名：张三
```

### 四、地址运算符 &

scanf的参数必须是变量的地址，使用 `&` 获取变量的地址。

**正确用法**
```c
int a;
scanf("%d", &a);  // 正确：&a表示变量a的地址
```

**错误用法**
```c
scanf("%d", a);  // 错误！a不是地址
```

**特殊情况：字符数组**
```c
char str[100];
scanf("%s", str);  // 正确：数组名str本身就是地址
```

### 五、多个数据输入

**空格或回车分隔**
```c
int a, b, c;
scanf("%d%d%d", &a, &b, &c);
// 可以输入：10 20 30 或 10回车20回车30
```

**指定分隔符**
```c
scanf("%d,%d,%d", &a, &b, &c);  // 必须用逗号分隔
// 输入必须：10,20,30
```

**混合分隔**
```c
scanf("%d %c %d", &a, &op, &b);
// 可以输入：10 + 20
```

### 六、scanf的返回值

```c
int count = scanf("%d%d", &a, &b);
// 成功读取2个：返回2
// 只成功读取1个：返回1
// 全部失败：返回0
// 遇到文件结束：返回EOF
```

**建议用法**
```c
if (scanf("%d", &a) != 1) {
    printf("输入错误！\\n");
}
```

### 七、示例：计算两个数的和

```c
#include <stdio.h>

int main(void) {
    int a, b, sum;

    printf("请输入两个整数（用空格分隔）：");
    if (scanf("%d%d", &a, &b) == 2) {
        sum = a + b;
        printf("%d + %d = %d\\n", a, b, sum);
    } else {
        printf("输入错误！\\n");
    }

    return 0;
}
```

### 八、注意事项

1. **必须使用 & 符号**（字符数组除外）
2. 字符数组使用 %s 读取，遇到空白字符停止
3. scanf的返回值表示成功读取的项数
4. 格式字符串中的普通字符需要原样输入
5. 建议在使用前初始化变量
6. 字符输入受缓冲区影响

### 九、常见错误

```c
// 错误1：忘记&
int a;
scanf("%d", a);  // 错误！

// 错误2：%s读取字符串带&
char name[20];
scanf("%s", &name);  // 不推荐

// 错误3：格式说明符不匹配
float f;
scanf("%d", &f);  // 错误！

// 错误4：字符输入问题
char c1, c2;
scanf("%c%c", &c1, &c2);
// 输入 "ab" 时，c1='a', c2='b'
// 但如果前面有回车，会读取回车
```""",
            "summary": "scanf是格式化输入函数，从键盘读取数据，需要使用&获取变量地址",
            "code_example": """#include <stdio.h>

int main(void) {
    int a, b;

    printf("请输入两个整数：");
    int count = scanf("%d%d", &a, &b);

    if (count == 2) {
        printf("%d + %d = %d\\n", a, b, a + b);
        printf("成功读取了%d个数据\\n", count);
    } else {
        printf("输入错误！只读取了%d个数据\\n", count);
    }

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了scanf函数的基本用法，包括读取整数、检查返回值、处理输入错误",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["printf函数", "基本数据类型", "变量与常量"],
            "tips": ["scanf参数要加&符号", "整数用%d，浮点数用%f", "注意检查scanf的返回值"],
            "common_mistakes": ["忘记&符号", "格式说明符不匹配", "忽略scanf返回值检查"]
        },
        {
            "name": "C语言开发环境",
            "order_index": 6,
            "content": """## C语言开发环境

### 一、常用集成开发环境（IDE）

| IDE | 特点 | 适用人群 | 下载地址 |
|-----|------|----------|----------|
| Code::Blocks | 轻量级、跨平台、免费、开源 | 初学者 | codeblocks.org |
| Visual Studio / Visual C++ | 功能强大、专业级、Windows原生 | Windows开发 | visualstudio.com |
| Dev-C++ | 轻量级、简洁、中文界面 | 初学者 | sourceforge.net |
| CLion | 现代化界面、智能提示 | 专业开发 | jetbrains.com/clion |

### 二、开发环境组成

**编译器（Compiler）**
- 将C源代码翻译成机器码
- GCC、MinGW、MSVC、Clang等

**编辑器（Editor）**
- 编写代码的工具
- 支持语法高亮、自动缩进等功能

**调试器（Debugger）**
- 单步执行、查看变量值
- 设置断点、监视变量变化

### 三、Code::Blocks基本使用

**新建项目步骤**
1. 打开Code::Blocks
2. 点击 File → New → Project
3. 选择 "Console Application"
4. 选择C语言
5. 设置项目名称和路径
6. 选择编译器（默认GCC）
7. 点击完成

**编写代码**
```c
#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    return 0;
}
```

**编译运行**
- 编译：Ctrl+F9
- 运行：Ctrl+F10
- 编译并运行：F9

### 四、常见错误处理

**编译错误（Compile Error）**
```c
// 语法错误
int a = 10  // 错误！缺少分号
// 编译器报告：syntax error
```

**链接错误（Link Error）**
```c
int main(void) {
    printf("%d", miss());  // miss()未定义
    return 0;
}
```

**运行错误（Runtime Error）**
```c
int main(void) {
    int a = 10 / 0;  // 除零错误，程序崩溃
    return 0;
}
```

**逻辑错误（Logic Error）**
```c
int main(void) {
    int result = 10 + 4;  // 结果应该是15，但写成了4
    printf("%d", result);  // 输出14而不是15
    return 0;
}
```

### 五、程序的调试方法

**设置断点**
- 在代码行号左侧单击设置断点
- 程序运行到断点会暂停

**单步执行**
- F7：执行一行代码
- 逐语句：进入函数内部
- 逐过程：跳过函数调用

**查看变量**
- 鼠标悬停查看变量值
- 使用监视窗口监视表达式

**调试步骤**
1. 在可疑代码处设置断点
2. 运行程序（按F8或F5）
3. 程序在断点处暂停
4. 单步执行，观察变量变化
5. 找到问题根源
6. 修改代码，重新编译运行

### 六、学习建议

1. **选择一款IDE** - 推荐Code::Blocks或Dev-C++
2. **多动手练习** - 只看不动手学不会编程
3. **学会看错误信息** - 编译器会告诉你哪里错了
4. **擅用调试工具** - 单步执行帮助理解程序执行过程
5. **参考官方文档** - 学习IDE和编译器的使用方法
6. **积累代码量** - 多写多练，熟能生巧

### 七、常见IDE快捷键

| 功能 | Code::Blocks | Visual Studio |
|------|--------------|---------------|
| 编译 | Ctrl+F9 | Ctrl+B |
| 运行 | Ctrl+F10 | F5 |
| 编译运行 | F9 | F5 |
| 调试 | F8 | F5 |
| 格式化代码 | Ctrl+Shift+F | Ctrl+K+F |
| 注释 | Ctrl+Shift+C | Ctrl+K+C |
| 取消注释 | Ctrl+Shift+X | Ctrl+K+U |""",
            "summary": "C语言常用开发环境包括Code::Blocks、Visual C++等，编程需要编译器、编辑器和调试器配合使用",
            "code_example": """/*
 * 第一个C程序 - Hello World
 * 这是学习C语言的经典入门程序
 * 功能：向屏幕输出问候语
 */

#include <stdio.h>

int main(void) {
    // 向屏幕输出问候语
    printf("==========================\\n");
    printf("  欢迎学习C语言程序设计！  \\n");
    printf("==========================\\n");

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了一个完整的C程序，包含多行注释说明、格式化输出",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["C程序的基本结构", "main函数", "printf函数"],
            "tips": ["推荐使用Code::Blocks或Dev-C++作为入门IDE", "学会阅读编译错误信息", "多动手练习是学习编程的关键"],
            "common_mistakes": ["选择过于复杂的IDE", "不习惯看错误信息", "只看不动手"]
        },
        {
            "name": "软件开发基本过程",
            "order_index": 7,
            "content": """## 软件开发基本过程

### 一、软件开发的阶段

软件开发是一个系统化的过程，通常包括以下阶段：

```
需求分析 → 设计 → 编码 → 测试 → 维护
```

### 二、各阶段详解

**1. 需求分析阶段**
- 理解用户需求
- 确定系统功能
- 编写需求文档

**2. 设计阶段**
- 总体设计：划分模块
- 详细设计：设计算法和数据结构
- 绘制流程图

**3. 编码阶段**
- 选择编程语言
- 编写代码
- 代码调试

**4. 测试阶段**
- 单元测试：测试每个模块
- 集成测试：测试模块间的配合
- 系统测试：测试整个系统

**5. 维护阶段**
- 修正错误
- 功能扩展
- 性能优化

### 三、程序设计的基本步骤

**步骤1：分析问题**
```
确定输入、输出
分析数据特点和约束条件
```

**步骤2：设计算法**
```
选择合适的数据结构
设计算法步骤
绘制流程图
```

**步骤3：编写代码**
```
根据算法编写代码
注意编码规范
添加注释
```

**步骤4：调试程序**
```
编译检查语法错误
运行检查逻辑错误
使用调试工具
```

**步骤5：测试验证**
```
设计测试用例
验证输入输出
边界条件测试
```

### 四、流程图

流程图是描述算法的图形工具。

**基本符号**
| 符号 | 名称 | 用途 |
|------|------|------|
| 椭圆 | 开始/结束 | 表示程序开始或结束 |
| 平行四边形 | 输入/输出 | 表示输入或输出操作 |
| 矩形 | 处理 | 表示处理或运算 |
| 菱形 | 判断 | 表示条件判断 |
| 箭头 | 流程线 | 表示执行方向 |

**流程图示例：判断成绩等级**
```
开始
  ↓
输入成绩score
  ↓
score>=90? ─是→ 输出"A"
  ↓否
score>=80? ─是→ 输出"B"
  ↓否
score>=60? ─是→ 输出"C"
  ↓否
输出"D"
  ↓
结束
```

### 五、伪代码

伪代码是介于自然语言和编程语言之间的描述方式。

**示例：判断闰年**
```
输入年份year
如果 year能被4整除 且 year不能被100整除
    输出 "是闰年"
否则如果 year能被400整除
    输出 "是闰年"
否则
    输出 "不是闰年"
```

**示例：求最大公约数**
```
输入 a, b
当 b不等于0
    t = b
    b = a % b
    a = t
输出 a
```

### 六、结构化程序设计

结构化程序设计的三种基本结构：

**顺序结构**
```
语句1
语句2
语句3
```

**选择结构**
```
如果 条件
    语句1
否则
    语句2
```

**循环结构**
```
当 条件成立
    循环体
```

### 七、学习建议

1. 先画流程图再写代码
2. 算法要清晰明了
3. 注意边界条件
4. 多做练习，熟能生巧
5. 参考经典算法的实现""",
            "summary": "软件开发包括需求分析、设计、编码、测试、维护五个阶段，流程图和伪代码是描述算法的工具",
            "code_example": """/*
 * 求两个数最大值的程序
 * 演示结构化程序设计
 */

#include <stdio.h>

int main(void) {
    int a, b, max;

    // 输入
    printf("请输入两个整数：");
    scanf("%d%d", &a, &b);

    // 处理（选择结构）
    if (a > b) {
        max = a;
    } else {
        max = b;
    }

    // 输出
    printf("最大值是：%d\\n", max);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了结构化程序设计的顺序、选择结构，展示了求最大值算法的实现",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["算法与流程图", "程序设计描述方法", "常见错误分析"],
            "tips": ["先画流程图再写代码", "算法要清晰明了", "注意边界条件"],
            "common_mistakes": ["算法步骤不完整", "忽略边界条件", "代码结构混乱"]
        }
    ]
}


async def generate():
    """生成第1章第1节知识点"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 查找C语言课程
        result = await db.execute(select(Course).where(Course.code == "C"))
        course = result.scalar_one_or_none()

        if not course:
            print("C语言课程不存在，请先运行init_db.py")
            return

        # 查找第1章
        result = await db.execute(
            select(Chapter).where(Chapter.course_id == course.id, Chapter.order_index == 1)
        )
        chapter = result.scalar_one_or_none()

        if not chapter:
            # 创建第1章
            chapter = Chapter(
                course_id=course.id,
                title="简单C程序设计",
                description="学习C语言的基本概念，包括程序结构、数据类型、输入输出等基础知识",
                content="""本章介绍C语言的基本概念，包括：
1. C程序的基本结构
2. 基本数据类型
3. 变量与常量
4. 格式化输入输出
5. 程序开发环境

通过本章学习，学生能够编写简单的C程序。""",
                order_index=1,
                estimated_minutes=120,
                difficulty_tags=["基础", "入门"],
                skill_tags=["程序结构", "数据类型", "输入输出"]
            )
            db.add(chapter)
            await db.flush()
            print(f"创建章节: {chapter.title}")

        # 查找或创建第1节
        result = await db.execute(
            select(Section).where(Section.chapter_id == chapter.id, Section.order_index == 1)
        )
        section = result.scalar_one_or_none()

        if not section:
            section = Section(
                chapter_id=chapter.id,
                title=SECTION_DATA["section_title"],
                description=SECTION_DATA["section_description"],
                order_index=SECTION_DATA["order_index"],
                estimated_minutes=SECTION_DATA["estimated_minutes"]
            )
            db.add(section)
            await db.flush()
            print(f"创建小节: {section.title}")
        else:
            # 删除现有知识点
            from sqlalchemy import delete, text
            await db.execute(text("DELETE FROM section_knowledge_points WHERE section_id = :sid"), {"sid": section.id})
            print(f"清空小节: {section.title}")

        # 插入知识点
        for kp_data in SECTION_DATA["knowledge_points"]:
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

        await db.commit()
        print(f"\\n第1章第1节生成完成！")
        print(f"小节名称: {SECTION_DATA['section_title']}")
        print(f"知识点数量: {len(SECTION_DATA['knowledge_points'])}个")


if __name__ == "__main__":
    asyncio.run(generate())
