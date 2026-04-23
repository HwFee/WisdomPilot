"""Generate Chapter 4: 模块化设计与应用 - 按教学大纲生成"""
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
    "chapter_title": "模块化设计与应用",
    "chapter_description": "学习C语言的模块化程序设计方法，包括函数定义、调用、参数传递及预处理指令",
    "sections": [
        {
            "title": "模块化程序设计概述",
            "description": "模块化程序设计方法及模块化程序设计的要点",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "模块化程序设计概念",
                    "order_index": 1,
                    "content": """## 模块化程序设计概念

模块化程序设计是一种将复杂程序分解为若干独立模块进行设计和编写的方法。

### 一、为什么需要模块化

**传统开发方式的问题：**
- 代码重复利用困难
- 调试和维护困难
- 难以团队协作开发
- 代码可读性差

```c
// 一个巨大的main函数
int main() {
    // 输入数据... 100行
    // 处理数据... 200行
    // 输出结果... 100行
    // 错误处理... 50行
    return 0;
}
```

**模块化开发方式：**
```c
// 主程序结构清晰
int main() {
    int data = inputData();
    int result = processData(data);
    outputResult(result);
    return 0;
}
```

### 二、模块化的核心思想

1. **分而治之**：将大问题分解为小问题
2. **信息隐藏**：模块内部实现细节对外部透明
3. **高内聚低耦合**：模块内部紧密相关，模块之间联系松散
4. **可复用性**：一次开发，多次使用

### 三、模块化的层次结构

| 层次 | 说明 | 示例 |
|------|------|------|
| 程序 | 完整程序 | 整个学生成绩管理系统 |
| 模块/文件 | 功能独立的部分 | input.c、process.c、output.c |
| 函数 | 模块的具体实现 | inputStudent()、calcAverage() |
| 语句块 | 函数内的逻辑单元 | if判断、循环等 |

### 四、函数是模块化的基本单位

在C语言中，函数是模块化的基本单位：

```c
// 模块化设计示例：计算器
#include <stdio.h>

// 函数声明（接口）
void showMenu();
int add(int a, int b);
int subtract(int a, int b);
int multiply(int a, int b);
float divide(int a, int b);

int main() {
    int choice, a, b;
    while (1) {
        showMenu();
        scanf("%d", &choice);
        if (choice == 5) break;
        printf("输入两个数：");
        scanf("%d %d", &a, &b);

        switch (choice) {
            case 1: printf("结果：%d\\n", add(a, b)); break;
            case 2: printf("结果：%d\\n", subtract(a, b)); break;
            case 3: printf("结果：%d\\n", multiply(a, b)); break;
            case 4: printf("结果：%.2f\\n", divide(a, b)); break;
        }
    }
    return 0;
}

// 函数定义（实现）
void showMenu() {
    printf("1.加法 2.减法 3.乘法 4.除法 5.退出\\n");
}

int add(int a, int b) { return a + b; }
int subtract(int a, int b) { return a - b; }
int multiply(int a, int b) { return a * b; }
float divide(int a, int b) { return (float)a / b; }
```

### 五、模块化的优点

1. **提高代码可读性**：每个函数职责明确
2. **便于调试**：可单独测试每个函数
3. **促进复用**：相同功能可被不同程序调用
4. **支持团队开发**：不同人可负责不同模块
5. **易于维护**：修改一个模块不影响其他模块""",
                    "summary": "模块化程序设计将复杂程序分解为独立模块，核心思想是分而治之、信息隐藏、高内聚低耦合。函数是C语言模块化的基本单位",
                    "code_example": """// 模块化计算器示例
#include <stdio.h>

int add(int a, int b) { return a + b; }
int subtract(int a, int b) { return a - b; }
int multiply(int a, int b) { return a * b; }
float divide(int a, int b) { return (float)a / b; }

int main() {
    int a = 10, b = 5;
    printf("%d + %d = %d\\n", a, b, add(a, b));
    printf("%d - %d = %d\\n", a, b, subtract(a, b));
    printf("%d * %d = %d\\n", a, b, multiply(a, b));
    printf("%d / %d = %.2f\\n", a, b, divide(a, b));
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "模块化将计算器功能分解为add、subtract、multiply、divide四个函数，每个函数独立实现一个功能，main函数负责调度",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["函数的定义与声明", "函数调用", "函数参数传递", "预处理指令"],
                    "tips": "模块化设计时，每个函数应该'做一件事且做好一件事'。函数长度一般控制在20-50行内",
                    "common_mistakes": "1. 函数设计过于臃肿，承担太多功能；2. 模块间耦合度过高；3. 函数命名不清晰"
                },
                {
                    "name": "函数的基本概念",
                    "order_index": 2,
                    "content": """## 函数的基本概念

### 一、函数的定义

函数定义包括函数名、参数列表、返回类型和函数体：

```c
返回类型 函数名(参数列表) {
    // 函数体
    return 返回值;
}
```

**示例：**
```c
// 求两个整数最大值的函数
int max(int a, int b) {
    if (a > b)
        return a;
    else
        return b;
}

// 无参数无返回值的函数
void printHello() {
    printf("Hello!\\n");
}
```

### 二、函数的分类

| 分类标准 | 函数类型 | 说明 |
|----------|----------|------|
| 有无返回值 | 有返回值函数 | 返回一个计算结果 |
| | 无返回值函数 | 执行操作但不返回结果（void） |
| 有无参数 | 有参函数 | 需要传入数据 |
| | 无参函数 | 不需要传入数据 |
| 用户定义 | 标准库函数 | 如printf、scanf、strlen等 |
| | 用户自定义函数 | 程序员根据需要编写 |

### 三、函数声明与调用

**函数声明（函数原型）：**
```c
返回类型 函数名(参数类型列表);
// 示例
int max(int a, int b);
void printArray(int arr[], int n);
```

**函数调用：**
```c
函数名(实参列表);

// 示例
int result = max(10, 20);  // 有返回值
printHello();              // 无返回值
```

### 四、函数执行的流程

```
主调函数
    ↓ 调用
被调函数（执行函数体）
    ↓返回
主调函数（继续执行后续代码）
```

### 五、return语句详解

```c
// 返回值
return 表达式;     // 返回表达式的值
return (表达式);   // 等价于上面的形式

// 无返回值
return;           // 用于void函数

// 注意事项
return 1;         // 返回整数值1
return (1);       // 同上
return 3.14;      // 如果函数返回类型是int，会丢失小数部分
```

### 六、函数设计原则

1. **单一职责**：每个函数只完成一个功能
2. **命名规范**：函数名应反映其功能
   ```c
   // 好命名
   int calculateAverage(int scores[], int n);
   void sortArray(int arr[], int n);

   // 差命名
   int calc(int s[], int n);      // calc太模糊
   void func1();                   // 不知所云
   ```

3. **参数合理**：参数不宜过多（最好不超过5个）
4. **避免副作用**：除非必要，函数不应修改全局变量""",
                    "summary": "函数定义包括返回类型、函数名、参数列表和函数体。分为有返回值和无返回值、有参和无参函数。return语句用于返回值",
                    "code_example": """// 完整的函数示例
#include <stdio.h>

// 函数声明
int max(int a, int b);
int min(int a, int b);
void swap(int *x, int *y);

int main() {
    int a = 10, b = 20;
    printf("最大值：%d\\n", max(a, b));
    printf("最小值：%d\\n", min(a, b));

    printf("交换前：a=%d, b=%d\\n", a, b);
    swap(&a, &b);
    printf("交换后：a=%d, b=%d\\n", a, b);
    return 0;
}

// 函数定义
int max(int a, int b) {
    return (a > b) ? a : b;
}

int min(int a, int b) {
    return (a < b) ? a : b;
}

void swap(int *x, int *y) {
    int temp = *x;
    *x = *y;
    *y = temp;
}""",
                    "code_language": "c",
                    "code_explanation": "max和min函数返回整数值，swap函数通过指针交换两个数的值，避免了值传递的问题",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["函数的定义与声明", "函数调用", "函数参数传递", "变量作用域"],
                    "tips": "函数名应使用动词或动词短语，如calculate、print、find等。返回类型void表示无返回值",
                    "common_mistakes": "1. 函数返回类型不匹配；2. 忘记return语句；3. return后继续执行函数体"
                }
            ]
        },
        {
            "title": "函数的定义与调用",
            "description": "函数的定义、声明、使用及应用实例",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "函数定义详解",
                    "order_index": 1,
                    "content": """## 函数定义详解

### 一、函数定义的基本形式

```c
返回类型 函数名(参数列表) {
    // 函数体
    return 返回值;
}
```

**完整示例：**
```c
// 计算整数平方
int square(int x) {
    return x * x;
}

// 判断闰年
int isLeapYear(int year) {
    if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0))
        return 1;  // 是闰年
    else
        return 0;  // 不是闰年
}
```

### 二、参数列表的规范

```c
// 单个参数
int square(int x)

// 多个参数（逗号分隔）
int max(int a, int b)
int calc(int x, int y, int z)

// 无参数（用void或空括号）
int getCount(void)
int getCount()  // 两种形式等价
```

### 三、返回类型详解

**1. 基本类型返回**
```c
int add(int a, int b) { return a + b; }
double average(int a, int b) { return (a + b) / 2.0; }
char toUpper(char c) { return c - 32; }
```

**2. 无返回值（void）**
```c
void printBanner() {
    printf("============\\n");
    printf("  Welcome!  \\n");
    printf("============\\n");
    // 没有return语句
}
```

**3. 返回指针**
```c
char* greet(char *name) {
    static char buffer[100];
    sprintf(buffer, "Hello, %s!", name);
    return buffer;
}
```

### 四、函数体的结构

```c
// 标准函数体结构
返回类型 函数名(参数列表) {
    // 1. 变量声明（可选）
    int local_var;

    // 2. 输入处理（可选）

    // 3. 主要逻辑
    // ...

    // 4. 返回结果
    return 结果;
}
```

### 五、函数定义的注意事项

1. **不能嵌套定义**：C语言不允许在函数内部定义另一个函数
   ```c
   // 错误！
   int outer() {
       int inner() {  // 不允许
           return 0;
       }
   }
   ```

2. **函数名不能重复**：同一作用域内不能有同名函数
   ```c
   // 错误！
   int max(int a, int b) { return a > b ? a : b; }
   int max(int x, int y) { return x > y ? x : y; }  // 重定义错误
   ```

3. **返回类型默认为int**：历史兼容性
   ```c
   // 不推荐
   add(a, b) { return a + b; }  // 默认返回int

   // 推荐：明确声明返回类型
   int add(int a, int b) { return a + b; }
   ```

### 六、函数定义的练习

```c
// 练习1：阶乘函数
int factorial(int n) {
    int result = 1;
    for (int i = 1; i <= n; i++) {
        result *= i;
    }
    return result;
}

// 练习2：绝对值函数
int absValue(int n) {
    return n >= 0 ? n : -n;
}

// 练习3：判断素数
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;
    for (int i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return 0;
    }
    return 1;
}""",
                    "summary": "函数定义包括返回类型、函数名、参数列表和函数体。C语言不允许函数嵌套定义，函数名不能重复，返回类型默认为int",
                    "code_example": """// 阶乘函数
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// 判断素数
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;
    for (int i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return 0;
    }
    return 1;
}

// 主函数调用
int main() {
    printf("5! = %d\\n", factorial(5));   // 120
    printf("7是素数：%d\\n", isPrime(7)); // 1
    printf("8是素数：%d\\n", isPrime(8)); // 0
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "factorial使用递归计算阶乘，isPrime通过试除法判断素数只需检查到sqrt(n)",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["函数声明", "函数调用", "函数参数传递", "递归函数"],
                    "tips": "推荐始终显式声明返回类型，避免使用默认int类型。函数体内部不要定义其他函数",
                    "common_mistakes": "1. 尝试在函数内部定义函数；2. 返回类型不匹配；3. 函数参数类型遗漏"
                },
                {
                    "name": "函数声明与调用详解",
                    "order_index": 2,
                    "content": """## 函数声明与调用详解

### 一、函数声明（函数原型）

**为什么需要函数声明：**
- 编译器从上往下处理代码
- 如果调用在前、定义在后，需要提前声明

```c
// 场景：main函数调用printMenu，但printMenu定义在main之后
int main() {
    printMenu();  // 编译错误！编译器不知道printMenu的存在
    return 0;
}

void printMenu() {  // 定义在main之后
    printf("1. 新游戏\\n");
    printf("2. 继续游戏\\n");
}
```

**正确做法 - 添加函数声明：**
```c
// 函数声明（告诉编译器这个函数存在）
void printMenu();

int main() {
    printMenu();  // 现在可以调用了
    return 0;
}

void printMenu() {  // 定义
    printf("1. 新游戏\\n");
    printf("2. 继续游戏\\n");
}
```

### 二、函数声明的语法

```c
返回类型 函数名(参数类型列表);
// 示例
int max(int a, int b);
void printArray(int arr[], int n);
double calc(double x, double y, double z);
char* strCopy(char dest[], const char src[]);

// 参数名可以省略，只写类型
int max(int, int);
```

### 三、函数调用的过程

```c
int square(int x) {
    return x * x;
}

int main() {
    int result = square(5);  // 函数调用
    return 0;
}
```

**调用时发生了什么：**
1. 传递参数（将5传给x）
2. 保存调用点的返回地址
3. 跳转到square函数执行
4. 函数执行完成后返回结果
5. 回到调用点继续执行

### 四、函数调用的形式

**1. 作为表达式的一部分**
```c
int a = max(3, 4) + 10;  // max(3,4)返回4，a=14
```

**2. 作为另一个函数的参数**
```c
printf("最大值：%d\\n", max(a, b));
```

**3. 作为另一个函数的实参**
```c
int arr[5] = {3, 1, 4, 1, 5};
sort(arr, 5);  // 假设sort接受数组和长度
```

**4. 单独调用（无返回值函数）**
```c
printWelcome();  // void函数调用
```

### 五、函数调用栈

```c
void funcA() { funcB(); }
void funcB() { funcC(); }
void funcC() { printf("Hello!\\n"); }

int main() {
    funcA();  // 调用顺序：main -> A -> B -> C
    return 0;
}
```

**栈的变化：**
```
调用时（进栈）：
main -> funcA -> funcB -> funcC

返回时（出栈）：
C返回 -> B返回 -> A返回 -> main继续
```

### 六、函数调用的注意事项

1. **实参形参要匹配**
   ```c
   // 声明
   int max(int a, int b);

   // 调用
   max(3, 4);      // 正确：两个int参数
   max(3);         // 错误：参数不足
   max(3, 4, 5);   // 错误：参数过多
   ```

2. **参数类型自动转换**
   ```c
   int square(int x) { return x * x; }

   int main() {
       int a = square(3);    // 正确：int -> int
       double b = square(3); // 正确但可能丢失精度
       return 0;
   }
   ```

3. **函数不能调用自己（除非使用递归）**""",
                    "summary": "函数声明告诉编译器函数的存在，函数调用执行函数体并可获得返回值。调用时发生参数传递、跳转执行、返回结果的过程",
                    "code_example": """#include <stdio.h>

// 函数声明
int max(int a, int b);
int min(int a, int b);
void swap(int *x, int *y);

int main() {
    int a = 10, b = 20;
    printf("较大值：%d\\n", max(a, b));
    printf("较小值：%d\\n", min(a, b));
    swap(&a, &b);
    printf("交换后：a=%d, b=%d\\n", a, b);
    return 0;
}

// 函数定义
int max(int a, int b) {
    return (a > b) ? a : b;
}

int min(int a, int b) {
    return (a < b) ? a : b;
}

void swap(int *x, int *y) {
    int temp = *x;
    *x = *y;
    *y = temp;
}""",
                    "code_language": "c",
                    "code_explanation": "通过函数声明使main函数能调用定义在后面的函数。swap使用指针参数实现原地交换",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["函数定义详解", "函数参数传递", "递归函数", "变量作用域"],
                    "tips": "推荐把函数声明放在头文件，函数定义放在源文件。调用函数时实参必须与形参类型匹配",
                    "common_mistakes": "1. 调用未声明的函数；2. 实参形参类型不匹配；3. 忽略函数返回值"
                }
            ]
        },
        {
            "title": "函数参数传递",
            "description": "函数参数传递的方式及函数设计的基本原则",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "值传递与地址传递",
                    "order_index": 1,
                    "content": """## 值传递与地址传递

### 一、值传递（Pass by Value）

**概念**：将实参的值复制一份传递给形参，函数内部对形参的修改不影响实参。

```c
void increment(int x) {
    x++;  // 修改的是形参x
    printf("函数内：x = %d\\n", x);
}

int main() {
    int a = 10;
    increment(a);  // a的值10传递给x
    printf("函数外：a = %d\\n", a);  // a仍然是10
    return 0;
}
```

**执行结果：**
```
函数内：x = 11
函数外：a = 10
```

**图示：**
```
调用前：
    a = 10
    [  a  ] ──复制──> [  x  ] = 10

函数内修改x++后：
    a = 10        x = 11
    [  a  ]       [  x  ]  (两者独立)

函数结束后，x被销毁，a不受影响
```

### 二、地址传递（Pass by Pointer）

**概念**：将实参的地址传递给形参，函数内部通过地址访问和修改实参。

```c
void increment(int *p) {
    (*p)++;  // 通过指针修改实参
    printf("函数内：*p = %d\\n", *p);
}

int main() {
    int a = 10;
    increment(&a);  // 传递a的地址
    printf("函数外：a = %d\\n", a);  // a变为11
    return 0;
}
```

**执行结果：**
```
函数内：*p = 11
函数外：a = 11
```

### 三、值传递与地址传递对比

| 特性 | 值传递 | 地址传递 |
|------|--------|----------|
| 传递内容 | 值的副本 | 地址（指针） |
| 修改效果 | 不影响实参 | 影响实参 |
| 数据量 | 小（固定大小） | 更小（只传地址） |
| 安全性 | 更安全 | 需要注意指针有效性 |

### 四、地址传递的典型应用

**1. 交换两个数的值**
```c
void swap(int *x, int *y) {
    int temp = *x;
    *x = *y;
    *y = temp;
}

int main() {
    int a = 10, b = 20;
    swap(&a, &b);  // a=20, b=10
    return 0;
}
```

**2. 返回多个值**
```c
void divide(int a, int b, int *quotient, int *remainder) {
    *quotient = a / b;
    *remainder = a % b;
}

int main() {
    int q, r;
    divide(17, 5, &q, &r);  // q=3, r=2
    printf("商=%d, 余数=%d\\n", q, r);
    return 0;
}
```

**3. 修改数组元素**
```c
void doubleArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {
        arr[i] *= 2;  // 直接修改原数组
    }
}

int main() {
    int arr[] = {1, 2, 3};
    doubleArray(arr, 3);  // arr变为{2, 4, 6}
    return 0;
}
```

### 五、指针作为参数的注意事项

1. **指针必须有效**
   ```c
   // 错误示例
   void func(int *p) {
       *p = 100;  // p是野指针，可能崩溃
   }
   int main() {
       int *ptr;
       func(ptr);  // 未初始化的指针
       return 0;
   }
   ```

2. **使用前检查NULL**
   ```c
   void func(int *p) {
       if (p != NULL) {  // 安全检查
           *p = 100;
       }
   }
   ```""",
                    "summary": "值传递复制实参给形参，函数内修改不影响实参；地址传递传递实参地址，函数内可通过地址修改实参。地址传递用于需要修改实参或提高效率的场景",
                    "code_example": """// 值传递示例
void byValue(int x) { x = 100; }

// 地址传递示例
void byPointer(int *p) { *p = 100; }

int main() {
    int a = 10;
    byValue(a);
    printf("值传递后：a = %d\\n", a);  // a = 10，不变

    int b = 10;
    byPointer(&b);
    printf("地址传递后：b = %d\\n", b);  // b = 100，改变了

    // 交换函数
    int x = 10, y = 20;
    swap(&x, &y);  // x=20, y=10
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "值传递中a的值10被复制给x，修改x不影响a。地址传递传递&b给p，*p=100直接修改b的值",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["数组作为函数参数", "指针基础", "函数定义详解", "函数调用详解"],
                    "tips": "如果函数需要修改实参，使用指针传递；如果不需要修改实参但数据较大（如数组），也使用指针传递以提高效率",
                    "common_mistakes": "1. 值传递后忘记修改不会影响实参；2. 使用未初始化的指针；3. 忘记取地址符&"
                },
                {
                    "name": "数组作为函数参数",
                    "order_index": 2,
                    "content": """## 数组作为函数参数

### 一、数组传递给函数的特点

**关键概念**：数组名在大多数情况下退化为指针

```c
// arr实际接收的是数组首元素的地址
void printArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    printArray(arr, 5);  // arr等价于&arr[0]
    return 0;
}
```

**等价的声明方式：**
```c
void printArray(int arr[], int n);   // 可读性好
void printArray(int *arr, int n);    // 底层理解
void printArray(int arr[10], int n); // 指定大小（实际忽略）
```

### 二、数组参数传递的特点

**1. 地址传递，不是值传递**
```c
void modifyArray(int arr[], int n) {
    arr[0] = 100;  // 直接修改原数组
}

