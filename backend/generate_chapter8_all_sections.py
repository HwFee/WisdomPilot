"""Generate Chapter 8: 综合设计与应用 - 按教学大纲生成"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint
from sqlalchemy import select


CHAPTER_DATA = {
    "chapter_title": "综合设计与应用",
    "chapter_description": "学习变量的作用域、存储类别、指针与数组的深入关系、main函数参数、指针函数、动态存储分配等",
    "sections": [
        {
            "title": "变量的作用域与存储类别",
            "description": "变量的作用域、存储类别及变量的完整定义模式等",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "作用域与存储类别综合",
                    "order_index": 1,
                    "content": """## 作用域与存储类别综合

### 一、作用域完整回顾

| 作用域类型 | 说明 | 关键字 |
|------------|------|--------|
| 块作用域 | {}内 | 自动 |
| 函数原型作用域 | 函数原型参数 | - |
| 文件作用域 | 整个文件可见 | extern/static |
| 函数作用域 | goto标签 | - |

```c
// 文件作用域
static int globalVar = 100;  // 本文件可见
extern int anotherVar;        // 外部文件可见

int main() {
    // 块作用域
    int localVar = 10;
    if (localVar > 0) {
        int blockVar = 20;  // 块作用域
    }
    // blockVar在这里不可见
}
```

### 二、存储类别完整回顾

| 存储类别 | 关键字 | 存储位置 | 生命周期 | 作用域 |
|----------|--------|----------|----------|--------|
| 自动 | auto | 栈 | 函数结束 | 块 |
| 寄存器 | register | 寄存器 | 函数结束 | 块 |
| 静态 | static | 静态区 | 程序运行 | 局部/文件 |
| 外部 | extern | 静态区 | 程序运行 | 文件 |

### 三、static的双重含义

```c
// 1. 静态局部变量：持久存储
void counter() {
    static int count = 0;  // 只初始化一次，程序结束才销毁
    count++;
    printf("count = %d\\n", count);
}

// 2. 静态全局变量：限制作用域
static int fileScopeVar = 100;  // 只能在本文件访问
```

### 四、全局变量与局部变量

```c
int globalVar = 100;  // 全局变量，静态存储

void func() {
    int localVar = 10;  // 局部变量，自动存储

    // 访问全局变量（可能被局部变量遮蔽）
    printf("%d\\n", globalVar);     // 访问全局
    printf("%d\\n", ::globalVar);  // C++访问全局，C语言无此语法
}
```

### 五、变量的完整定义模式

```c
// [存储类别] [类型限定符] 类型 说明符 [初始化];
static const int ARR_SIZE = 100;
extern unsigned int flags;
register int counter;
```

### 六、函数链接属性

```c
// 默认函数链接属性为外部
extern int externalFunc();  // 其他文件可调用
static int internalFunc();   // 仅本文件可调用

// 使用场景
// .c文件
static int helper();  // 仅本文件使用的辅助函数
int publicAPI();      // 导出给其他文件的API
```

### 七、综合示例

```c
#include <stdio.h>

static int globalCounter = 0;  // 静态全局变量

int increment() {
    static int count = 0;  // 静态局部变量
    globalCounter++;
    count++;
    return count;
}

int main() {
    printf("第1次调用: count=%d, global=%d\\n", increment(), globalCounter);
    printf("第2次调用: count=%d, global=%d\\n", increment(), globalCounter);
    printf("第3次调用: count=%d, global=%d\\n", increment(), globalCounter);
    return 0;
}

// 输出:
// 第1次调用: count=1, global=1
// 第2次调用: count=2, global=2
// 第3次调用: count=3, global=3
```""",
                    "summary": "变量有作用域和存储期两个属性。static对局部变量是存储期属性，对全局变量是作用域属性。函数也有链接属性",
                    "code_example": """// 静态局部变量示例
void counter() {
    static int count = 0;  // 只初始化一次
    count++;
    printf("%d\\n", count);
}

int main() {
    counter();  // 1
    counter();  // 2
    counter();  // 3
    return 0;
}

