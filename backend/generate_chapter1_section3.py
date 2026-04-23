"""Generate Chapter 1 Section 3: 程序设计基础 - 按教学大纲生成"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint
from sqlalchemy import select, text, join


# 第一章第3节：教学大纲内容
# 1.3 讲述基本功能设计、程序设计描述的方法、程序实现及常见错误分析及编程风格

SECTION_DATA = {
    "section_title": "程序设计基础",
    "section_description": "基本功能设计、程序设计描述的方法、程序实现及常见错误分析及编程风格",
    "order_index": 3,
    "estimated_minutes": 25,
    "knowledge_points": [
        {
            "name": "算法的基本概念",
            "order_index": 1,
            "content": """## 算法的基本概念

### 一、算法的定义

**算法**：解决特定问题的步骤和方法，是程序设计的核心。

**著名例子：欧几里得算法（求最大公约数）**
```
1. 用较大数除以较小数
2. 得到余数
3. 用较小数除以余数
4. 重复步骤2-3，直到余数为0
5. 最后的除数就是最大公约数
```

### 二、算法的特性

**1. 有穷性**
- 算法必须在有限步骤内结束
- 不能无限循环

**2. 确定性**
- 每一步都有明确的含义
- 不会产生歧义

**3. 可行性**
- 每一步都能通过执行完成
- 不能执行的步骤无效

**4. 输入**
- 算法有零个或多个输入
- 输入是算法开始前的已知数据

**5. 输出**
- 算法至少有一个输出
- 输出是算法执行的结果

### 三、算法的评价标准

**正确性**
- 算法必须能够正确解决问题
- 对所有合法输入都能给出正确结果

**高效性**
- 时间复杂度越低越好
- 占用时间越短越好

**空间效率**
- 占用内存越少越好

**可读性**
- 算法逻辑清晰易理解
- 便于维护和修改

### 四、算法描述方法

1. **自然语言** - 用日常语言描述
2. **流程图** - 用图形符号描述
3. **伪代码** - 介于自然语言和代码之间
4. **程序代码** - 用编程语言实现

### 五、简单算法示例

**求1+2+3+...+100的和**
```
算法1（累加法）：
1. sum = 0
2. i = 1
3. 如果 i <= 100，转第4步，否则转第7步
4. sum = sum + i
5. i = i + 1
6. 转回第3步
7. 输出sum
```

**判断闰年**
```
输入年份year
如果 year能被4整除 且 year不能被100整除
    是闰年
否则如果 year能被400整除
    是闰年
否则
    不是闰年
```

### 六、注意事项

1. 算法要有明确的输入和输出
2. 每一步都要具体可执行
3. 算法必须在有限步骤内结束
4. 选择效率高的算法""",
            "summary": "算法是解决问题的步骤和方法，具有有穷性、确定性、可行性等特性，是程序设计的核心",
            "code_example": """#include <stdio.h>

// 求1+2+...+100的和
int main(void) {
    int sum = 0;
    int i = 1;

    while (i <= 100) {
        sum = sum + i;
        i = i + 1;
    }

    printf("1+2+...+100 = %d\\n", sum);
    return 0;
}