int main() {
    int arr[] = {1, 2, 3};
    modifyArray(arr, 3);
    printf("arr[0] = %d\\n", arr[0]);  // 100，数组被修改了
    return 0;
}
```

**2. 数组大小需要单独传递**
```c
// 错误做法
void printArray(int arr[]) {
    // arr不知道有多少个元素
    for (int i = 0; i < ???; i++) {  // 不知道循环多少次
    }
}

// 正确做法
void printArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {  // 通过n指定大小
        printf("%d ", arr[i]);
    }
}
```

### 三、二维数组作为函数参数

```c
// 声明方式
void printMatrix(int matrix[][3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}

// 调用
int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
printMatrix(matrix, 2);
```

**注意**：第二维的大小必须指定
```c
// 错误
void func(int matrix[][]);      // 编译错误

// 正确
void func(int matrix[][10]);     // 必须指定第二维
void func(int (*matrix)[10]);    // 等价写法
```

### 四、指针运算与数组

```c
void printArray(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        printf("%d ", *(arr + i));  // 等价于arr[i]
    }
}

int main() {
    int arr[] = {10, 20, 30, 40};
    printArray(arr, 4);  // arr是指向首元素的指针
    return 0;
}
```

### 五、综合示例：数组处理函数

```c
#include <stdio.h>

