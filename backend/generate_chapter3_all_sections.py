"""Generate Chapter 3: 循环结构及应用 - 按教学大纲生成"""
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
    "chapter_title": "循环结构及应用",
    "chapter_description": "学习C语言的循环控制语句，包括for、while、do-while循环及循环嵌套",
    "sections": [
        {
            "title": "循环控制语句概述",
            "description": "介绍循环控制语句的特点和基本概念",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "循环控制语句概述",
                    "order_index": 1,
                    "content": """## 循环控制语句概述

循环控制语句是C语言中用于重复执行一段代码的结构，是程序设计中最重要的结构之一。

### 一、为什么需要循环

在实际编程中，我们经常需要重复执行某些操作：
- 打印1到100的所有整数
- 计算1+2+3+...+100的和
- 逐个处理数组中的每个元素

如果没有循环，这些任务需要编写大量重复代码，几乎不可能完成。

### 二、C语言中的循环语句

C语言提供了三种循环语句：

| 循环语句 | 关键字 | 特点 |
|----------|--------|------|
| for循环 | for | 适合已知循环次数的场景 |
| while循环 | while | 适合循环次数未知的场景 |
| do-while循环 | do-while | 先执行后判断，至少执行一次 |

### 三、循环的基本组成

一个循环结构通常包括：
1. **初始化部分**：设置循环控制变量的初始值
2. **循环条件**：判断是否继续循环
3. **循环体**：需要重复执行的代码
4. **更新部分**：修改循环控制变量

### 四、循环的执行流程

```
开始 → 初始化 → ┌──────────────────┐
              ↓   条件判断          │
         ┌────┴────────────────────┘
         ↓ (条件为真)              ↑ (条件为假)
      执行循环体 ──────────────→ 更新变量 ─┘
              ↓ (条件仍为真)
         继续执行循环体
```

### 五、循环的分类

- **当型循环**：先判断条件，后执行循环体（for、while）
- **直到型循环**：先执行循环体，后判断条件（do-while）""",
                    "summary": "循环控制语句用于重复执行代码块，C语言提供for、while、do-while三种循环，三种循环都能实现循环结构，各有特点",
                    "code_example": """// for循环：适合已知循环次数
for (int i = 1; i <= 100; i++) {
    printf("%d ", i);
}

// while循环：适合循环次数未知
int i = 1;
while (i <= 100) {
    printf("%d ", i);
    i++;
}

// do-while循环：先执行后判断，至少执行一次
int i = 1;
do {
    printf("%d ", i);
    i++;
} while (i <= 100);""",
                    "code_language": "c",
                    "code_explanation": "三种循环都能实现1到100的打印，for循环将初始化、条件、更新集中在一起；while循环结构更清晰；do-while至少执行一次",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["for循环", "while循环", "do-while循环", "循环嵌套"],
                    "tips": "选择循环语句时：已知循环次数用for，不确定循环次数但明确继续条件用while，不确定但至少执行一次用do-while",
                    "common_mistakes": "1. 忘记在循环体中更新循环变量导致死循环；2. 循环条件写成死循环条件如 i>=0；3. for循环中多个变量初始化时用逗号分隔而非分号"
                },
                {
                    "name": "循环的跳转与辅助控制",
                    "order_index": 2,
                    "content": """## 循环的跳转与辅助控制

除了基本的循环语句，C语言还提供了两个重要的辅助控制语句：break和continue。

### 一、break语句

**作用**：终止整个循环，提前退出

break语句通常与if语句结合使用，在满足某个条件时强行退出循环。

```c
for (int i = 1; i <= 100; i++) {
    if (i == 50) {
        break;  // 当i等于50时，退出循环
    }
    printf("%d ", i);
}
// 只打印1到49
```

### 二、continue语句

**作用**：跳过本次循环的剩余部分，直接进行下一次循环条件判断

```c
for (int i = 1; i <= 10; i++) {
    if (i % 2 == 0) {
        continue;  // 跳过偶数，不打印
    }
    printf("%d ", i);  // 只打印奇数：1 3 5 7 9
}
```

### 三、break与continue的区别

| 语句 | 作用 | 效果 |
|------|------|------|
| break | 终止整个循环 | 跳出循环体，结束循环 |
| continue | 跳过本次循环 | 跳过后面代码，开始下一次循环 |

### 四、循环语句的选择

选择循环语句的原则：

1. **已知循环次数**：优先使用for循环
   ```c
   for (int i = 0; i < n; i++) { ... }
   ```

2. **循环次数未知，条件明确**：使用while循环
   ```c
   while (scanf("%d", &num) == 1) { ... }
   ```

3. **至少执行一次**：使用do-while循环
   ```c
   do {
       menu();
   } while (choice != 'q');
   ```

### 五、死循环与避免

**死循环**：循环条件永远为真，程序无法正常退出

```c
// 错误的死循环示例
for (int i = 1; i <= 10; i--) {  // i越来越小，永远不会大于10
    printf("%d ", i);
}

// 更隐蔽的死循环
while (1) {
    // 忘记写break或条件永远不会变
}
```

**正确做法**：
- 确保循环变量会朝着循环结束的方向变化
- 在适当位置使用break语句
- 使用有穷的循环条件""",
                    "summary": "break语句用于终止整个循环，continue用于跳过本次循环。循环选择应根据是否已知循环次数、是否至少执行一次来决定",
                    "code_example": """// break：找到第一个被3整除的数就退出
for (int i = 1; i <= 100; i++) {
    if (i % 3 == 0) {
        printf("第一个被3整除的数：%d", i);
        break;
    }
}

// continue：打印1-10的奇数
for (int i = 1; i <= 10; i++) {
    if (i % 2 == 0) {
        continue;  // 跳过偶数
    }
    printf("%d ", i);  // 输出：1 3 5 7 9
}""",
                    "code_language": "c",
                    "code_explanation": "break和continue都能改变循环执行流程，break直接结束循环，continue只是跳过当前迭代。调试时可先运行看是否正常结束来判断是否有死循环",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["for循环", "while循环", "do-while循环", "循环嵌套"],
                    "tips": "break和continue都会降低代码可读性，应谨慎使用。可以用重构来消除，如将条件反转来替代continue",
                    "common_mistakes": "1. 在嵌套循环中使用break只退出内层循环；2. 将break和continue混用导致逻辑混乱；3. 在do-while后写分号导致死循环"
                }
            ]
        },
        {
            "title": "for循环详解",
            "description": "for循环的表达形式、流程图绘制方法及应用实例",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "for循环基本形式",
                    "order_index": 1,
                    "content": """## for循环基本形式

for循环是C语言中最常用的循环语句，特别适合已知循环次数的场景。

### 一、for循环语法

```c
for (初始化; 条件表达式; 更新表达式) {
    循环体语句;
}
```

### 二、执行流程

```
┌─────────────────────────────────────┐
│         for (expr1; expr2; expr3)   │
│              {                       │
│   expr1 → 判断expr2 → 为真 → 执行循环体
│      ↑                    ↓
│      └──←←←←←←←←←←←← expr3 ←←←←←←┘
│               为假 → 结束循环
│              }                       │
└─────────────────────────────────────┘
```

### 三、各部分详解

**1. 初始化部分（expr1）**
- 作用：给循环变量赋初值
- 执行时机：循环开始前，只执行一次
- 可以是单个变量初始化或多个变量初始化

```c
int i = 1;           // 正确
int i = 1, j = 2;    // 正确，可以在for中初始化多个变量
```

**2. 条件表达式（expr2）**
- 作用：判断是否继续循环
- 类型：关系或逻辑表达式，结果为真(非0)或假(0)
- 执行时机：每次循环前
- 可以省略（相当于始终为真）

**3. 更新表达式（expr3）**
- 作用：更新循环变量的值
- 执行时机：每次循环体执行后
- 可以是递增、递减或其他操作

### 四、常见形式

```c
// 形式1：标准计数循环
for (int i = 0; i < n; i++) {
    // i从0到n-1，执行n次
}

// 形式2：倒序循环
for (int i = n - 1; i >= 0; i--) {
    // i从n-1到0
}

// 形式3：步长不为1
for (int i = 0; i < n; i += 2) {
    // i: 0, 2, 4, 6, ...
}

// 形式4：多个循环变量
for (int i = 0, j = n-1; i < j; i++, j--) {
    // i从0开始，j从n-1开始，逐渐靠拢
}
```

### 五、注意事项

1. for语句三个表达式都可以省略，但分号必须保留
2. 省略条件表达式表示条件始终为真，需要在循环体内用break退出
3. for循环变量i的作用域仅在循环内部""",
                    "summary": "for循环是C语言最常用的循环语句，语法为for(初始化;条件;更新){循环体}，适合已知循环次数的场景，循环变量作用域仅在循环内",
                    "code_example": """// 计算1到100的和
int sum = 0;
for (int i = 1; i <= 100; i++) {
    sum += i;
}
printf("1+2+...+100 = %d\\n", sum);

// 打印九九乘法表
for (int i = 1; i <= 9; i++) {
    for (int j = 1; j <= i; j++) {
        printf("%d*%d=%d\\t", j, i, i*j);
    }
    printf("\\n");
}""",
                    "code_language": "c",
                    "code_explanation": "第一个例子展示基本计数循环，初始化i=1，判断i<=100，每次循环后i++。第二个展示嵌套循环打印九九乘法表，内层循环控制列数",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["for循环深入", "while循环", "do-while循环", "循环嵌套"],
                    "tips": "循环变量i的作用域在循环体内，循环结束后不能使用i。如果需要在循环外使用，应在for之前声明",
                    "common_mistakes": "1. 在for(;;)中省略分号导致语法错误；2. 循环变量类型不一致导致精度问题；3. 忘记更新表达式导致死循环"
                },
                {
                    "name": "for循环深入应用",
                    "order_index": 2,
                    "content": """## for循环深入应用

### 一、for循环的特殊形式

**1. 省略表达式**
```c
// 省略初始化（循环变量在for前定义）
int i = 1;
for (; i <= 100; i++) {
    sum += i;
}

// 省略条件（条件始终为真，需在循环内用break退出）
for (int i = 1; ; i++) {
    if (i > 100) break;
    sum += i;
}

// 省略更新（更新在循环体内）
for (int i = 1; i <= 100;) {
    sum += i;
    i++;
}

// 全部省略（死循环）
for (;;) {
    // 相当于 while(1)
}
```

**2. 循环变量声明（C99标准）**
```c
// 传统方式：在for之前声明
int i;
for (i = 0; i < 10; i++) { }

// C99方式：在for内声明（推荐）
for (int i = 0; i < 10; i++) { }
// i的作用域仅在for循环内
```

### 二、for循环的典型应用

**1. 累加求和**
```c
// 计算1! + 2! + 3! + ... + n!
int n = 5;
int sum = 0;
for (int i = 1; i <= n; i++) {
    int factorial = 1;
    for (int j = 1; j <= i; j++) {
        factorial *= j;
    }
    sum += factorial;
}
```

**2. 计数循环**
```c
// 统计正整数n的位数
int n = 12345;
int count = 0;
for (; n > 0; count++) {
    n /= 10;
}
// count = 5
```

**3. 穷举法**
```c
// 找出100以内所有素数
for (int i = 2; i <= 100; i++) {
    int is_prime = 1;
    for (int j = 2; j < i; j++) {
        if (i % j == 0) {
            is_prime = 0;
            break;
        }
    }
    if (is_prime) {
        printf("%d ", i);
    }
}
```

### 三、for循环的效率问题

**1. 避免重复计算**
```c
int arr[10];
int n = 10;

// 低效：每次循环都计算n-1
for (int i = 0; i < n - 1; i++) {
    // ...
}

// 高效：将不变表达式提到循环外
int limit = n - 1;
for (int i = 0; i < limit; i++) {
    // ...
}
```

**2. 循环不变式外提**
```c
// 低效
for (int i = 0; i < strlen(s); i++) {
    // strlen(s)在每次循环都被调用
}

// 高效
int len = strlen(s);
for (int i = 0; i < len; i++) {
    // ...
}
```

### 四、for循环与数组

```c
int arr[] = {5, 3, 8, 1, 9};
int n = sizeof(arr) / sizeof(arr[0]);

// 遍历数组
for (int i = 0; i < n; i++) {
    printf("%d ", arr[i]);
}

// 查找最大值
int max = arr[0];
for (int i = 1; i < n; i++) {
    if (arr[i] > max) {
        max = arr[i];
    }
}

// 数组逆序
for (int i = 0, j = n - 1; i < j; i++, j--) {
    int temp = arr[i];
    arr[i] = arr[j];
    arr[j] = temp;
}
```""",
                    "summary": "for循环的特殊形式包括省略表达式、C99变量声明。典型应用有累加求和、计数循环、穷举法。应注意避免循环内重复计算提高效率",
                    "code_example": """// 找出100以内所有素数
for (int i = 2; i <= 100; i++) {
    int is_prime = 1;
    for (int j = 2; j < i; j++) {
        if (i % j == 0) {
            is_prime = 0;
            break;
        }
    }
    if (is_prime) {
        printf("%d ", i);
    }
}

// 计算数组平均值
int arr[] = {5, 3, 8, 1, 9};
int n = sizeof(arr) / sizeof(arr[0]);
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += arr[i];
}
printf("平均值：%.2f\\n", (double)sum / n);""",
                    "code_language": "c",
                    "code_explanation": "素数判断使用穷举法，对每个数i用2到i-1的数去除，如果能整除则不是素数。平均值计算先累加所有元素，再除以个数",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["for循环基本形式", "while循环", "循环嵌套", "break与continue"],
                    "tips": "循环变量在for内声明是C99标准，现代编译器都支持。strlen等函数调用应提到循环外避免重复计算",
                    "common_mistakes": "1. 忽略循环变量的作用域差异；2. 在循环内修改循环变量；3. 循环条件使用strlen(s)导致O(n²)复杂度"
                }
            ]
        },
        {
            "title": "while循环详解",
            "description": "while循环的表达形式、流程图绘制方法及应用实例",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "while循环基本形式",
                    "order_index": 1,
                    "content": """## while循环基本形式

while循环是C语言中最基本的循环结构，属于"当型循环"。

### 一、while循环语法

```c
while (条件表达式) {
    循环体语句;
}
```

### 二、执行流程

```
┌─────────────────────────┐
│                         │
│    ┌────────────────────┴─┐
│    ↓                      │
│  条件判断                  │
│    │                       │
│    ├──真(非0)→ 执行循环体 ─┘
│    │           ↑
│    │           │
│    └──假(0)→ 退出循环
│                         │
└─────────────────────────┘
```

### 三、与for循环的比较

| 特性 | for循环 | while循环 |
|------|---------|-----------|
| 适用场景 | 已知循环次数 | 循环次数未知 |
| 结构 | 初始化、条件、更新集中 | 三部分分散 |
| 强调重点 | 计数 | 条件判断 |

### 四、常见形式

**1. 计数型while**
```c
int i = 1;        // 初始化在循环前
while (i <= 100) { // 条件判断
    printf("%d ", i);
    i++;          // 更新在循环体末尾
}
```

**2. 标志型while**
```c
int choice;
while (1) {        // 死循环，用break退出
    printf("1. 开始游戏\\n");
    printf("2. 退出\\n");
    scanf("%d", &choice);
    if (choice == 2) break;
}
```

**3. 输入型while**
```c
int num, sum = 0;
printf("输入整数（0结束）：");
while (scanf("%d", &num) == 1 && num != 0) {
    sum += num;
}
printf("总和：%d\\n", sum);
```

### 五、while循环的注意事项

1. **先判断后执行**：如果第一次条件就为假，循环体一次都不执行
2. **循环条件变化**：必须确保循环条件朝着假的方向发展
3. **避免死循环**：检查循环变量的更新是否正确

### 六、while循环的典型应用

```c
// 计算最大公约数（辗转相除法）
int a = 48, b = 18;
while (b != 0) {
    int temp = a % b;
    a = b;
    b = temp;
}
printf("最大公约数：%d\\n", a);

// 计算阶乘
int n = 5;
int factorial = 1;
int i = 1;
while (i <= n) {
    factorial *= i;
    i++;
}
printf("%d! = %d\\n", n, factorial);""",
                    "summary": "while循环先判断条件后执行循环体，适合循环次数未知的场景。应确保循环条件朝着假的方向发展，避免死循环",
                    "code_example": """// 计算最大公约数（辗转相除法）
int a = 48, b = 18;
while (b != 0) {
    int temp = a % b;
    a = b;
    b = temp;
}
printf("最大公约数：%d\\n", a);

// 猜数字游戏
int secret = 7, guess;
while (1) {
    printf("猜一个数字(1-10)：");
    scanf("%d", &guess);
    if (guess == secret) {
        printf("恭喜猜对！\\n");
        break;
    } else if (guess > secret) {
        printf("太大了！\\n");
    } else {
        printf("太小了！\\n");
    }
}""",
                    "code_language": "c",
                    "code_explanation": "辗转相除法通过不断取余使b逐渐变为0，当b为0时a就是最大公约数。猜数字游戏用while(1)加break实现不确定次数的循环",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["while循环深入", "for循环", "do-while循环", "break与continue"],
                    "tips": "while循环更符合'当...时'的自然语义，当循环次数不确定时优先选择while",
                    "common_mistakes": "1. 忘记在循环体中更新循环条件相关变量；2. 循环条件写错导致多执行或少执行一次；3. 与for循环混淆，忘记初始化"
                },
                {
                    "name": "while循环深入应用",
                    "order_index": 2,
                    "content": """## while循环深入应用

### 一、while循环的常见模式

**1. 读取直到有效输入**
```c
int age;
printf("请输入年龄(1-150)：");
while (scanf("%d", &age) != 1 || age < 1 || age > 150) {
    while (getchar() != '\\n');  // 清除输入缓冲区
    printf("输入无效，请重新输入：");
}
printf("您的年龄是：%d\\n", age);
```

**2. 字符串处理**
```c
char str[] = "Hello";
int i = 0;
while (str[i] != '\\0') {
    putchar(str[i]);
    i++;
}

// 统计字符串长度
int len = 0;
while (str[len] != '\\0') {
    len++;
}
```

**3. 链表遍历（C语言重要用法）**
```c
struct Node {
    int data;
    struct Node* next;
};

struct Node* head;  // 假设已有链表
struct Node* p = head;
while (p != NULL) {
    printf("%d ", p->data);
    p = p->next;
}
```

### 二、while循环的嵌套

```c
// 打印直角三角形
/*
*
**
***
****
*****
*/
int n = 5;
int i = 1;
while (i <= n) {
    int j = 1;
    while (j <= i) {
        printf("*");
        j++;
    }
    printf("\\n");
    i++;
}
```

### 三、while循环与递归对比

**问题：计算斐波那契数列前n项**

while循环版本：
```c
int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    int i = 2;
    while (i <= n) {
        int temp = a + b;
        a = b;
        b = temp;
        i++;
    }
    return b;
}
```

### 四、while循环的注意事项

1. **输入缓冲区问题**
```c
// 常见错误
char ch;
while (ch != 'q') {
    scanf("%c", &ch);  // 会读取换行符'\\n'
}

// 正确做法：跳过换行符
char ch;
while (scanf(" %c", &ch) == 1 && ch != 'q') {
    // %c前有空格，跳过空白字符
}
```

2. **空循环体问题**
```c
// 正确：doNothing是空语句
while (condition)
    ;  // 空语句，什么都不做

// 错误：容易误认为是while循环体
while (condition);  // 这是一个死循环！
```

### 五、性能与可读性

**1. 循环不变式外提**
```c
// 低效
while (i < strlen(str)) {  // 每次都调用strlen
    // ...
}

// 高效
int len = strlen(str);
while (i < len) {
    // ...
}
```

**2. 循环展开（空间换时间）**
```c
// 普通版本
while (i < n) {
    sum += arr[i];
    i++;
}

// 循环展开（每4次处理）
while (i + 3 < n) {
    sum += arr[i] + arr[i+1] + arr[i+2] + arr[i+3];
    i += 4;
}
// 处理剩余元素
while (i < n) {
    sum += arr[i];
    i++;
}
```""",
                    "summary": "while循环的典型应用包括读取有效输入、字符串处理、链表遍历。注意输入缓冲区和空循环体问题，可通过循环不变式外提和循环展开优化性能",
                    "code_example": """// 统计字符串中各字符出现次数
char str[] = "hello world";
int count[256] = {0};  // ASCII码计数器
int i = 0;
while (str[i] != '\\0') {
    count[(int)str[i]]++;
    i++;
}
for (int i = 0; i < 256; i++) {
    if (count[i] > 0) {
        printf("'%c': %d次\\n", i, count[i]);
    }
}""",
                    "code_language": "c",
                    "code_explanation": "用数组作为计数器遍历字符串，ASCII码作为索引统计每个字符出现次数。while循环遇到字符串结束符\\0时停止",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["while循环基本形式", "for循环", "do-while循环", "循环嵌套"],
                    "tips": "scanf的%c会读取所有字符包括空格和换行，加空格可以跳过空白字符。链表遍历是while循环的经典应用",
                    "common_mistakes": "1. 忽略输入缓冲区导致程序卡住；2. while(condition);形成空循环体导致死循环；3. 字符串未加\\0结束符"
                }
            ]
        },
        {
            "title": "do-while循环详解",
            "description": "do-while循环的表达形式、流程图绘制方法及应用实例",
            "order_index": 4,
            "knowledge_points": [
                {
                    "name": "do-while循环基本形式",
                    "order_index": 1,
                    "content": """## do-while循环基本形式

do-while循环是C语言三种循环语句中的"直到型循环"，特点是**先执行后判断**。

### 一、do-while循环语法

```c
do {
    循环体语句;
} while (条件表达式);
// 注意：while后面有分号！
```

### 二、执行流程

```
┌──────────────────────────────────┐
│                                  │
│    执行循环体 ──────────────────┐ │
│    ↓                            │ │
│    判断条件                      │ │
│    ↓                            │ │
│    ├──真(非0)──→ 继续执行循环体 ←┘ │
│    │                              │
│    └──假(0)──→ 退出循环 ───────┘ │
│                                  │
└──────────────────────────────────┘
```

### 三、与while循环的区别

| 特性 | while循环 | do-while循环 |
|------|-----------|--------------|
| 判断时机 | 先判断后执行 | 先执行后判断 |
| 循环体执行次数 | 0次或多次 | 至少1次 |
| 语法 | 无分号 | while后有分号 |

### 四、代码对比

```c
int i = 10;

// while循环：条件初始为假，循环体不执行
while (i < 10) {
    printf("while: i = %d\\n", i);  // 不执行
    i++;
}

// do-while循环：条件初始为假，循环体仍执行一次
do {
    printf("do-while: i = %d\\n", i);  // 执行一次
    i++;
} while (i < 10);  // 输出：do-while: i = 10
```

### 五、do-while的典型应用

**1. 菜单驱动程序**
```c
int choice;
do {
    printf("\\n===== 菜单 =====\\n");
    printf("1. 开始游戏\\n");
    printf("2. 继续游戏\\n");
    printf("3. 退出\\n");
    printf("请选择：");
    scanf("%d", &choice);

    switch (choice) {
        case 1: printf("开始新游戏...\\n"); break;
        case 2: printf("继续游戏...\\n"); break;
        case 3: printf("退出游戏...\\n"); break;
        default: printf("无效选择！\\n");
    }
} while (choice != 3);
```

**2. 猜数字游戏**
```c
int secret = 7;
int guess;
do {
    printf("猜一个数字(1-10)：");
    scanf("%d", &guess);
    if (guess > secret) {
        printf("太大了！\\n");
    } else if (guess < secret) {
        printf("太小了！\\n");
    }
} while (guess != secret);
printf("恭喜猜对了！\\n");
```

**3. 输入验证**
```c
int num;
do {
    printf("请输入1-100之间的数：");
    scanf("%d", &num);
    if (num < 1 || num > 100) {
        printf("输入错误，请重新输入！\\n");
    }
} while (num < 1 || num > 100);
printf("您输入的是：%d\\n", num);
```

### 六、注意事项

1. **不要忘记分号**：while后的分号是语法的一部分，不能省略
2. **至少执行一次**：如果需要在条件不满足时也执行一次循环体，选择do-while
3. **循环条件更新**：确保循环条件最终会变为假，避免死循环""",
                    "summary": "do-while循环先执行后判断，保证循环体至少执行一次。适合菜单程序、输入验证等至少需要执行一次的场景。while后必须有分号",
                    "code_example": """// 菜单驱动程序
int choice;
do {
    printf("\\n===== 菜单 =====\\n");
    printf("1. 开始游戏\\n");
    printf("2. 继续游戏\\n");
    printf("3. 退出\\n");
    printf("请选择：");
    scanf("%d", &choice);

    switch (choice) {
        case 1: printf("开始新游戏...\\n"); break;
        case 2: printf("继续游戏...\\n"); break;
        case 3: printf("退出游戏...\\n"); break;
        default: printf("无效选择！\\n");
    }
} while (choice != 3);

// 输入验证
int num;
do {
    printf("请输入1-100之间的数：");
    scanf("%d", &num);
    if (num < 1 || num > 100) {
        printf("输入错误！\\n");
    }
} while (num < 1 || num > 100);""",
                    "code_language": "c",
                    "code_explanation": "菜单程序用do-while保证菜单至少显示一次，用户选择退出(3)时才结束。输入验证保证用户输入有效值前不断循环",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["do-while深入", "while循环", "for循环", "break与continue"],
                    "tips": "菜单程序和输入验证是do-while的经典应用，确保用户至少看到一次菜单或至少输入一次数据",
                    "common_mistakes": "1. 忘记while后的分号导致语法错误；2. 误用while代替do-while导致少执行一次；3. 在循环内忘记更新条件导致死循环"
                },
                {
                    "name": "do-while循环深入应用",
                    "order_index": 2,
                    "content": """## do-while循环深入应用

### 一、do-while与循环变量的作用域

do-while的特殊性在于：循环体在条件判断之前执行

```c
// 常见错误：循环变量作用域问题
int i = 0;
do {
    printf("%d ", i);
    i++;
} while (i < 10);
printf("\\n%d\\n", i);  // i = 10，可以访问

// 对比for循环
for (int j = 0; j < 10; j++) {
    printf("%d ", j);
}
printf("%d\\n", j);  // 错误！j的作用域仅在for内
```

### 二、do-while的嵌套

```c
// 打印九九乘法表（改进版）
int i = 1;
do {
    int j = 1;
    do {
        printf("%d*%d=%2d\\t", j, i, i*j);
        j++;
    } while (j <= i);
    printf("\\n");
    i++;
} while (i <= 9);
```

### 三、用do-while实现循环结构

**1. 实现任意循环次数**
```c
// 用do-while模拟for循环
int i = 0;  // 初始化
do {
    printf("%d ", i);
    i++;     // 更新
} while (i < 10);  // 条件
```

**2. 实现直到型循环模式**
```c
// 重复输入直到正确
int correct = 0;
int answer;
do {
    printf("5 + 3 = ? ");
    scanf("%d", &answer);
    if (answer == 8) {
        printf("正确！\\n");
        correct = 1;
    } else {
        printf("错误，请重试！\\n");
    }
} while (!correct);
```

### 四、do-while与算法的结合

**1. 数值计算**
```c
// 计算平方根（牛顿迭代法）
double a = 2.0;  // 要计算平方根的数
double x = a / 2;  // 初始近似值
double epsilon = 1e-10;  // 精度要求

do {
    x = (x + a / x) / 2;  // 迭代公式
} while (fabs(x * x - a) > epsilon);

printf("sqrt(%g) = %.10f\\n", a, x);
```

**2. 累加器模式**
```c
// 菜单选择累加
double sum = 0;
int choice;
do {
    printf("1. 加数  2. 减数  3. 查看结果  4. 退出：");
    scanf("%d", &choice);
    if (choice == 1) {
        double x; scanf("%lf", &x); sum += x;
    } else if (choice == 2) {
        double x; scanf("%lf", &x); sum -= x;
    } else if (choice == 3) {
        printf("当前结果：%.2f\\n", sum);
    }
} while (choice != 4);
```

### 五、do-while的优缺点

**优点**：
1. 保证循环体至少执行一次
2. 适合需要先执行后判断的场景
3. 结构比while循环更紧凑

**缺点**：
1. 可读性不如while循环（条件在最后）
2. 容易忘记while后的分号
3. 不如for循环适合计数型循环

### 六、循环语句选择建议

```
已知循环次数？──是──→ for循环
    │
    └─否─至少执行一次？──是──→ do-while循环
              │
              └─否─→ while循环
```""",
                    "summary": "do-while循环体在条件判断前执行，保证至少执行一次。适合先执行后判断的场景。适合菜单程序、输入验证、迭代计算等",
                    "code_example": """// 计算平方根（牛顿迭代法）
double a = 2.0;
double x = a / 2;
double epsilon = 1e-10;

do {
    x = (x + a / x) / 2;
} while (fabs(x * x - a) > epsilon);

printf("sqrt(%g) = %.10f\\n", a, x);

// 菜单累加器
double sum = 0;
int choice;
do {
    printf("1.加 2.减 3.查看 4.退出：");
    scanf("%d", &choice);
    if (choice == 1) { double x; scanf("%lf", &x); sum += x; }
    else if (choice == 2) { double x; scanf("%lf", &x); sum -= x; }
    else if (choice == 3) { printf("结果：%.2f\\n", sum); }
} while (choice != 4);""",
                    "code_language": "c",
                    "code_explanation": "牛顿迭代法通过do-while保证至少计算一次，用fabs判断收敛精度。菜单累加器用do-while保证菜单至少显示一次让用户选择",
                    "difficulty": 2,
                    "importance": 3,
                    "related_points": ["do-while循环基本形式", "while循环", "for循环", "break与continue"],
                    "tips": "迭代计算常用do-while因为通常需要至少一次迭代。选择循环语句应遵循：先判断用while，先执行用do-while",
                    "common_mistakes": "1. 忘记while后分号；2. 在循环内忘记更新导致死循环；3. 误用do-while导致多执行一次"
                }
            ]
        },
        {
            "title": "循环嵌套与综合应用",
            "description": "循环嵌套、循环控制及循环语句的选择，以及综合应用实例",
            "order_index": 5,
            "knowledge_points": [
                {
                    "name": "循环嵌套基础",
                    "order_index": 1,
                    "content": """## 循环嵌套基础

循环嵌套是指在一个循环的循环体内包含另一个循环，形成多层循环结构。

### 一、嵌套循环语法

```c
// 基本语法
for (外层条件) {      // 外层循环
    for (内层条件) {  // 内层循环
        循环体;
    }
}

// 三种循环可以互相嵌套
while (外层条件) {
    for (内层条件) {
        // 循环体
    }
}
```

### 二、执行流程

```
外层循环第1次 ─┬─ 内层循环全部执行完
              │
              ├─ 内层循环第1次
              ├─ 内层循环第2次
              │  ...
              └─ 内层循环结束

外层循环第2次 ─┬─ 内层循环全部执行完
              │
              └─ ... (重复直到外层循环结束)
```

### 三、常见嵌套模式

**1. 矩形打印**
```c
// 打印5行10列的*
for (int i = 0; i < 5; i++) {      // 控制行数
    for (int j = 0; j < 10; j++) { // 控制列数
        printf("*");
    }
    printf("\\n");
}
```

**2. 三角形打印**
```c
/*
*
**
***
****
*****
*/
// 左对齐直角三角形
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= i; j++) {
        printf("*");
    }
    printf("\\n");
}

// 右对齐直角三角形
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 5; j++) {
        if (j <= 5 - i)
            printf(" ");
        else
            printf("*");
    }
    printf("\\n");
}
```

**3. 九九乘法表**
```c
for (int i = 1; i <= 9; i++) {
    for (int j = 1; j <= i; j++) {
        printf("%d*%d=%2d\\t", j, i, i*j);
    }
    printf("\\n");
}
```

### 四、嵌套循环的计数

**关键规则**：总循环次数 = 外层循环次数 × 内层循环次数

```c
// 外层5次，内层每次变化
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= i; j++) { // 1+2+3+4+5=15次
        // 循环体
    }
}
// 总执行次数 = 1+2+3+4+5 = 15次
```

### 五、嵌套深度与性能

**嵌套层数建议**：一般不超过3层

```c
// 3层嵌套示例（打印3D图案）
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        for (int k = 0; k < 3; k++) {
            printf("(%d,%d,%d)\\n", i, j, k);
        }
    }
}
// 总执行次数 = 3 × 3 × 3 = 27次
```""",
                    "summary": "循环嵌套是一个循环的循环体内包含另一个循环。外层控制行/层，内层控制列/内部次数。总执行次数为各层循环次数的乘积",
                    "code_example": """// 打印九九乘法表
for (int i = 1; i <= 9; i++) {
    for (int j = 1; j <= i; j++) {
        printf("%d*%d=%2d\\t", j, i, i*j);
    }
    printf("\\n");
}

// 打印菱形
int n = 4;  // 上半部分行数
// 上半部分（含中间行）
for (int i = 1; i <= n; i++) {
    for (int j = 1; j <= n - i; j++) printf(" ");
    for (int j = 1; j <= 2*i - 1; j++) printf("*");
    printf("\\n");
}
// 下半部分
for (int i = n - 1; i >= 1; i--) {
    for (int j = 1; j <= n - i; j++) printf(" ");
    for (int j = 1; j <= 2*i - 1; j++) printf("*");
    printf("\\n");
}""",
                    "code_language": "c",
                    "code_explanation": "九九乘法表内层循环次数等于当前行号i，实现左下角三角形。菱形用两个三角形拼接，上半部分行数n，下半部分n-1行",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["for循环", "while循环", "do-while循环", "break与continue"],
                    "tips": "分析嵌套循环时，用'外层循环执行一次，内层循环执行全部'的原则理解。嵌套循环越少越好，超过3层应考虑算法优化",
                    "common_mistakes": "1. 内层循环变量与外层混淆导致逻辑错误；2. 忘记在内层循环结束时换行；3. 嵌套层数过多导致O(n³)复杂度"
                },
                {
                    "name": "循环嵌套深入与综合应用",
                    "order_index": 2,
                    "content": """## 循环嵌套深入与综合应用

### 一、复杂图案打印

**1. 空心矩形**
```c
// 5行10列空心矩形
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 10; j++) {
        if (i == 1 || i == 5 || j == 1 || j == 10)
            printf("*");
        else
            printf(" ");
    }
    printf("\\n");
}
```

**2. 数字三角形**
```c
/*
1
12
123
1234
12345
*/
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= i; j++) {
        printf("%d", j);
    }
    printf("\\n");
}

/*
    1
   12
  123
 1234
12345
*/
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 5; j++) {
        if (j <= 5 - i)
            printf(" ");
        else
            printf("%d", j - (5 - i));
    }
    printf("\\n");
}
```

### 二、算法中的嵌套循环

**1. 冒泡排序**
```c
int arr[] = {64, 34, 25, 12, 22, 11, 90};
int n = sizeof(arr) / sizeof(arr[0]);

for (int i = 0; i < n - 1; i++) {           // 比较轮数
    for (int j = 0; j < n - 1 - i; j++) {   // 每轮比较次数
        if (arr[j] > arr[j + 1]) {
            int temp = arr[j];
            arr[j] = arr[j + 1];
            arr[j + 1] = temp;
        }
    }
}
```

**2. 质数判断（优化）**
```c
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    // 只需检查到sqrt(n)
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}

// 打印100以内所有质数
for (int i = 2; i <= 100; i++) {
    if (isPrime(i)) {
        printf("%d ", i);
    }
}
```

### 三、综合实例：学生成绩统计

```c
// 统计多个班级的成绩
int classCount, studentCount;
printf("输入班级数和学生数：");
scanf("%d %d", &classCount, &studentCount);

for (int c = 1; c <= classCount; c++) {
    int sum = 0;
    printf("\\n班级%d成绩：\\n", c);
    for (int s = 1; s <= studentCount; s++) {
        int score;
        printf("  学生%d成绩：", s);
        scanf("%d", &score);
        sum += score;
    }
    printf("  班级%d平均分：%.2f\\n", c, (double)sum / studentCount);
}
```

### 四、循环语句的选择策略

| 场景 | 推荐循环 | 原因 |
|------|----------|------|
| 已知循环次数 | for | 初始化、判断、更新集中 |
| 次数未知，先判断 | while | 先判断后执行，符合逻辑 |
| 至少执行一次 | do-while | 先执行后判断 |
| 多层嵌套 | 外层for，内层灵活 | 结构清晰，便于分析 |

### 五、性能优化

**1. 减少循环次数**
```c
// 原始冒泡排序
for (int i = 0; i < n - 1; i++) {
    for (int j = 0; j < n - 1; j++) {
        // 比较所有对
    }
}

// 优化：添加交换标志，提前结束
for (int i = 0; i < n - 1; i++) {
    int swapped = 0;
    for (int j = 0; j < n - 1 - i; j++) {
        if (arr[j] > arr[j + 1]) {
            swap(arr[j], arr[j + 1]);
            swapped = 1;
        }
    }
    if (!swapped) break;  // 已排好序，提前结束
}
```

**2. 避免重复计算**
```c
// 低效
for (int i = 0; i < n; i++) {
    for (int j = 0; j < m; j++) {
        if (i == 0) process(arr[0][j]);  // 在内层循环中判断
    }
}

// 高效
for (int j = 0; j < m; j++) {
    process(arr[0][j]);  // 提到外层
}
for (int i = 1; i < n; i++) {
    for (int j = 0; j < m; j++) {
        // 处理其他元素
    }
}
```""",
                    "summary": "嵌套循环用于复杂图案打印和算法实现。综合应用包括冒泡排序、质数判断、成绩统计。循环选择应根据已知条件和使用场景决定",
                    "code_example": """// 冒泡排序
int arr[] = {64, 34, 25, 12, 22, 11, 90};
int n = sizeof(arr) / sizeof(arr[0]);

for (int i = 0; i < n - 1; i++) {
    for (int j = 0; j < n - 1 - i; j++) {
        if (arr[j] > arr[j + 1]) {
            int temp = arr[j];
            arr[j] = arr[j + 1];
            arr[j + 1] = temp;
        }
    }
}

// 判断质数（优化到sqrt）
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}""",
                    "code_language": "c",
                    "code_explanation": "冒泡排序外层控制轮数i=0到n-2，内层j=0到n-2-i，每轮把最大元素'冒泡'到最后。质数判断只需检查到sqrt(n)可减少约一半计算量",
                    "difficulty": 3,
                    "importance": 5,
                    "related_points": ["循环嵌套基础", "for循环", "while循环", "break与continue"],
                    "tips": "嵌套循环分析时，从内向外理解：内层循环负责具体操作，外层控制操作重复次数。优化时先考虑减少不必要的循环",
                    "common_mistakes": "1. 内层循环条件写错导致多比较或少比较；2. 排序时内外层变量使用混淆；3. 忽略提前结束优化的机会"
                }
            ]
        }
    ]
}


async def save_chapter3(db):
    """保存第3章数据到数据库"""

    # 查找C语言课程
    result = await db.execute(
        select(Course).where(Course.name.like('%C语言%'))
    )
    course = result.scalar_one_or_none()
    if not course:
        print("错误：未找到C语言课程！")
        return None

    # 查找或创建第3章
    result = await db.execute(
        select(Chapter).where(
            Chapter.course_id == course.id,
            Chapter.title.like('%循环%')
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
        total = await save_chapter3(db)
        if total:
            print(f"\n第3章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