// 判断闰年
int isLeapYear(int year) {
    if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)) {
        return 1;
    }
    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了累加法求和算法和判断闰年算法",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["流程图", "伪代码", "程序调试"],
            "tips": ["先设计算法再写代码", "算法要清晰明了", "注意边界条件"],
            "common_mistakes": ["算法步骤不完整", "忽略边界条件", "算法效率低下"]
        },
        {
            "name": "流程图",
            "order_index": 2,
            "content": """## 流程图

### 一、流程图简介

流程图是用图形符号描述算法执行过程的工具。

### 二、基本符号

| 符号 | 名称 | 用途 |
|------|------|------|
| 椭圆 | 开始/结束 | 表示程序开始或结束 |
| 平行四边形 | 输入/输出 | 表示输入或输出操作 |
| 矩形 | 处理 | 表示处理或运算 |
| 菱形 | 判断 | 表示条件判断 |
| 箭头 | 流程线 | 表示执行方向 |
| 连接线 | 连接 | 连接流程图的各个部分 |

### 三、顺序结构流程图

```
    ┌─────┐
    │开始 │
    └──┬──┘
       │
    ┌──▼──┐
    │输入a│
    └──┬──┘
       │
    ┌──▼──┐
    │b=a*2│
    └──┬──┘
       │
    ┌──▼──┐
    │输出b│
    └──┬──┘
       │
    ┌──▼──┐
    │结束 │
    └─────┘
```

### 四、选择结构流程图

**单分支**
```
    ┌─────┐
    │开始 │
    └──┬──┘
       │
    ┌──▼──┐
    │输入a│
    └──┬──┘
       │
    ┌──▼───┐
    │a>0? │ ← 菱形（判断）
    └─┬───┘
      │
   是 │ 否
   ┌──▼──┐   ┌─────┐
   │输出+│   │输出- │
   └─┬──┘   └─────┘
      │
      └────→┼←─┘
             │
          ┌──▼──┐
          │结束 │
          └─────┘
```

**双分支**
```
    ┌─────┐
    │开始 │
    └──┬──┘
       │
    ┌──▼──┐
    │输入a│
    └──┬──┘
       │
    ┌──▼───┐
    │a>0? │
    └─┬───┘
      │
   是 └──┴─── 否
   ┌──▼──┐    ┌──▼──┐
   │输出正│    │输出非正│
   └──┬──┘    └─────┘
      │
   ┌──▼──┐
   │结束 │
   └─────┘
```

### 五、循环结构流程图

**while循环**
```
    ┌─────┐
    │开始 │
    └──┬──┘
       │
    ┌──▼──┐
    │i=1  │
    │sum=0│
    └──┬──┘
       │
    ┌──▼───┐
    │i<=100│ ← 循环条件
    └─┬───┘
      │
   是 └──┴─── 否
   ┌──▼──┐    ┌─────┐
   │sum=sum│   │输出sum│
   │+i    │   └─┬───┘
   └─┬──┘      │
    ┌▼────────┘
   ┌┴─────┐
   │i=i+1 │
   └──────┘
```

### 六、流程图示例

**求两个数最大值**
```
    ┌─────┐
    │开始 │
    └──┬──┘
       │
    ┌──▼──────────┐
    │输入a, b     │
    └──┬──────────┘
       │
    ┌──▼───┐
    │a>b?  │
    └─┬───┘
      │
   是 └──┴─── 否
   ┌──▼──┐    ┌──▼──┐
   │max=a│    │max=b│
   └─┬──┘    └─┬──┘
      │        │
      └─┬──┬──┘
        └──┴──→┌──▼───┐
                │输出max│
                └──┬───┘
                   │
                ┌──▼──┐
                │结束 │
                └─────┘
```

### 七、注意事项

1. 流程图要清晰反映算法逻辑
2. 箭头方向表示执行顺序
3. 判断框有两个出口（是/否）
4. 循环框要有明确的循环条件""",
            "summary": "流程图是用图形符号描述算法的工具，包括开始/结束、输入/输出、处理、判断、循环等符号",
            "code_example": """#include <stdio.h>

// 用流程图思路求最大值
int main(void) {
    int a, b, max;

    // 输入
    printf("输入两个整数：");
    scanf("%d%d", &a, &b);

    // 判断（对应流程图中的菱形判断框）
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
            "code_explanation": "演示了求最大值算法的实现，对应流程图的选择结构",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["算法的基本概念", "选择结构", "循环结构"],
            "tips": ["先画流程图再写代码", "菱形表示判断，有两个出口", "注意循环条件的设置"],
            "common_mistakes": ["流程图方向混乱", "判断框出口不完整", "循环条件设置错误"]
        },
        {
            "name": "伪代码",
            "order_index": 3,
            "content": """## 伪代码

### 一、伪代码简介

伪代码是介于自然语言和编程语言之间的描述方式，用于描述算法逻辑。

**特点**
- 不需要遵守编程语言的语法
- 接近自然语言，易于理解
- 可以直接转换成程序代码

### 二、伪代码的基本结构

**顺序结构**
```
语句1
语句2
语句3
```

**选择结构**
```
如果 条件 则
    语句块1
否则
    语句块2
```

或者
```
如果 条件 则
    语句块
```

**循环结构**
```
当 条件 成立
    循环体
```

或者
```
循环 初始值 到 终止值
    循环体
```

### 三、伪代码示例

**求三个数中的最大值**
```
输入 a, b, c
max = a
如果 b > max
    max = b
如果 c > max
    max = c
输出 max
```

**累加1到100**
```
sum = 0
i = 1
当 i <= 100
    sum = sum + i
    i = i + 1
输出 sum
```

**判断成绩等级**
```
输入 score
如果 score >= 90
    输出 "A"
否则如果 score >= 80
    输出 "B"
否则如果 score >= 60
    输出 "C"
否则
    输出 "D"
```

**冒泡排序（部分）**
```
对于 i 从 0 到 n-2
    对于 j 从 0 到 n-i-2
        如果 a[j] > a[j+1]
            交换 a[j] 和 a[j+1]
```

### 四、伪代码到代码的转换

**伪代码**
```
输入 n
如果 n > 0
    输出 "正数"
否则
    输出 "非正数"
```

**转换为C代码**
```c
int n;
scanf("%d", &n);
if (n > 0) {
    printf("正数\\n");
} else {
    printf("非正数\\n");
}
```

### 五、伪代码的书写规范

1. 每行描述一个操作
2. 使用缩进表示层次
3. 变量名要清晰
4. 注释说明关键步骤
5. 保持简洁明了

### 六、示例：判断素数

**伪代码**
```
输入 n
如果 n <= 1
    输出 "不是素数"
否则
    是素数 = 真
    对于 i 从 2 到 n-1
        如果 n 能被 i 整除
            是素数 = 假
            退出循环
    如果 是素数
        输出 "是素数"
    否则
        输出 "不是素数"
```

### 七、注意事项

1. 伪代码要描述清楚算法逻辑
2. 注意条件判断的完整性
3. 循环要有明确的终止条件
4. 从伪代码转换到代码时注意语法""",
            "summary": "伪代码是介于自然语言和代码之间的描述方式，便于描述算法逻辑和转换为代码",
            "code_example": """#include <stdio.h>

// 伪代码示例：判断素数
int main(void) {
    int n, i, is_prime = 1;

    printf("输入一个整数：");
    scanf("%d", &n);

    if (n <= 1) {
        is_prime = 0;
    } else {
        for (i = 2; i < n; i++) {
            if (n % i == 0) {
                is_prime = 0;
                break;
            }
        }
    }

    if (is_prime) {
        printf("%d是素数\\n", n);
    } else {
        printf("%d不是素数\\n", n);
    }

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了素数判断算法的伪代码和对应C代码实现",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["算法的基本概念", "流程图", "循环结构"],
            "tips": ["伪代码便于理清算法逻辑", "注意条件判断的完整性", "循环要有明确的终止条件"],
            "common_mistakes": ["伪代码过于笼统", "条件判断不完整", "循环终止条件错误"]
        },
        {
            "name": "常见错误分析",
            "order_index": 4,
            "content": """## 常见错误分析

### 一、错误分类

**1. 编译错误（语法错误）**
- 违反C语言语法规则
- 编译器能直接检测

**2. 链接错误**
- 编译通过但链接失败
- 通常是函数或变量未定义

**3. 运行错误**
- 程序能运行但结果错误
- 逻辑错误最难发现

### 二、编译错误示例

**缺少分号**
```c
int a = 10  // 错误！缺少分号
```
错误信息：syntax error

**括号不匹配**
```c
if (a > b {  // 错误！缺少右括号
```
错误信息：expected ')'

**变量未声明**
```c
a = 10;  // 错误！变量a未声明
```
错误信息：'a' undeclared

**类型不匹配**
```c
int *p = "hello";  // 错误！类型不匹配
```

### 三、运行错误示例

**除零错误**
```c
int a = 10 / 0;  // 运行错误！程序崩溃
```

**数组越界**
```c
int a[5];
a[10] = 100;  // 越界访问，可能崩溃
```

**访问空指针**
```c
int *p = NULL;
*p = 10;  // 运行错误！空指针访问
```

### 四、逻辑错误示例

**整数除法问题**
```c
int a = 5, b = 2;
int avg = a + b / 2;  // 错误！结果应该是3.5，但实际是6
```
正确写法：
```c
int avg = (a + b) / 2;      // 整数除法：3
double avg = (a + b) / 2.0; // 浮点除法：3.5
```

**循环边界错误**
```c
// 意图：输出1到10
for (int i = 1; i < 10; i++) {  // 错误！只输出1到9
    printf("%d ", i);
}
```
正确写法：
```c
for (int i = 1; i <= 10; i++) {  // 正确
    printf("%d ", i);
}
```

**比较运算符错误**
```c
int score = 60;
if (score = 100) {  // 错误！应该是==，这里成了赋值
    printf("满分！\\n");
}
```
正确写法：
```c
if (score == 100) {  // 正确
    printf("满分！\\n");
}
```

### 五、常见错误总结

| 错误类型 | 示例 | 后果 | 解决方法 |
|----------|------|------|----------|
| 少分号 | int a=10 | 编译错误 | 检查每条语句 |
| 括号不匹配 | if(a>b{ | 编译错误 | 使用IDE括号匹配 |
| =和==混淆 | if(a=10) | 逻辑错误 | 赋值表达式不会恒真 |
| 整数除法 | a+b/2 | 结果错误 | 转为浮点除法 |
| 数组越界 | a[n] n超出范围 | 崩溃/数据破坏 | 检查边界 |
| 未初始化 | int a; printf("%d",a) | 结果不确定 | 先初始化 |

### 六、调试方法

**1. 阅读编译错误信息**
- 错误行号指出问题位置
- 仔细阅读错误描述

**2. 使用IDE调试工具**
- 设置断点
- 单步执行
- 观察变量值

**3. 添加输出语句**
- 在关键位置输出变量值
- 跟踪程序执行流程

**4. 简化问题**
- 注释掉部分代码
- 缩小问题范围

### 七、注意事项

1. 学会阅读编译错误信息
2. 常见错误要总结记忆
3. 使用=和==要区分清楚
4. 整数除法要特别注意
5. 数组下标不能越界""",
            "summary": "常见错误分为编译错误、运行错误和逻辑错误，需要学会阅读错误信息和调试方法",
            "code_example": """#include <stdio.h>

int main(void) {
    // 错误1：忘记分号
    // int a = 10  // 编译错误

    // 错误2：=和==混淆
    int score = 60;
    // if (score = 100) {  // 错误！这是赋值，不是比较
    if (score == 100) {    // 正确
        printf("满分！\\n");
    }

    // 错误3：整数除法
    int a = 5, b = 2;
    printf("a+b/2 = %d (错误)\\n", a + b / 2);        // 6
    printf("(a+b)/2 = %d\\n", (a + b) / 2);           // 3
    printf("(a+b)/2.0 = %.1f\\n", (a + b) / 2.0);    // 3.5

    // 正确做法：先转浮点再除
    double avg = (a + b) / 2.0;
    printf("平均值：%.1f\\n", avg);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了几种常见的错误，包括=和==混淆、整数除法问题，以及正确写法",
            "difficulty": 2,
            "importance": 5,
            "related_points": ["算法的基本概念", "选择结构", "循环结构"],
            "tips": ["学会阅读编译错误信息", "养成调试习惯", "注意=和==的区别"],
            "common_mistakes": ["忘记分号", "整数除法丢失精度", "变量名拼写错误", "=和==混淆"]
        },
        {
            "name": "编程风格",
            "order_index": 5,
            "content": """## 编程风格

### 一、编程风格的重要性

良好的编程风格可以：
- 提高代码可读性
- 便于维护和修改
- 减少错误发生
- 方便团队协作

### 二、缩进规范

**推荐：4空格缩进**
```c
int main(void) {
    int a = 10;
    if (a > 0) {
        printf("positive\\n");
    }
    return 0;
}
```

**不推荐：Tab或2空格**
```c
int main(void) {
  int a = 10;    // Tab（不统一）
    if (a > 0) {
        printf("positive\\n");
    }
    return 0;
}
```

### 三、空行使用

**函数之间加空行**
```c
int func1(void) {
    // ...
    return 0;
}

// 空行分隔
int func2(void) {
    // ...
    return 0;
}
```

**逻辑段落之间加空行**
```c
int main(void) {
    // 输入
    int a, b;
    scanf("%d%d", &a, &b);

    // 处理
    int sum = a + b;

    // 输出
    printf("sum = %d\\n", sum);

    return 0;
}
```

### 四、命名规范

**变量命名**
```c
// 好命名
int student_age;
int total_score;
double account_balance;

// 差命名
int a;      // 不知道代表什么
int x1;     // 不直观
int temp;   // 太模糊
```

**常量命名**
```c
#define MAX_SIZE 100
#define BUFFER_SIZE 1024
const int TIME_OUT = 5000;
```

**函数命名**
```c
int calculate_sum(void);
void print_message(void);
int find_max(int a, int b);
```

### 五、注释规范

**必要的注释**
```c
// 计算圆的面积
double radius = 5.0;
double area = PI * radius * radius;

// 判断是否及格
if (score >= 60) {
    printf("及格\\n");
}
```

**不要废话注释**
```c
int a = 10;  // 给a赋值为10（废话）
```

### 六、代码布局

**一行一句**
```c
// 推荐
int a = 10;
int b = 20;
int sum = a + b;

// 不推荐
int a = 10; int b = 20; int sum = a + b;
```

**花括号对齐**
```c
// 推荐
if (a > b) {
    max = a;
} else {
    max = b;
}
```

### 七、函数设计原则

1. **函数要短小** - 一个函数做一件事
2. **函数名要描述** - 函数名反映其功能
3. **参数要少** - 参数最好不超过3个
4. **避免副作用** - 函数最好只返回一个值

**示例**
```c
// 好函数
int max(int a, int b) {
    return (a > b) ? a : b;
}

// 差函数
void process(int a, int b, int *c, int *d, int *e) {
    // 太多参数和副作用
}
```

### 八、其他建议

1. 代码行数不要太长（建议80字符以内）
2. 变量声明放在函数开头
3. 避免使用全局变量
4. 使用有意义的名字
5. 保持风格一致""",
            "summary": "良好的编程风格包括合理缩进、有意义命名、适当注释、代码整洁清晰",
            "code_example": """#include <stdio.h>

// 宏常量（全大写）
#define MAX_SIZE 100
#define PI 3.14159

// 好风格的代码示例
int main(void) {
    // 1. 变量命名有意义
    int student_age = 20;
    int total_score = 95;
    char grade = 'A';

    // 2. 合理使用空行分隔逻辑
    printf("学生信息：\\n");
    printf("年龄：%d岁\\n", student_age);
    printf("总分：%d\\n", total_score);

    // 3. 适当的注释
    // 判断等级
    if (total_score >= 90) {
        grade = 'A';
    } else if (total_score >= 80) {
        grade = 'B';
    } else if (total_score >= 60) {
        grade = 'C';
    } else {
        grade = 'D';
    }

    printf("等级：%c\\n", grade);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "展示了良好编程风格的示例，包括有意义的变量名、合理空行、适当注释",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["常见错误分析", "程序调试", "代码规范"],
            "tips": ["保持代码风格一致", "代码要整洁清晰", "多阅读开源代码学习风格"],
            "common_mistakes": ["不缩进或缩进混乱", "变量名无意义", "不写注释", "代码过于拥挤"]
        },
        {
            "name": "程序调试方法",
            "order_index": 6,
            "content": """## 程序调试方法

### 一、调试的基本概念

**调试（Debug）**：找出程序中错误并修复的过程。

**Bug**：程序中的错误或缺陷。

**Debugger**：用于调试程序的工具。

### 二、调试方法分类

**1. 暴力调试**
- 添加输出语句
- 适合简单问题

**2. IDE调试**
- 使用集成开发环境的调试功能
- 适合复杂问题

**3. 日志调试**
- 输出程序运行轨迹
- 适合生产环境

### 三、使用输出语句调试

**添加打印语句**
```c
#include <stdio.h>

int main(void) {
    int a = 10, b = 0;
    printf("DEBUG: a = %d, b = %d\\n", a, b);  // 调试信息

    for (int i = 0; i < a; i++) {
        b += i;
        printf("DEBUG: i = %d, b = %d\\n", i, b);  // 循环中的值
    }

    printf("RESULT: b = %d\\n", b);
    return 0;
}
```

**注意事项**
- 标记调试输出，便于查找
- 调试完后删除或注释掉

### 四、IDE调试功能

**Code::Blocks调试**
1. 在代码行号左侧单击设置断点
2. 按F8开始调试
3. 按F7逐语句执行
4. 观察Variables窗口中的变量值

**Visual Studio调试**
1. F9设置断点
2. F5开始调试
3. F10逐过程，F11逐语句
4. Watch窗口监视变量

### 五、断点类型

**普通断点**
- 程序执行到该行前暂停
- 最常用的断点类型

**条件断点**
```
if (i == 10)  // 当i等于10时暂停
```

**监视点**
- 当特定变量值改变时暂停

### 六、调试步骤

1. **重现问题** - 确定在什么情况下出现问题
2. **定位问题** - 找出问题所在的代码位置
3. **分析原因** - 理解为什么出错
4. **修复问题** - 修改代码
5. **验证修复** - 确认问题已解决

### 七、常见调试案例

**案例1：循环错误**
```c
// 问题代码：输出1到10的和
int sum = 0;
for (int i = 1; i < 10; i++) {  // 错误！i<10应该是i<=10
    sum += i;
}
// 结果是45而不是55
```

**调试方法**：在循环中打印i的值
```c
for (int i = 1; i <= 10; i++) {
    printf("i = %d, sum = %d\\n", i, sum);
    sum += i;
}
```

**案例2：数组越界**
```c
int a[5] = {1, 2, 3, 4, 5};
for (int i = 0; i <= 5; i++) {  // 错误！<=应该是<
    printf("%d ", a[i]);
}
// a[5]越界！
```

### 八、调试技巧

1. **二分查找** - 注释掉一半代码，确定问题在半段
2. **单步执行** - 逐语句执行，观察变量变化
3. **打印关键变量** - 在关键位置输出变量值
4. **简化输入** - 用最简单的输入测试
5. **注意边界** - 特别检查边界条件

### 九、注意事项

1. 调试不能替代思考
2. 先分析再调试
3. 记录调试过程
4. 问题修复后要验证
5. 保持冷静""",
            "summary": "程序调试是找出并修复程序错误的过程，包括输出语句调试和IDE调试两种方法",
            "code_example": """#include <stdio.h>

int main(void) {
    int a[5] = {1, 2, 3, 4, 5};
    int sum = 0;

    printf("=== 调试开始 ===\\n");

    for (int i = 0; i < 5; i++) {  // 注意边界：i<5而不是i<=5
        printf("DEBUG: i=%d, a[%d]=%d\\n", i, i, a[i]);
        sum += a[i];
        printf("DEBUG: sum after add = %d\\n", sum);
    }

    printf("=== 调试结束 ===\\n");
    printf("最终结果：sum = %d\\n", sum);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了使用输出语句进行调试的方法，通过打印变量值跟踪程序执行",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["常见错误分析", "循环结构", "数组"],
            "tips": ["在关键位置添加调试输出", "单步执行观察变量变化", "注意边界条件"],
            "common_mistakes": ["不习惯使用调试工具", "边界条件错误", "忘记删调试代码"]
        },
        {
            "name": "程序测试基础",
            "order_index": 7,
            "content": """## 程序测试基础

### 一、程序测试的概念

**测试**：验证程序是否按预期工作。

**测试用例**：一组输入值和预期输出。

### 二、测试用例设计

**正常测试**
```c
// 输入：5，预期：1*2*3*4*5 = 120
int main(void) {
    int n = 5, factorial = 1;
    for (int i = 1; i <= n; i++) {
        factorial *= i;
    }
    printf("%d", factorial);  // 应该是120
    return 0;
}
```

**边界测试**
```c
// 测试n=0，预期：1（0! = 1）
// 测试n=1，预期：1
// 测试n=2，预期：2
```

**异常测试**
```c
// 测试负数，预期：报错或特殊处理
```

### 三、黑盒测试与白盒测试

**黑盒测试**
- 只关心输入和输出
- 不考虑程序内部实现

**白盒测试**
- 考虑程序内部结构
- 测试每条执行路径

### 四、测试覆盖

**语句覆盖**
- 每个语句至少执行一次

**分支覆盖**
- 每个分支至少执行一次

**路径覆盖**
- 每个可能的路径至少执行一次

### 五、简单测试示例

```c
#include <stdio.h>

// 被测试函数：求最大值
int max(int a, int b) {
    return (a > b) ? a : b;
}

// 测试函数
void test_max(void) {
    // 测试1：正常情况
    printf("max(3,5) = %d, 预期 = 5, %s\\n",
           max(3,5), max(3,5)==5 ? "PASS" : "FAIL");

    // 测试2：相等情况
    printf("max(5,5) = %d, 预期 = 5, %s\\n",
           max(5,5), max(5,5)==5 ? "PASS" : "FAIL");

    // 测试3：负数情况
    printf("max(-3,5) = %d, 预期 = 5, %s\\n",
           max(-3,5), max(-3,5)==5 ? "PASS" : "FAIL");
}

int main(void) {
    test_max();
    return 0;
}
```

### 六、测试原则

1. 测试用例要有代表性
2. 既要测正常情况，也要测异常情况
3. 注意边界条件测试
4. 测试后要验证结果
5. 保持测试的独立性""",
            "summary": "程序测试通过设计测试用例验证程序正确性，包括正常测试、边界测试和异常测试",
            "code_example": """#include <stdio.h>

// 求最大值函数
int max(int a, int b) {
    return (a > b) ? a : b;
}

// 简单测试框架
void test(void) {
    struct {
        int a, b, expected;
    } cases[] = {
        {3, 5, 5},      // 正常情况
        {5, 3, 5},      // 交换顺序
        {5, 5, 5},      // 相等
        {-3, 5, 5},     // 含负数
        {-3, -5, -3},   // 两个负数
    };

    int n = sizeof(cases) / sizeof(cases[0]);
    int passed = 0;

    for (int i = 0; i < n; i++) {
        int result = max(cases[i].a, cases[i].b);
        int pass = (result == cases[i].expected);
        printf("用例%d: max(%d,%d)=%d, %s\\n",
               i+1, cases[i].a, cases[i].b, result,
               pass ? "PASS" : "FAIL");
        if (pass) passed++;
    }

    printf("\\n通过率: %d/%d\\n", passed, n);
}

int main(void) {
    test();
    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了简单的测试框架设计，包含多个测试用例验证max函数正确性",
            "difficulty": 1,
            "importance": 3,
            "related_points": ["常见错误分析", "程序调试", "选择结构"],
            "tips": ["测试用例要有代表性", "注意边界条件测试", "测试后验证结果"],
            "common_mistakes": ["只测正常情况", "忽略边界条件", "测试后不验证"]
        }
    ]
}


async def generate():
    """生成第1章第3节知识点"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 查找第1章第3节
        result = await db.execute(
            select(Section)
            .where(Section.order_index == 3)
            .where(Section.title.like("%设计%") | Section.title.like("%基础%"))
        )
        section = result.scalar_one_or_none()

        if not section:
            # 尝试另一种方式查找
            result = await db.execute(
                select(Section)
                .join(Chapter := __import__('app.models.chapter', fromlist=['Chapter']).Chapter,
                      Section.chapter_id == Chapter.id)
                .where(Chapter.order_index == 1)
                .where(Section.order_index == 3)
            )
            section = result.scalar_one_or_none()

        if not section:
            print("请先运行第1章前两节的生成脚本")
            return

        # 清空现有知识点
        await db.execute(text("DELETE FROM section_knowledge_points WHERE section_id = :sid"), {"sid": section.id})

        # 更新小节信息
        section.title = SECTION_DATA["section_title"]
        section.description = SECTION_DATA["section_description"]
        section.estimated_minutes = SECTION_DATA["estimated_minutes"]

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
        print(f"\\n第1章第3节生成完成！")
        print(f"小节名称: {SECTION_DATA['section_title']}")
        print(f"知识点数量: {len(SECTION_DATA['knowledge_points'])}个")


if __name__ == "__main__":
    asyncio.run(generate())