// 求最大值
int arrayMax(int arr[], int n) {
    int max = arr[0];
    for (int i = 1; i < n; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

// 数组逆序
void reverseArray(int arr[], int n) {
    for (int i = 0, j = n - 1; i < j; i++, j--) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

// 数组排序（冒泡）
void sortArray(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int arr[] = {64, 34, 25, 12, 22};
    int n = sizeof(arr) / sizeof(arr[0]);

    printf("最大值：%d\\n", arrayMax(arr, n));

    reverseArray(arr, n);
    printf("逆序：");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);

    sortArray(arr, n);
    printf("\\n排序后：");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);

    return 0;
}
```""",
                    "summary": "数组名传递给函数时退化为指针，数组参数是地址传递而非值传递。二维数组第二维大小必须指定，数组处理函数通常需要同时传递数组指针和长度",
                    "code_example": """// 数组参数是地址传递
void doubleArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {
        arr[i] *= 2;  // 修改原数组
    }
}

// 二维数组参数
void printMatrix(int matrix[][3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}

int main() {
    int arr[] = {1, 2, 3};
    doubleArray(arr, 3);  // arr变为{2, 4, 6}
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "doubleArray通过地址传递直接修改原数组。printMatrix展示二维数组参数的用法，第二维3必须指定",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["值传递与地址传递", "指针基础", "二维数组", "函数设计原则"],
                    "tips": "数组传递给函数时会退化为指针，函数内无法用sizeof(arr)/sizeof(arr[0])计算元素个数，需要单独传递n",
                    "common_mistakes": "1. 在函数内用sizeof(arr)计算数组大小；2. 二维数组第二维大小未指定；3. 忘记传递数组长度参数"
                }
            ]
        },
        {
            "title": "预处理指令",
            "description": "预处理指令的使用方法，包括宏定义、条件编译等",
            "order_index": 4,
            "knowledge_points": [
                {
                    "name": "宏定义与宏函数",
                    "order_index": 1,
                    "content": """## 宏定义与宏函数

### 一、预处理指令概述

C语言的编译过程：
```
源文件(.c) → 预处理 → 编译 → 汇编 → 链接 → 可执行文件
```

预处理指令以#开头，在编译前由预处理器处理。

### 二、宏定义（#define）

**基本语法：**
```c
#define 宏名 替换文本
```

**示例：**
```c
#define PI 3.14159
#define MAX_SIZE 100
#define ERROR_CODE 1001

int main() {
    double area = PI * r * r;
    int arr[MAX_SIZE];
    return 0;
}
```

### 三、宏的特点

1. **不带分号**：宏定义末尾不加任何标点
   ```c
   // 正确
   #define PI 3.14159

   // 错误
   #define PI 3.14159;  // 多余的分号会被替换进去
   ```

2. **完全替换**：预处理器做的是文本替换
   ```c
   #define SQUARE(x) x * x

   int main() {
       int a = SQUARE(3);      // 替换为 3 * 3 = 9
       int b = SQUARE(2 + 1); // 替换为 2 + 1 * 2 + 1 = 5（错误！）
       return 0;
   }
   ```

### 四、宏函数

**定义：**
```c
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))
#define IS_DIGIT(c) ((c) >= '0' && (c) <= '9')
```

**使用：**
```c
int main() {
    int m = MAX(10, 20);           // m = 20
    int s = SQUARE(5);             // s = 25
    char c = '5';
    if (IS_DIGIT(c)) printf("是数字\\n");
    return 0;
}
```

**为什么加括号：**
```c
// 不加括号的问题
#define SQUARE(x) x * x
int a = SQUARE(3 + 1);  // 3 + 1 * 3 + 1 = 10（错误！）