// 静态全局变量
static int moduleVar = 100;  // 仅本文件可见
extern int sharedVar;          // 其他文件可见""",
                    "code_language": "c",
                    "code_explanation": "static局部变量count在函数调用间保持值，static全局变量moduleVar限制在本文件内可见",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["静态变量", "全局变量", "函数链接", "块作用域"],
                    "tips": "模块化编程中，非导出函数和变量应使用static限制作用域，避免命名冲突",
                    "common_mistakes": "1. 混淆static的双重含义；2. 过度使用全局变量；3. 函数和变量命名冲突"
                },
                {
                    "name": "多文件程序设计",
                    "order_index": 2,
                    "content": """## 多文件程序设计

### 一、多文件程序的概念

将程序分散到多个源文件，提高可维护性和编译效率：

```
project/
├── main.c        // 主函数
├── utils.h       // 头文件
├── utils.c       // 工具函数实现
├── calc.h        // 头文件
└── calc.c        // 计算函数实现
```

### 二、头文件的设计

```c
// calc.h
#ifndef CALC_H
#define CALC_H

// 导出函数声明
extern int add(int a, int b);
extern int subtract(int a, int b);
extern int multiply(int a, int b);
extern int divide(int a, int b);

// 导出常量
#define MAX_VALUE 1000

// 导出类型
typedef struct {
    int result;
    int error;
} CalcResult;

#endif
```

### 三、源文件实现

```c
// calc.c
#include "calc.h"

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    if (b == 0) return 0;
    return a / b;
}
```

### 四、主文件

```c
// main.c
#include <stdio.h>
#include "calc.h"

int main() {
    printf("10 + 5 = %d\\n", add(10, 5));
    printf("10 - 5 = %d\\n", subtract(10, 5));
    printf("10 * 5 = %d\\n", multiply(10, 5));
    printf("10 / 5 = %d\\n", divide(10, 5));
    return 0;
}
```

### 五、static的隐藏作用

```c
// utils.c
#include "utils.h"

static int helperFunction(int n) {  // 仅本文件可见
    // 内部实现
    return n * 2;
}

int publicFunction(int n) {
    return helperFunction(n) + 1;  // 可以调用static函数
}

// utils.h
extern int publicFunction(int n);  // 只需导出公开接口
```

### 六、编译多文件程序

```bash
# 分别编译
gcc -c main.c -o main.o
gcc -c calc.c -o calc.o
gcc -c utils.c -o utils.o

# 链接
gcc main.o calc.o utils.o -o program

# 或者一步到位
gcc main.c calc.c utils.c -o program

# 使用make（更高效）
make
```

### 七、常见问题

```c
// 1. 重复包含头文件
#ifndef _HEADER_H_
#define _HEADER_H_
// 内容
#endif

// 2. 循环引用（避免）
// a.h includes b.h
// b.h includes a.h  // 错误！

// 3. 变量声明与定义
// extern声明，定义在别处
extern int sharedVar;  // 声明
int sharedVar = 100;  // 定义
```""",
                    "summary": "多文件程序通过头文件声明接口，源文件实现功能。static函数/变量仅本文件可见，extern用于跨文件引用",
                    "code_example": """// file1.c
static int internalVar;  // 仅本文件可见
int externalVar;         // 其他文件可见

static void helper() {}   // 仅本文件可见
extern void api();        // 其他文件可见

// file2.c
extern int externalVar;   // 引用file1.c的变量
extern void api();        // 引用file1.c的函数""",
                    "code_language": "c",
                    "code_explanation": "static修饰的函数/变量只在本文件内可见，extern用于声明其他文件定义的变量或函数",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["静态变量", "extern关键字", "头文件", "编译链接"],
                    "tips": "头文件中只放声明不放定义，使用#ifndef防止重复包含",
                    "common_mistakes": "1. 头文件放变量定义导致重复定义；2. static误用导致函数不可访问；3. 忘记extern声明"
                }
            ]
        },
        {
            "title": "指针与数组深入",
            "description": "一维指针与一维数组的关系、一维指针与二维及多维数组的关系，多维指针与数组的关系",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "指针与数组关系深入",
                    "order_index": 1,
                    "content": """## 指针与数组关系深入

### 一、一维数组与指针

```c
int arr[5] = {1, 2, 3, 4, 5};
int *p = arr;  // p指向arr[0]

// arr[i] 等价于 *(arr + i)
// p[i]   等价于 *(p + i)

// 地址关系
arr      == &arr[0]
arr + 1  == &arr[1]
&arr[i]  == arr + i
```

### 二、指针算术运算

```c
int arr[] = {10, 20, 30, 40, 50};
int *p = arr;

p + 0   -> 10    *(p + 0)
p + 1   -> 20    *(p + 1)
p + 2   -> 30    *(p + 2)

// 指针相减
printf("%td\\n", p + 3 - p);  // 3（元素间隔）
```

### 三、数组指针（指向数组的指针）

```c
int arr[3][4];  // 3行4列的二维数组

// 数组指针：指向整个数组
int (*pArr)[4] = arr;  // pArr是指向包含4个int的数组的指针

// 访问元素
(*pArr)[0]     // arr[0][0]
pArr[1][2]     // arr[1][2]
```

### 四、二维数组与指针

```c
int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};

// 理解多层含义
matrix       -> int[3]*   指向一行（数组指针）
*matrix      -> int*      指向第一个元素
**matrix     -> int       第一个元素的值
matrix + 1   -> 跳过一行
*(matrix + 1) -> 指向第2行首元素
*(*(matrix + 1) + 2) -> matrix[1][2] = 6
```

### 五、指针数组与数组指针对比

```c
// 指针数组：数组元素是指针
int *arrPtr[3];  // 3个int*的数组

// 数组指针：指向数组的指针
int (*ptrToArr)[3];  // 指向包含3个int的数组的指针

// 对比
int value = 10;
int *ptr = &value;
int arr[3] = {1, 2, 3};

arrPtr[0] = ptr;  // 存放指针
ptrToArr = &arr;  // 存放数组地址
```

### 六、多维数组的指针参数

```c
// 二维数组参数
void printMatrix(int (*matrix)[3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}

// 三维数组参数
void process3D(int (*cube)[4][3], int n) {
    // cube是指向int[4][3]的指针
}
```

### 七、综合示例

```c
#include <stdio.h>

int main() {
    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};

    // 不同指针类型
    int *p1 = matrix[0];        // 指向第一行第一个元素
    int (*p2)[3] = matrix;      // 指向整个二维数组的一行
    int *p3 = (int *)matrix;    // 强制转为一维指针

    printf("p1[2] = %d\\n", p1[2]);  // 3
    printf("p2[1][2] = %d\\n", p2[1][2]);  // 6
    printf("p3[3] = %d\\n", p3[3]);  // 4

    // 指针运算
    printf("*(matrix[1] + 2) = %d\\n", *(matrix[1] + 2));  // 6
    printf("*(*(matrix + 1) + 2) = %d\\n", *(*(matrix + 1) + 2));  // 6
    return 0;
}
```""",
                    "summary": "数组名退化为指针，指针算术遵循类型。多维数组需要数组指针正确处理。int(*p)[n]是指向n个int数组的指针",
                    "code_example": """int matrix[2][3] = {{1,2,3},{4,5,6}};

// 访问方式
*(*(matrix + 1) + 2)  // 6
matrix[1][2]           // 6
*matrix[1] + 2         // &matrix[1][2]

// 数组指针
int (*p)[3] = matrix;  // p指向一维数组int[3]
p[1][2]                // 6

// 指针数组
int *arr[2] = {matrix[0], matrix[1]};
arr[1][2]              // 6""",
                    "code_language": "c",
                    "code_explanation": "matrix是指向int[3]的指针，*matrix是int*。int(*p)[3]声明了指向3元素数组的数组指针",
                    "difficulty": 3,
                    "importance": 5,
                    "related_points": ["指针基础", "二维数组", "指针数组", "函数参数传递"],
                    "tips": "函数参数声明二维数组时第二维必须指定，int matrix[][3]等价于int (*matrix)[3]",
                    "common_mistakes": "1. 混淆数组指针和指针数组；2. 二维数组参数第二维未指定；3. 指针算术类型错误"
                }
            ]
        },
        {
            "title": "main函数参数与命令行",
            "description": "main()的精确表达方式及参数的用法",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "main函数参数详解",
                    "order_index": 1,
                    "content": """## main函数参数详解

### 一、main函数的两种形式

```c
// 标准形式
int main(int argc, char *argv[]) {
    // argc: 参数个数
    // argv: 参数数组
    return 0;
}

// 等价形式
int main(int argc, char **argv) {
    return 0;
}
```

### 二、参数含义

| 参数 | 含义 |
|------|------|
| argc | 参数个数，包括程序名自身 |
| argv[0] | 程序名（可执行文件路径） |
| argv[1] ~ argv[argc-1] | 命令行参数 |
| argv[argc] | NULL（哨兵） |

### 三、示例程序

```bash
$ ./program hello world 123
```

```c
// argv内存布局
argv[0] -> "./program"  (程序名)
argv[1] -> "hello"
argv[2] -> "world"
argv[3] -> "123"
argv[4] -> NULL

// argc = 5
```

### 四、基本使用

```c
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("程序名: %s\\n", argv[0]);
    printf("参数个数: %d\\n", argc);

    printf("所有参数:\\n");
    for (int i = 0; i < argc; i++) {
        printf("  argv[%d] = %s\\n", i, argv[i]);
    }

    return 0;
}
```

### 五、参数解析示例

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int verbose = 0;
    char *inputFile = NULL;
    char *outputFile = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = 1;
        } else if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            inputFile = argv[++i];
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            outputFile = argv[++i];
        } else if (argv[i][0] == '-') {
            fprintf(stderr, "未知选项: %s\\n", argv[i]);
            return 1;
        }
    }

    if (verbose) {
        printf("输入文件: %s\\n", inputFile ? inputFile : "(无)");
        printf("输出文件: %s\\n", outputFile ? outputFile : "(无)");
    }

    return 0;
}
```

### 六、环境变量

```c
#include <stdio.h>
extern char **environ;  // 环境变量数组

int main() {
    printf("环境变量:\\n");
    for (char **env = environ; *env != NULL; env++) {
        printf("%s\\n", *env);
    }
    return 0;
}
```

### 七、getopt函数（Unix）

```c
#include <unistd.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
    int flag = 0;
    int digit_optind = 0;

    int c;
    while ((c = getopt(argc, argv, "abf:v")) != -1) {
        switch (c) {
            case 'a':
                printf("选项: a\\n");
                break;
            case 'b':
                printf("选项: b\\n");
                break;
            case 'f':
                printf("选项: f, 值=%s\\n", optarg);
                break;
            case 'v':
                printf("选项: v (verbose)\\n");
                break;
            case '?':
                printf("未知选项或缺少参数\\n");
                break;
        }
    }

    printf("非选项参数:\\n");
    for (int i = optind; i < argc; i++) {
        printf("  %s\\n", argv[i]);
    }

    return 0;
}
```""",
                    "summary": "main函数接收命令行参数，argc是参数个数，argv是参数数组（argv[0]是程序名）。环境变量通过environ访问",
                    "code_example": """int main(int argc, char *argv[]) {
    // 遍历所有参数
    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = %s\\n", i, argv[i]);
    }

    // 环境变量
    extern char **environ;
    for (char **e = environ; *e; e++) {
        printf("%s\\n", *e);
    }
}

// 运行: ./prog hello world
// argc = 3
// argv = {"./prog", "hello", "world", NULL}""",
                    "code_language": "c",
                    "code_explanation": "argv[0]是程序名，argv[1]开始是用户输入的参数，argv[argc]是NULL。遍历时注意边界检查",
                    "difficulty": 2,
                    "importance": 3,
                    "related_points": ["命令行参数解析", "环境变量", "字符串处理", "getopt"],
                    "tips": "使用getopt等库函数解析命令行参数更规范可靠",
                    "common_mistakes": "1. 忘记argv[0]是程序名；2. 不检查argv[i]是否越界；3. 忘记optind初始化"
                }
            ]
        },
        {
            "title": "指针函数与动态内存",
            "description": "指针型函数的定义与使用方法，指针的动态存储空间分配的方法，设计时的注意事项等",
            "order_index": 4,
            "knowledge_points": [
                {
                    "name": "指针函数与函数指针",
                    "order_index": 1,
                    "content": """## 指针函数与函数指针

### 一、指针函数（返回指针的函数）

```c
// 指针函数：返回指针的函数
返回类型 *函数名(参数列表);

// 示例：返回字符串
const char* getDayName(int day) {
    static const char *names[] = {
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    };
    if (day >= 1 && day <= 7) {
        return names[day - 1];
    }
    return NULL;
}

// 示例：返回动态分配的内存
int* createArray(int size) {
    int *p = malloc(size * sizeof(int));
    if (p) {
        for (int i = 0; i < size; i++) {
            p[i] = i;
        }
    }
    return p;
}
```

### 二、函数指针（指向函数的指针）

```c
// 函数指针：指向函数的指针
返回类型 (*指针名)(参数类型列表);

// 示例
int (*funcPtr)(int, int);  // 指向返回int、接收两个int的函数

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

int main() {
    funcPtr = add;        // 指向add
    printf("%d\\n", funcPtr(3, 2));  // 5

    funcPtr = sub;         // 指向sub
    printf("%d\\n", funcPtr(3, 2));  // 1
    return 0;
}
```

### 三、指针函数 vs 函数指针

| 类型 | 语法 | 含义 |
|------|------|------|
| 指针函数 | int* func() | 返回int*的函数 |
| 函数指针 | int (*fp)() | 指向返回int的函数的指针 |

```c
// 指针函数：返回指针
int* allocateArray(int size) { ... }

// 函数指针：指向函数
int (*handler)(int, int);
```

### 四、函数指针作为参数（回调）

```c
int calculate(int a, int b, int (*op)(int, int)) {
    return op(a, b);
}

int add(int a, int b) { return a + b; }
int mul(int a, int b) { return a * b; }

int main() {
    printf("%d\\n", calculate(10, 5, add));  // 15
    printf("%d\\n", calculate(10, 5, mul));  // 50
    return 0;
}
```

### 五、返回指针的注意事项

```c
// 错误1：返回局部变量地址
const char* badFunction() {
    char str[] = "Hello";  // 局部数组
    return str;  // 危险！str将被销毁
}

// 错误2：返回参数地址（参数在栈上，函数结束后销毁）
const char* badFunction2(char *s) {
    return s;  // 如果s是局部变量则危险
}

// 正确1：返回静态变量地址
const char* goodFunction1() {
    static const char *msg = "Hello";
    return msg;
}

// 正确2：返回动态分配内存
const char* goodFunction2() {
    char *p = malloc(10);
    strcpy(p, "Hello");
    return p;  // 调用者需要free
}

// 正确3：返回字符串常量
const char* goodFunction3() {
    return "Hello";  // 常量区，永远有效
}
```""",
                    "summary": "指针函数返回指针，可能是动态内存、静态变量或字符串常量。函数指针指向函数，可作为回调。返回指针时不能返回局部变量地址",
                    "code_example": """// 指针函数
int* createArray(int n) {
    int *p = malloc(n * sizeof(int));
    return p;  // 调用者负责free
}

// 函数指针
int (*op)(int, int) = add;  // op指向add
printf("%d\\n", op(3, 2));     // 5

// 回调函数
int apply(int x, int y, int (*f)(int,int)) {
    return f(x, y);
}
apply(10, 5, add);  // 15""",
                    "code_language": "c",
                    "code_explanation": "指针函数返回malloc的内存需要free。函数指针op指向add，op(3,2)即add(3,2)",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["动态内存分配", "函数指针", "回调函数", "字符串返回"],
                    "tips": "返回指针的函数要明确返回的是静态内存、动态内存还是字符串常量",
                    "common_mistakes": "1. 返回局部变量地址；2. 返回malloc后忘记free；3. 混淆指针函数和函数指针语法"
                },
                {
                    "name": "动态内存分配",
                    "order_index": 2,
                    "content": """## 动态内存分配

### 一、内存区域划分

```
程序内存布局：
┌────────────────┐ 高地址
│     代码区      │  代码
├────────────────┤
│     全局区      │  全局变量、静态变量
├────────────────┤
│     堆区       │  malloc/free 管理
│     (heap)     │
│                │
├────────────────┤
│     栈区       │  函数参数、局部变量
│     (stack)    │
└────────────────┘ 低地址
```

### 二、malloc和free

```c
#include <stdlib.h>
#include <stdio.h>

int main() {
    // 分配内存
    int *p = (int *)malloc(sizeof(int));
    if (p == NULL) {
        printf("分配失败\\n");
        return 1;
    }

    *p = 100;
    printf("%d\\n", *p);

    // 释放内存
    free(p);
    p = NULL;  // 避免悬空指针

    return 0;
}
```

### 三、分配数组内存

```c
// 分配整型数组
int *arr = (int *)malloc(n * sizeof(int));
if (arr == NULL) { /* 错误处理 */ }

// 使用
for (int i = 0; i < n; i++) {
    arr[i] = i;
}

// 释放
free(arr);
arr = NULL;
```

### 四、realloc调整大小

```c
int *arr = (int *)malloc(5 * sizeof(int));

// 扩大到10个元素
int *newArr = (int *)realloc(arr, 10 * sizeof(int));
if (newArr == NULL) {
    free(arr);  // 原来的arr仍然有效
    return 1;
}
arr = newArr;  // 更新指针

// 缩小可以直接realloc
arr = (int *)realloc(arr, 3 * sizeof(int));
```

### 五、calloc（分配并初始化为0）

```c
// malloc + memset
int *arr = (int *)calloc(n, sizeof(int));
// 等价于:
// int *arr = (int *)malloc(n * sizeof(int));
// memset(arr, 0, n * sizeof(int));
```

### 六、常见错误

```c
// 错误1：内存泄漏
void leak() {
    int *p = malloc(sizeof(int));
    *p = 100;
    // 忘记free
    return;  // p丢失，内存泄漏
}

// 错误2：重复释放
free(p);
free(p);  // 危险！未定义行为

// 错误3：释放非动态内存
int arr[10];
free(arr);  // 错误！arr不是malloc分配的

// 错误4：访问已free的内存
free(p);
*p = 100;   // 危险！悬空指针
```

### 七、二级指针与动态数组

```c
// 动态分配二维数组
int rows = 3, cols = 4;
int **matrix = (int **)malloc(rows * sizeof(int *));
for (int i = 0; i < rows; i++) {
    matrix[i] = (int *)malloc(cols * sizeof(int));
}

// 释放
for (int i = 0; i < rows; i++) {
    free(matrix[i]);
}
free(matrix);

// 一维数组模拟二维
int **matrix = (int **)malloc(rows * sizeof(int *));
matrix[0] = (int *)malloc(rows * cols * sizeof(int));
for (int i = 1; i < rows; i++) {
    matrix[i] = matrix[0] + i * cols;
}
```

### 八、综合示例

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char name[30];
    int age;
    float score;
} Student;

Student* createStudent(const char *name, int age, float score) {
    Student *p = (Student *)malloc(sizeof(Student));
    if (p) {
        strncpy(p->name, name, 29);
        p->name[29] = '\\0';
        p->age = age;
        p->score = score;
    }
    return p;
}

int main() {
    Student **class = (Student **)malloc(3 * sizeof(Student *));
    if (class == NULL) return 1;

    class[0] = createStudent("Alice", 20, 92.5);
    class[1] = createStudent("Bob", 19, 88.0);
    class[2] = createStudent("Charlie", 21, 95.0);

    for (int i = 0; i < 3; i++) {
        printf("%s %d %.1f\\n",
            class[i]->name, class[i]->age, class[i]->score);
        free(class[i]);  // 释放每个学生
    }
    free(class);  // 释放指针数组

    return 0;
}
```""",
                    "summary": "动态内存从堆区分配，malloc分配free释放，calloc分配并初始化为0，realloc调整大小。malloc返回NULL要检查，free后指针要置NULL",
                    "code_example": """// 分配
int *p = (int*)malloc(sizeof(int));
int *arr = (int*)malloc(n * sizeof(int));

// 释放
free(p);
free(arr);
p = NULL;
arr = NULL;

// 调整大小
arr = (int*)realloc(arr, newSize * sizeof(int));

// 分配结构体
Student *s = (Student*)malloc(sizeof(Student));
free(s);""",
                    "code_language": "c",
                    "code_explanation": "malloc分配指定字节内存，free释放。分配后检查NULL，释放后置NULL避免悬空指针",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["指针函数", "内存布局", "malloc/calloc/realloc", "内存泄漏"],
                    "tips": "malloc/free要配对，分配即检查返回值，释放即将指针置NULL避免悬空指针",
                    "common_mistakes": "1. 忘记检查malloc返回值NULL；2. 内存泄漏（malloc后忘记free）；3. free后继续使用指针"
                }
            ]
        }
    ]
}