// 加括号后
#define SQUARE(x) ((x) * (x))
int a = SQUARE(3 + 1);  // ((3 + 1) * (3 + 1)) = 16（正确）
```

### 五、常用的预定义宏

| 宏 | 说明 | 示例 |
|----|------|------|
| __FILE__ | 当前源文件名 | "main.c" |
| __LINE__ | 当前行号 | 25 |
| __DATE__ | 编译日期 | "Apr 21 2026" |
| __TIME__ | 编译时间 | "14:30:00" |
| __STDC__ | 是否符合ANSI C | 1 |

```c
printf("文件：%s，行号：%d\\n", __FILE__, __LINE__);
printf("编译时间：%s %s\\n", __DATE__, __TIME__);
```

### 六、宏的优缺点

**优点：**
- 执行效率高（没有函数调用开销）
- 可用于定义常量
- 可实现条件编译

**缺点：**
- 不进行类型检查
- 可能产生副作用
- 调试困难
- 代码膨胀""",
                    "summary": "宏定义使用#define进行文本替换，宏函数要注意加括号避免优先级问题。预定义宏__FILE__、__LINE__等可用于调试",
                    "code_example": """#define PI 3.14159
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define IS_LEAP(y) (((y) % 4 == 0 && (y) % 100 != 0) || ((y) % 400 == 0))

int main() {
    printf("PI = %.5f\\n", PI);
    printf("5的平方 = %d\\n", SQUARE(5));
    printf("较大值 = %d\\n", MAX(10, 20));
    printf("2024是闰年：%d\\n", IS_LEAP(2024));
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "宏定义做文本替换，PI被替换为3.14159，SQUARE(5)被替换为((5)*(5))，MAX求两数较大值",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["条件编译", "文件包含", "函数定义详解", "const与宏比较"],
                    "tips": "宏函数的所有参数和整个表达式都要加括号，避免副作用和优先级问题。简单常量推荐用const或enum代替宏",
                    "common_mistakes": "1. 宏定义末尾加分号；2. 宏参数忘记加括号导致副作用；3. 宏与函数混淆"
                },
                {
                    "name": "条件编译",
                    "order_index": 2,
                    "content": """## 条件编译

### 一、条件编译的概念

条件编译允许根据某些条件选择性地编译代码片段。

```c
#if 条件
    代码段1
#else
    代码段2
#endif
```

### 二、#if / #else / #endif

```c
#define DEBUG 1

int main() {
    #if DEBUG == 1
        printf("调试模式\\n");
        // 调试代码
    #else
        printf("发布模式\\n");
        // 发布代码
    #endif
    return 0;
}
```

### 三、#ifdef / #ifndef

**#ifdef**：如果已定义宏，则编译代码
**#ifndef**：如果未定义宏，则编译代码

```c
#define VERSION 2

int main() {
    #ifdef DEBUG
        printf("DEBUG已定义\\n");
    #endif

    #ifndef RELEASE
        printf("RELEASE未定义\\n");
    #endif

    return 0;
}
```

### 四、防止重复包含

条件编译的经典应用 - 防止头文件重复包含：

```c
// math_utils.h
#ifndef _MATH_UTILS_H_
#define _MATH_UTILS_H_

// 函数声明
int add(int a, int b);
int subtract(int a, int b);

#endif  // _MATH_UTILS_H_

// 使用 #pragma once 也可以（现代编译器支持）
// #pragma once
```

### 五、调试与发布模式切换

```c
#define DEBUG_MODE 1  // 改为0切换到发布模式

#if DEBUG_MODE
    #define LOG(fmt, ...) printf("[DEBUG] " fmt "\\n", ##__VA_ARGS__)