async def save_chapter8(db):
    """保存第8章数据到数据库"""

    result = await db.execute(
        select(Course).where(Course.name.like('%C语言%'))
    )
    course = result.scalar_one_or_none()
    if not course:
        print("错误：未找到C语言课程！")
        return None

    result = await db.execute(
        select(Chapter).where(
            Chapter.course_id == course.id,
            Chapter.title == CHAPTER_DATA["chapter_title"]
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        result = await db.execute(
            select(Chapter).where(Chapter.course_id == course.id)
        )
        chapter_count = len(result.all())

        chapter = Chapter(
            course_id=course.id,
            title=CHAPTER_DATA["chapter_title"],
            description=CHAPTER_DATA["chapter_description"],
            order_index=chapter_count + 1
        )
        db.add(chapter)
        await db.flush()
        print(f"创建章节：{chapter.title}")
    else:
        print(f"使用已有章节：{chapter.title}")
        result = await db.execute(
            select(Section).where(Section.chapter_id == chapter.id)
        )
        old_sections = result.scalars().all()
        for sec in old_sections:
            await db.execute(
                SectionKnowledgePoint.__table__.delete().where(
                    SectionKnowledgePoint.section_id == sec.id
                )
            )
        for sec in old_sections:
            await db.delete(sec)
        await db.flush()

    total_points = 0
    for section_data in CHAPTER_DATA["sections"]:
        section = Section(
            chapter_id=chapter.id,
            title=section_data["title"],
            description=section_data["description"],
            order_index=section_data["order_index"]
        )
        db.add(section)
        await db.flush()

        for kp_data in section_data["knowledge_points"]:
            kp = SectionKnowledgePoint(
                section_id=section.id,
                name=kp_data["name"],
                content=kp_data["content"],
                summary=kp_data.get("summary", ""),
                code_example=kp_data.get("code_example", ""),
                code_language=kp_data.get("code_language", "c"),
                code_explanation=kp_data.get("code_explanation", ""),
                difficulty=kp_data.get("difficulty", 1),
                importance=kp_data.get("importance", 3),
                related_points=",".join(kp_data.get("related_points", [])) if kp_data.get("related_points") else "",
                tips=kp_data.get("tips", ""),
                common_mistakes=kp_data.get("common_mistakes", ""),
                order_index=kp_data.get("order_index", 1)
            )
            db.add(kp)
            total_points += 1

        print(f"  [{section.title}] {len(section_data['knowledge_points'])}个知识点")

    await db.commit()
    return total_points


async def main():
    async with AsyncSessionLocal() as db:
        total = await save_chapter8(db)
        if total:
            print(f"\n第8章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