#else
    #define LOG(fmt, ...) do {} while(0)
#endif

int main() {
    int x = 10;
    LOG("x = %d", x);  // 调试时输出：[DEBUG] x = 10
    return 0;
}
```

### 六、跨平台支持

```c
#ifdef _WIN32
    #include <windows.h>
    #define CLEAR "cls"
#elif __linux__
    #include <unistd.h>
    #define CLEAR "clear"
#elif __APPLE__
    #define CLEAR "clear"
#else
    #define CLEAR ""
#endif

int main() {
    system(CLEAR);  // 根据平台执行清屏命令
    return 0;
}
```

### 七、条件编译 vs 运行时if

| 特性 | 条件编译 | 运行时if |
|------|----------|----------|
| 判断时机 | 编译时 | 运行时 |
| 代码体积 | 不满足条件的代码不编译 | 所有代码都编译 |
| 执行效率 | 更高 | 有判断开销 |
| 灵活性 | 低（编译后不能改变） | 高（可动态改变） |

```c
// 条件编译
#if DEBUG == 0
    // 这段代码永远不会执行，编译时就被删除了
#endif

// 运行时判断
if (DEBUG == 0) {
    // 编译时仍然存在，有运行时开销
}
```""",
                    "summary": "条件编译根据条件选择性地编译代码，常用于调试/发布模式切换、防止头文件重复包含、跨平台支持等场景",
                    "code_example": """// 防止头文件重复包含
#ifndef _HEADER_H_
#define _HEADER_H_
// 头文件内容
#endif

// 调试模式切换
#define DEBUG 1
#if DEBUG
    #define LOG printf
#else
    #define LOG(fmt, ...) do {} while(0)
#endif

int main() {
    LOG("这是一条调试信息\\n");
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "条件编译#ifdef防止头文件重复包含，#if DEBUG根据调试模式选择是否编译日志代码",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["文件包含", "宏定义与宏函数", "预处理概述", "const与宏比较"],
                    "tips": "头文件保护使用#ifndef比#define更安全。调试代码用条件编译可以避免发布时删除调试代码",
                    "common_mistakes": "1. #if和#ifdef混淆；2. 忘记#endif；3. 头文件保护命名冲突"
                }
            ]
        },
        {
            "title": "变量作用域与存储类别",
            "description": "变量的作用域、存储类别及函数的声明周期",
            "order_index": 5,
            "knowledge_points": [
                {
                    "name": "变量作用域规则",
                    "order_index": 1,
                    "content": """## 变量作用域规则

### 一、作用域的概念

变量作用域指的是程序中能够访问该变量的区域。

### 二、不同作用域的类型

| 作用域类型 | 说明 | 示例 |
|------------|------|------|
| 块作用域 | 大括号{}内 | if、for、函数内 |
| 函数作用域 | 整个函数内 | goto标签 |
| 文件作用域 | 从声明处到文件结尾 | 函数外的全局变量 |
| 原型作用域 | 函数原型声明中 | 函数原型参数 |

### 三、块作用域

```c
int main() {
    int x = 10;          // 块开始，x可见
    if (x > 5) {
        int y = 20;      // y只在if块内可见
        printf("%d %d\\n", x, y);
    }
    // printf("%d\\n", y);  // 错误！y不在作用域内
    return 0;
}
```

### 四、函数作用域与形参

```c
// 形参的作用域是整个函数
int add(int a, int b) {  // a, b在add函数内处处可见
    int sum = a + b;
    return sum;
}
```

### 五、文件作用域（全局变量）

```c
int global_var = 100;  // 文件作用域，从这里到文件末尾

void func1() {
    printf("%d\\n", global_var);  // 可以访问
}

void func2() {
    printf("%d\\n", global_var);  // 可以访问
}
```

### 六、作用域嵌套与遮蔽

```c
int x = 10;  // 全局变量

int main() {
    int x = 20;  // 局部变量，遮蔽全局变量
    printf("%d\\n", x);    // 输出20，访问局部变量
    printf("%d\\n", ::x);  // C++可以这样访问全局变量
                            // C语言没有这种语法
    {
        int x = 30;        // 更内层的块，再次遮蔽
        printf("%d\\n", x);  // 输出30
    }
    printf("%d\\n", x);    // 输出20，回到main的x
    return 0;
}
```

### 七、如何访问被遮蔽的变量

**C语言方法**：避免遮蔽，使用不同命名
```c
int global_x = 10;

int main() {
    int local_x = 20;
    printf("global_x = %d\\n", global_x);  // 显式使用全局变量
    printf("local_x = %d\\n", local_x);
    return 0;
}
```

### 八、作用域与生命周期

| 作用域 | 生命周期 | 存储位置 |
|--------|----------|----------|
| 块作用域（局部变量） | 从定义到块结束 | 栈 |
| static局部变量 | 整个程序运行期间 | 静态存储区 |
| 全局变量 | 整个程序运行期间 | 静态存储区 |
| register变量 | 块作用域期间 | 寄存器（如果可能） |""",
                    "summary": "变量作用域分为块作用域、函数作用域、文件作用域。块内可访问全局变量，但同名会遮蔽全局变量。C语言无法直接访问被遮蔽的全局变量",
                    "code_example": """int global_var = 100;  // 全局变量

int main() {
    int local_var = 10;  // 局部变量

    printf("global_var = %d\\n", global_var);
    printf("local_var = %d\\n", local_var);

    {
        int block_var = 20;  // 块变量
        printf("block_var = %d\\n", block_var);
    }
    // printf("%d\\n", block_var);  // 错误！

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "global_var是全局变量在整个文件可见，local_var是main函数的局部变量，block_var只在嵌套块内可见",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["存储类别", "static变量", "全局变量与局部变量", "函数声明与调用"],
                    "tips": "尽量避免使用全局变量和同名遮蔽，减少Bug。建议使用有意义的变量名",
                    "common_mistakes": "1. 误以为块内定义的变量块外可用；2. 全局变量与局部变量同名混淆；3. 作用域过大导致变量冲突"
                },
                {
                    "name": "存储类别与生命周期",
                    "order_index": 2,
                    "content": """## 存储类别与生命周期

### 一、C语言的存储类别

| 存储类别 | 关键字 | 存放位置 | 生命周期 | 作用域 |
|----------|--------|----------|----------|--------|
| 自动变量 | auto（默认） | 栈 | 函数结束 | 块作用域 |
| 静态变量 | static | 静态存储区 | 程序运行期间 | 局部/全局 |
| 寄存器变量 | register | 寄存器 | 函数结束 | 块作用域 |
| 外部变量 | extern | 静态存储区 | 程序运行期间 | 文件 |

### 二、自动变量（auto）

```c
// auto是默认存储类别，可以省略
int main() {
    auto int x = 10;  // 等价于 int x = 10;
    int y = 20;       // 也是自动变量
    return 0;
}
```

### 三、静态变量（static）

**1. 静态局部变量**
```c
void count() {
    static int n = 0;  // 静态局部变量，只初始化一次
    n++;
    printf("调用次数：%d\\n", n);
}

int main() {
    count();  // 输出：调用次数：1
    count();  // 输出：调用次数：2
    count();  // 输出：调用次数：3
    return 0;
}
```

**特点**：
- 只初始化一次
- 函数结束后不销毁，值保留
- 作用域仍是局部（只能在函数内访问）

**2. 静态全局变量**
```c
static int global_var = 100;  // 静态全局变量

// 只能在本文件中访问，不能被其他文件extern
```

### 四、寄存器变量（register）

```c
int main() {
    register int i;  // 请求将i存储在寄存器中
    for (i = 0; i < 100; i++) {
        // 频繁使用的变量用register可能提高效率
    }
    return 0;
}
```

**注意**：
- 不能对寄存器变量取地址（&i非法）
- 只是请求，不保证一定放入寄存器
- 现代编译器会自动优化，很少需要手动声明

### 五、外部变量（extern）

**1. 声明外部变量**
```c
// file1.c
int shared_var = 100;  // 定义

// file2.c
extern int shared_var;  // 声明引用file1.c中的变量
printf("%d\\n", shared_var);  // 输出100
```

**2. extern关键字的作用**
```c
// 声明（告诉编译器这个变量存在）
extern int var;

// 定义（真正创建变量）
int var = 10;
```

### 六、存储类别选择指南

| 需求 | 推荐存储类别 |
|------|--------------|
| 一般局部变量 | auto（默认，无需声明） |
| 需要保留值的局部变量 | static |
| 频繁使用的循环变量 | register |
| 多个文件共享的变量 | extern |
| 限制仅本文件访问的全局变量 | static |

### 七、static的双重含义

| 语境 | 含义 |
|------|------|
| static局部变量 | 存储期：整个程序运行期间 |
| static全局变量 | 链接属性：仅本文件可见 |""",
                    "summary": "存储类别决定变量的生命周期和作用域。static局部变量保留值，static全局变量限制文件作用域，extern用于跨文件访问全局变量",
                    "code_example": """// static局部变量示例
void counter() {
    static int count = 0;  // 只初始化一次，值保留
    count++;
    printf("count = %d\\n", count);
}

int main() {
    counter();  // 1
    counter();  // 2
    counter();  // 3
    return 0;
}

// 全局变量与extern
// file1.c
int global = 100;

// file2.c
extern int global;  // 引用file1.c中的global
printf("%d\\n", global);""",
                    "code_language": "c",
                    "code_explanation": "static局部变量counter中的count只初始化一次，每次调用都保留上次的值。extern用于声明在其他文件定义的全局变量",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["变量作用域规则", "全局变量与局部变量", "函数设计原则", "多文件程序"],
                    "tips": "全局变量用static限制作用域避免命名冲突，需要在函数间共享数据时用参数传递",
                    "common_mistakes": "1. static局部变量与全局变量混淆；2. 对register变量取地址；3. 多文件时全局变量冲突"
                }
            ]
        }
    ]
}


async def save_chapter4(db):
    """保存第4章数据到数据库"""

    # 查找C语言课程
    result = await db.execute(
        select(Course).where(Course.name.like('%C语言%'))
    )
    course = result.scalar_one_or_none()
    if not course:
        print("错误：未找到C语言课程！")
        return None

    # 查找或创建第4章
    result = await db.execute(
        select(Chapter).where(
            Chapter.course_id == course.id,
            Chapter.title == CHAPTER_DATA["chapter_title"]
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        # 获取章节数
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
        # 删除旧的知识点
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

    # 创建小节
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

        # 创建知识点
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
        total = await save_chapter4(db)
        if total:
            print(f"\n第4章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
