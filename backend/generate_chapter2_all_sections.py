"""Generate Chapter 2: 选择控制结构与应用 - 按教学大纲生成"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint
from sqlalchemy import select, text


# 第2章：选择控制结构与应用
# 教学大纲：
# 2.1 关系运算符、逻辑运算符及表达式等
# 2.2 if选择结构一般形式、流程图、嵌套及表达式拓展
# 2.3 switch语句的表达形式及其使用方法
# 2.4 应用实例

CHAPTER_DATA = {
    "chapter_title": "选择控制结构与应用",
    "chapter_description": "学习C语言的选择控制语句，包括关系运算、条件语句和switch语句",
    "sections": [
        {
            "title": "关系运算与逻辑运算",
            "description": "关系运算符、逻辑运算符及表达式",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "关系运算符",
                    "order_index": 1,
                    "content": """## 关系运算符

关系运算符用于比较两个值的大小关系，返回真(1)或假(0)。

### 一、运算符列表

| 运算符 | 含义 | 示例 |
|--------|------|------|
| > | 大于 | a > b |
| < | 小于 | a < b |
| >= | 大于等于 | a >= b |
| <= | 小于等于 | a <= b |
| == | 等于 | a == b |
| != | 不等于 | a != b |

### 二、运算结果

关系运算的结果是整数：
- **真(1)**：条件成立
- **假(0)**：条件不成立

```c
int a = 10, b = 20;
int r1 = a > b;    // r1 = 0（假）
int r2 = a < b;    // r2 = 1（真）
int r3 = a == 10;  // r3 = 1（真）
```

### 三、基本使用

```c
#include <stdio.h>

int main(void) {
    int a = 10, b = 20;

    printf("a > b = %d\\n", a > b);   // 0
    printf("a < b = %d\\n", a < b);   // 1
    printf("a >= 10 = %d\\n", a >= 10); // 1
    printf("a <= b = %d\\n", a <= b);   // 1
    printf("a == 10 = %d\\n", a == 10); // 1
    printf("a != b = %d\\n", a != b);   // 1

    return 0;
}
```

### 四、重要提醒

**= 与 == 的区别**

```c
int a = 10;

// 赋值：把10赋给a
a = 10;

// 比较：判断a是否等于10
a == 10;

// 错误写法（常见bug）
if (a = 10) {  // 这是赋值，条件永远为真！
    printf("总是执行\\n");
}

// 正确写法
if (a == 10) {
    printf("a等于10\\n");
}
```

### 五、注意事项

1. `==` 是比较运算符，不是赋值运算符
2. 关系运算结果要么是1（真），要么是0（假）
3. 浮点数比较要小心精度问题
```c
// 浮点数比较问题
if (0.1 + 0.2 == 0.3) {  // 可能不成立！因为精度问题
    printf("相等\\n");
}
// 正确做法：判断差值是否足够小
if (fabs(0.1 + 0.2 - 0.3) < 1e-6) {
    printf("近似相等\\n");
}
```

### 六、与if语句配合

```c
int age = 20;

if (age >= 18) {  // 使用 >= 比较
    printf("成年人\\n");
}

if (age == 20) {  // 使用 == 比较是否相等
    printf("正好20岁\\n");
}
```""",
                    "summary": "关系运算符用于比较大小，包括>,<,>=,<=,==,!=，结果是1（真）或0（假）",
                    "code_example": """#include <stdio.h>

int main(void) {
    int a = 10, b = 20;

    printf("a=%d, b=%d\\n", a, b);
    printf("a > b  = %d\\n", a > b);   // 0
    printf("a < b  = %d\\n", a < b);   // 1
    printf("a >= 10 = %d\\n", a >= 10); // 1
    printf("a == 10 = %d\\n", a == 10); // 1
    printf("a != b  = %d\\n", a != b);   // 1

    // =与==的区别演示
    if (a == 10) {
        printf("a等于10\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了各种关系运算符的使用，以及=和==的区别",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["逻辑运算符", "if语句", "条件表达式"],
                    "tips": ["==是比较运算符，不是赋值", "注意=和==的区别", "浮点数比较要小心精度"],
                    "common_mistakes": ["混淆=和==", "浮点数比较错误", "关系运算符优先级错误"]
                },
                {
                    "name": "逻辑运算符",
                    "order_index": 2,
                    "content": """## 逻辑运算符

逻辑运算符用于组合多个条件，构成更复杂的表达式。

### 一、运算符列表

| 运算符 | 含义 | 说明 |
|--------|------|------|
| && | 逻辑与 | 所有条件都为真时结果为真 |
| \\|\\| | 逻辑或 | 任意一个条件为真时结果为真 |
| ! | 逻辑非 | 取反，真变假，假变真 |

### 二、真值表

**&&（与）**
| A | B | A && B |
|---|---|--------|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

**||（或）**
| A | B | A \\|\\| B |
|---|---|---------|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

**!（非）**
| A | !A |
|---|----|
| 0 | 1 |
| 1 | 0 |

### 三、基本使用

```c
#include <stdio.h>

int main(void) {
    int a = 10, b = 20, c = 5;

    // && 逻辑与：所有条件都为真
    if (a > 0 && b > 0) {
        printf("a和b都是正数\\n");
    }

    // || 逻辑或：任意一个条件为真
    if (a > 0 || c > 0) {
        printf("a和c至少有一个是正数\\n");
    }

    // ! 逻辑非：取反
    if (!(a < 0)) {
        printf("a不是负数\\n");
    }

    return 0;
}
```

### 四、短路求值

**&& 的短路**
- 如果第一个条件为假，不再判断第二个条件
```c
int a = 0, b = 10;
if (a != 0 && b/a > 1) {  // 第一个条件为假，不会执行b/a
    // 不会进入这里
}
```

**|| 的短路**
- 如果第一个条件为真，不再判断第二个条件
```c
int a = 10, b = 0;
if (a > 0 || b/a > 1) {  // 第一个条件为真，不会执行b/a
    // 会进入这里
}
```

### 五、综合示例

```c
#include <stdio.h>

int main(void) {
    int year = 2024;

    // 判断闰年：能被4整除但不能被100整除，或者能被400整除
    if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)) {
        printf("%d年是闰年\\n", year);
    } else {
        printf("%d年不是闰年\\n", year);
    }

    // 判断年龄段
    int age = 25;
    if (age < 0 || age > 150) {
        printf("年龄不合法\\n");
    } else if (age < 18) {
        printf("未成年\\n");
    } else if (age < 60) {
        printf("成年人\\n");
    } else {
        printf("老年人\\n");
    }

    return 0;
}
```

### 六、优先级

```c
// 优先级：! > && > ||
// 建议加括号明确意图

if (!a && b || c)      // 可能产生歧义
if ((!a && b) || c)    // 明确先算!a && b，再||c
if (!(a && (b || c)))  // 注意括号位置
```

### 七、注意事项

1. && 优先级高于 ||
2. ! 优先级最高
3. 利用短路特性可以避免某些错误
4. 建议多加括号使表达式更清晰""",
                    "summary": "逻辑运算符包括&&（与）、||（或）、!（非），用于组合多个条件",
                    "code_example": """#include <stdio.h>

int main(void) {
    int a = 10, b = 20, c = 30;

    // 逻辑与：所有条件都为真才成立
    printf("a>0 && b>0 = %d\\n", a>0 && b>0);  // 1
    printf("a>0 && c<0 = %d\\n", a>0 && c<0);  // 0

    // 逻辑或：任意一个条件为真就成立
    printf("a>0 || c<0 = %d\\n", a>0 || c<0);  // 1
    printf("a<0 || c<0 = %d\\n", a<0 || c<0);  // 0

    // 逻辑非
    printf("!a<0 = %d\\n", !a<0);  // 1

    // 综合判断
    if ((a + b > c) && (b > 0)) {
        printf("a+b大于c且b为正数\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了逻辑运算符的使用，包括&&、||、!以及综合判断",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["关系运算符", "if语句", "条件表达式"],
                    "tips": ["注意短路求值特性", "&&优先级高于||", "建议多加括号"],
                    "common_mistakes": ["混淆&和&&", "忽略运算符优先级", "!=和!==混淆"]
                },
                {
                    "name": "条件表达式（三目运算符）",
                    "order_index": 3,
                    "content": """## 条件表达式（三目运算符）

条件运算符是C语言中唯一的三目运算符，是if-else的简化形式。

### 一、语法

```c
条件 ? 表达式1 : 表达式2
```

### 二、说明

- 如果**条件为真**，返回**表达式1**的值
- 如果**条件为假**，返回**表达式2**的值

### 三、基本使用

```c
#include <stdio.h>

int main(void) {
    int a = 10, b = 20;

    // 求最大值
    int max = (a > b) ? a : b;
    printf("最大值：%d\\n", max);  // 20

    // 求最小值
    int min = (a < b) ? a : b;
    printf("最小值：%d\\n", min);  // 10

    // 求绝对值
    int x = -5;
    int abs_x = (x > 0) ? x : -x;
    printf("绝对值：%d\\n", abs_x);  // 5

    return 0;
}
```

### 四、与if-else对比

**使用if-else**
```c
int max;
if (a > b) {
    max = a;
} else {
    max = b;
}
```

**使用条件运算符**
```c
int max = (a > b) ? a : b;
```

### 五、嵌套使用

```c
// 成绩等级判定
int score = 85;
char grade = (score >= 90) ? 'A' :
             (score >= 80) ? 'B' :
             (score >= 60) ? 'C' : 'D';

printf("等级：%c\\n", grade);  // B
```

### 六、注意事项

1. 条件运算符优先级很低，表达式通常要加括号
2. 表达式1和表达式2类型应一致或可以转换
3. 不要过度嵌套，影响可读性
4. 条件运算符不能代替复杂的if语句

### 七、常见错误

```c
// 错误1：忘记括号
int max = a > b ? a : b;  // 可能产生警告

// 错误2：过度嵌套
char grade = a >= 90 ? 'A' : a >= 80 ? 'B' : ...;  // 可读性差
```""",
                    "summary": "条件运算符(?:)是if-else的简化形式，语法：条件?表达式1:表达式2",
                    "code_example": """#include <stdio.h>

int main(void) {
    int a = 10, b = 20;

    // 基本用法
    int max = (a > b) ? a : b;
    printf("max = %d\\n", max);

    // 求绝对值
    int x = -8;
    int abs_x = (x > 0) ? x : -x;
    printf("|x| = %d\\n", abs_x);

    // 成绩等级
    int score = 75;
    char grade = (score >= 90) ? 'A' :
                 (score >= 80) ? 'B' :
                 (score >= 60) ? 'C' : 'D';
    printf("grade = %c\\n", grade);

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了条件运算符求最大值、绝对值、等级判定",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["if语句", "关系运算符"],
                    "tips": ["简化简单的if-else赋值", "注意优先级", "不要过度嵌套"],
                    "common_mistakes": ["过度使用嵌套", "忘记括号", "与if语句混用"]
                }
            ]
        },
        {
            "title": "if选择结构",
            "description": "if结构一般形式、流程图表达方式及如何使用、if语句的嵌套及实用例、表达式在if结构中使用的拓展",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "if语句基本形式",
                    "order_index": 1,
                    "content": """## if语句基本形式

if语句是C语言中最基本的选择控制语句，用于根据条件决定是否执行某些语句。

### 一、单分支if语句

**语法**
```c
if (条件) {
    // 条件为真时执行的语句
}
```

**流程图**
```
      ┌─────┐
      │开始 │
      └──┬──┘
         │
      ┌──▼───┐
      │条件?  │ ← 菱形判断
      └──┬───┘
         │
      是 └──┴─── 否
      ┌──▼──┐
      │执行  │      （跳过执行）
      └──┬──┘
         │
      ┌──▼──┐
      │继续  │
      └─────┘
```

**示例**
```c
#include <stdio.h>

int main(void) {
    int age = 20;

    if (age >= 18) {
        printf("你已经成年了\\n");
    }

    printf("程序结束\\n");

    return 0;
}
```

### 二、双分支if-else语句

**语法**
```c
if (条件) {
    // 条件为真时执行的语句
} else {
    // 条件为假时执行的语句
}
```

**流程图**
```
      ┌─────┐
      │开始 │
      └──┬──┘
         │
      ┌──▼───┐
      │条件?  │
      └──┬───┘
         │
    是 ┌─┴─┐ 否
    ┌──▼──┐  ┌──▼──┐
    │语句1│  │语句2│
    └──┬──┘  └──┬──┘
       └────┬────┘
            │
         ┌──▼──┐
         │继续  │
         └─────┘
```

**示例**
```c
#include <stdio.h>

int main(void) {
    int num = 10;

    if (num % 2 == 0) {
        printf("%d是偶数\\n", num);
    } else {
        printf("%d是奇数\\n", num);
    }

    return 0;
}
```

### 三、注意事项

1. 条件表达式必须用括号括起来
2. 推荐使用 `{ }` 包裹多条语句
3. else子句不能单独存在
4. else总是与最近的if配对

### 四、if语句的练习

```c
// 判断一个数是正数还是负数
int x = -5;
if (x > 0) {
    printf("正数\\n");
} else {
    printf("非正数\\n");
}

// 判断是否及格
int score = 75;
if (score >= 60) {
    printf("及格\\n");
} else {
    printf("不及格\\n");
}
```""",
                    "summary": "if语句用于条件判断，单分支if只有条件为真时执行，双分支if-else还有条件为假时的处理",
                    "code_example": """#include <stdio.h>

int main(void) {
    int num = 10;

    // 单分支if
    if (num > 0) {
        printf("%d是正数\\n", num);
    }

    // 双分支if-else
    if (num % 2 == 0) {
        printf("%d是偶数\\n", num);
    } else {
        printf("%d是奇数\\n", num);
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了单分支if和双分支if-else语句的使用",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["关系运算符", "逻辑运算符", "if语句嵌套"],
                    "tips": ["条件表达式用括号", "推荐使用大括号", "else与最近的if配对"],
                    "common_mistakes": ["忘记括号", "else匹配错误", "分号误加"]
                },
                {
                    "name": "多分支if-else语句",
                    "order_index": 2,
                    "content": """## 多分支if-else语句

当有多个条件需要判断时，使用多分支if-else语句。

### 一、语法形式

```c
if (条件1) {
    // 条件1为真时执行
} else if (条件2) {
    // 条件1为假，条件2为真时执行
} else if (条件3) {
    // 条件1、2为假，条件3为真时执行
} else {
    // 所有条件都为假时执行
}
```

### 二、成绩等级示例

```c
#include <stdio.h>

int main(void) {
    int score = 85;
    char grade;

    if (score >= 90) {
        grade = 'A';
    } else if (score >= 80) {
        grade = 'B';
    } else if (score >= 70) {
        grade = 'C';
    } else if (score >= 60) {
        grade = 'D';
    } else {
        grade = 'E';
    }

    printf("成绩：%d，等级：%c\\n", score, grade);

    return 0;
}
```

### 三、流程图

```
      ┌─────┐
      │开始 │
      └──┬──┘
         │
      ┌──▼────┐
      │score>=90│
      └──┬────┘
         │
      是┌┴┐否
    ┌──▼──┐ ┌──▼────┐
    │A    │ │score>=80│
    └──┬──┘ └──┬────┘
       │       │
      是┌┴┐否 ┌┴┐
    ┌──▼──┐ │┌─▼────┐
    │...  │ ││ B    │
    └─────┘ └┴──────┘
```

### 四、三个数排序示例

```c
#include <stdio.h>

int main(void) {
    int a, b, c;
    printf("输入三个整数：");
    scanf("%d%d%d", &a, &b, &c);

    int max, mid, min;

    if (a >= b && b >= c) {
        max = a; mid = b; min = c;
    } else if (a >= c && c >= b) {
        max = a; mid = c; min = b;
    } else if (b >= a && a >= c) {
        max = b; mid = a; min = c;
    } else if (b >= c && c >= a) {
        max = b; mid = c; min = a;
    } else if (c >= a && a >= b) {
        max = c; mid = a; min = b;
    } else {
        max = c; mid = b; min = a;
    }

    printf("从大到小：%d > %d > %d\\n", max, mid, min);

    return 0;
}
```

### 五、else-if的配对规则

```c
// else与最近的if配对
if (a > b)
    if (a > c)
        max = a;
    else        // 这个else与 if(a > c) 配对
        max = c;

// 使用大括号明确意图
if (a > b) {
    if (a > c) {
        max = a;
    }
} else {        // 这个else与 if(a > b) 配对
    max = b;
}
```

### 六、注意事项

1. 条件按顺序判断，先写的条件优先级高
2. else子句可以省略
3. 注意else的配对规则
4. 多个条件要用逻辑运算符连接""",
                    "summary": "多分支if-else用于处理多个条件的判断，按顺序逐个判断条件",
                    "code_example": """#include <stdio.h>

int main(void) {
    int score = 78;
    char grade;

    // 多分支判断
    if (score >= 90) {
        grade = 'A';
    } else if (score >= 80) {
        grade = 'B';
    } else if (score >= 70) {
        grade = 'C';
    } else if (score >= 60) {
        grade = 'D';
    } else {
        grade = 'F';
    }

    printf("成绩%d的等级是%c\\n", score, grade);

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了多分支if-else判断成绩等级",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["if语句基本形式", "关系运算符", "逻辑运算符"],
                    "tips": ["条件按顺序判断", "注意else配对", "善用逻辑运算符"],
                    "common_mistakes": ["条件顺序错误", "else匹配混乱", "遗漏边界条件"]
                },
                {
                    "name": "if语句嵌套",
                    "order_index": 3,
                    "content": """## if语句嵌套

嵌套是指在if或else分支中再包含if语句。

### 一、嵌套if语句

**语法**
```c
if (外层条件) {
    if (内层条件) {
        // 外层和内层条件都为真
    } else {
        // 外层条件为真，内层条件为假
    }
} else {
    // 外层条件为假
}
```

### 二、成绩分类详细示例

```c
#include <stdio.h>

int main(void) {
    int score = 85;
    char grade;
    char status[20];

    // 外层：判断是否及格
    if (score >= 60) {
        // 内层：细分等级
        if (score >= 90) {
            grade = 'A';
            strcpy(status, "优秀");
        } else if (score >= 80) {
            grade = 'B';
            strcpy(status, "良好");
        } else {
            grade = 'C';
            strcpy(status, "及格");
        }
    } else {
        grade = 'D';
        strcpy(status, "不及格");
    }

    printf("成绩：%d，等级：%c，评价：%s\\n", score, grade, status);

    return 0;
}
```

### 三、嵌套深度问题

```c
// 嵌套太深（不推荐，超过3层要考虑重构）
if (a > 0) {
    if (b > 0) {
        if (c > 0) {
            printf("都是正数\\n");
        }
    }
}

// 用逻辑运算符替代（推荐）
if (a > 0 && b > 0 && c > 0) {
    printf("都是正数\\n");
}
```

### 四、嵌套与else-if的区别

**嵌套if**
```c
if (a > 0) {
    if (b > 0) {
        // 条件a>0且b>0
    }
}
```

**else-if**
```c
if (a > 0) {
    // 条件a>0
} else if (b > 0) {
    // 条件a<=0且b>0
}
```

### 五、注意事项

1. 嵌套层次不要太深（建议不超过3层）
2. 使用大括号明确else的配对
3. 深层嵌套考虑用逻辑运算符改写
4. 保持代码清晰可读""",
                    "summary": "if语句可以嵌套使用，但嵌套层次不要太深，建议不超过3层",
                    "code_example": """#include <stdio.h>
#include <string.h>

int main(void) {
    int score = 85;
    char grade;

    // 嵌套if：先判断是否及格，再细分等级
    if (score >= 60) {
        if (score >= 90) {
            grade = 'A';
        } else if (score >= 80) {
            grade = 'B';
        } else {
            grade = 'C';
        }
    } else {
        grade = 'D';
    }

    printf("成绩等级：%c\\n", grade);

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了嵌套if语句的使用，先判断及格再细分等级",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["if语句基本形式", "多分支if-else", "逻辑运算符"],
                    "tips": ["嵌套层次不要太深", "用大括号明确配对", "考虑用逻辑运算符替代"],
                    "common_mistakes": ["else配对错误", "嵌套过深", "条件重复判断"]
                },
                {
                    "name": "if语句典型应用",
                    "order_index": 4,
                    "content": """## if语句典型应用

### 一、求解方程根

```c
#include <stdio.h>
#include <math.h>

int main(void) {
    double a, b, c, delta, x1, x2;

    printf("输入一元二次方程系数a,b,c：");
    scanf("%lf%lf%lf", &a, &b, &c);

    if (a == 0) {
        printf("不是二次方程\\n");
    } else {
        delta = b * b - 4 * a * c;

        if (delta > 0) {
            x1 = (-b + sqrt(delta)) / (2 * a);
            x2 = (-b - sqrt(delta)) / (2 * a);
            printf("有两个实根：%.2f 和 %.2f\\n", x1, x2);
        } else if (delta == 0) {
            x1 = -b / (2 * a);
            printf("有一个实根：%.2f\\n", x1);
        } else {
            printf("无实根\\n");
        }
    }

    return 0;
}
```

### 二、石头剪刀布游戏判断

```c
#include <stdio.h>

int main(void) {
    int player, computer;

    printf("请出拳（0-石头，1-剪刀，2-布）：");
    scanf("%d", &player);

    computer = 1;  // 假设电脑出剪刀

    if (player < 0 || player > 2) {
        printf("无效输入\\n");
    } else if (player == computer) {
        printf("平局！\\n");
    } else if ((player == 0 && computer == 1) ||
               (player == 1 && computer == 2) ||
               (player == 2 && computer == 0)) {
        printf("你赢了！\\n");
    } else {
        printf("你输了！\\n");
    }

    return 0;
}
```

### 三、计算器基本功能

```c
#include <stdio.h>

int main(void) {
    double a, b, result;
    char op;

    printf("输入两个操作数和运算符（如 3 + 5）：");
    scanf("%lf %c %lf", &a, &op, &b);

    if (op == '+') {
        result = a + b;
    } else if (op == '-') {
        result = a - b;
    } else if (op == '*') {
        result = a * b;
    } else if (op == '/') {
        if (b != 0) {
            result = a / b;
        } else {
            printf("除数不能为零！\\n");
            return 1;
        }
    } else {
        printf("无效运算符！\\n");
        return 1;
    }

    printf("%.2f %c %.2f = %.2f\\n", a, op, b, result);

    return 0;
}
```

### 四、注意事项

1. 先考虑正常情况，再考虑边界情况
2. 除法要先判断除数是否为零
3. 使用else-if处理多个互斥条件
4. 复杂判断考虑拆分成多个简单判断""",
                    "summary": "if语句典型应用包括方程求解、游戏判断、计算器等实际场景",
                    "code_example": """#include <stdio.h>

int main(void) {
    int choice;
    double a, b;

    printf("1-加法 2-减法 3-乘法 4-除法\\n");
    printf("选择运算：");
    scanf("%d", &choice);

    printf("输入两个数：");
    scanf("%lf%lf", &a, &b);

    if (choice == 1) {
        printf("%.2f + %.2f = %.2f\\n", a, b, a + b);
    } else if (choice == 2) {
        printf("%.2f - %.2f = %.2f\\n", a, b, a - b);
    } else if (choice == 3) {
        printf("%.2f * %.2f = %.2f\\n", a, b, a * b);
    } else if (choice == 4) {
        if (b != 0) {
            printf("%.2f / %.2f = %.2f\\n", a, b, a / b);
        } else {
            printf("除数不能为零！\\n");
        }
    } else {
        printf("无效选择！\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了if-else用于实现简单计算器的菜单选择",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["if语句基本形式", "多分支if-else"],
                    "tips": ["先处理特殊情况", "注意边界条件", "保持代码清晰"],
                    "common_mistakes": ["忽略边界条件", "除法不判断零", "条件重复"]
                }
            ]
        },
        {
            "title": "switch语句",
            "description": "switch语句的表达形式及其使用方法和简单的应用实例",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "switch语句基础",
                    "order_index": 1,
                    "content": """## switch语句基础

switch语句用于多分支选择，根据表达式的值选择执行不同的代码块。

### 一、语法形式

```c
switch (表达式) {
    case 常量1:
        // 语句块1
        break;
    case 常量2:
        // 语句块2
        break;
    case 常量3:
        // 语句块3
        break;
    default:
        // 默认语句块
}
```

### 二、执行流程

1. 计算switch后面表达式的值
2. 将表达式的值与各case后的常量比较
3. 如果匹配，执行相应case后的语句
4. 如果都不匹配，执行default后的语句
5. 遇到break或switch结束退出

### 三、基本示例

```c
#include <stdio.h>

int main(void) {
    int day;
    printf("输入星期几（1-7）：");
    scanf("%d", &day);

    switch (day) {
        case 1:
            printf("星期一\\n");
            break;
        case 2:
            printf("星期二\\n");
            break;
        case 3:
            printf("星期三\\n");
            break;
        case 4:
            printf("星期四\\n");
            break;
        case 5:
            printf("星期五\\n");
            break;
        case 6:
            printf("星期六\\n");
            break;
        case 7:
            printf("星期日\\n");
            break;
        default:
            printf("无效输入\\n");
    }

    return 0;
}
```

### 四、switch的特点

1. **表达式的值必须是整数类型**（int、char、枚举等）
2. **case后的常量必须不同**
3. **case后可以是多个语句，不需要大括号**
4. **default子句可以省略**
5. **break用于跳出switch**

### 五、与if-else的对比

| 特点 | switch | if-else |
|------|--------|---------|
| 判断条件 | 表达式等于某常量 | 任意布尔条件 |
| 适用场景 | 离散值比较 | 范围或复杂条件 |
| 可读性 | 多分支时更清晰 | 复杂条件时更灵活 |""",
                    "summary": "switch语句用于多分支选择，根据表达式的整数值选择执行相应的case分支",
                    "code_example": """#include <stdio.h>

int main(void) {
    int op;
    double a, b;

    printf("输入两个数：");
    scanf("%lf%lf", &a, &b);

    printf("选择运算：1-加 2-减 3-乘 4-除\\n");
    scanf("%d", &op);

    switch (op) {
        case 1:
            printf("%.2f + %.2f = %.2f\\n", a, b, a + b);
            break;
        case 2:
            printf("%.2f - %.2f = %.2f\\n", a, b, a - b);
            break;
        case 3:
            printf("%.2f * %.2f = %.2f\\n", a, b, a * b);
            break;
        case 4:
            if (b != 0) {
                printf("%.2f / %.2f = %.2f\\n", a, b, a / b);
            } else {
                printf("除数不能为零\\n");
            }
            break;
        default:
            printf("无效选择\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了switch语句实现简单计算器菜单选择",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["if语句", "break语句", "if-else对比"],
                    "tips": ["switch表达式必须是整数", "case常量要互不相同", "不要忘记break"],
                    "common_mistakes": ["忘记break", "case后不是常量", "忘记default"]
                },
                {
                    "name": "switch语句深入",
                    "order_index": 2,
                    "content": """## switch语句深入

### 一、case穿透

如果不加break语句，程序会继续执行后面的case，这就是case穿透。

```c
#include <stdio.h>

int main(void) {
    int score = 85;
    int level = score / 10;

    switch (level) {
        case 10:
        case 9:          // level为10或9都执行这里
            printf("等级：A\\n");
            break;
        case 8:
            printf("等级：B\\n");
            break;
        case 7:
        case 6:
            printf("等级：C\\n");
            break;
        default:
            printf("等级：D\\n");
    }

    return 0;
}
```

### 二、多操作同一处理

利用case穿透，多个case执行同一段代码：

```c
switch (grade) {
    case 'A':
    case 'a':
        printf("优秀\\n");
        break;
    case 'B':
    case 'b':
        printf("良好\\n");
        break;
    case 'C':
    case 'c':
    case 'D':
    case 'd':
        printf("及格\\n");
        break;
    default:
        printf("无效\\n");
}
```

### 三、字符作为case常量

字符本质上就是整数，可以直接作为case常量：

```c
#include <stdio.h>

int main(void) {
    char op;
    double a, b;

    printf("输入两个数：");
    scanf("%lf %c %lf", &a, &op, &b);

    switch (op) {
        case '+':
            printf("%.2f + %.2f = %.2f\\n", a, b, a + b);
            break;
        case '-':
            printf("%.2f - %.2f = %.2f\\n", a, b, a - b);
            break;
        case '*':
            printf("%.2f * %.2f = %.2f\\n", a, b, a * b);
            break;
        case '/':
            if (b != 0) {
                printf("%.2f / %.2f = %.2f\\n", a, b, a / b);
            }
            break;
        default:
            printf("无效运算符\\n");
    }

    return 0;
}
```

### 四、注意事项

1. **break的作用**：退出switch，防止穿透到下一个case
2. **case常量**：必须是整型常量或常量表达式
3. **default位置**：可以放在任意位置，但通常放在最后
4. **多个case同一处理**：利用穿透特性

### 五、常见错误

```c
// 错误1：忘记break（可能是故意的，也可能不是）
switch (day) {
    case 1:
        printf("星期一\\n");  // 忘记break
    case 2:
        printf("星期二\\n");   // 继续执行
        break;
}

// 错误2：case后不能是变量
int a = 1;
switch (x) {
    case a:    // 错误！case后必须是常量
        break;
}

// 错误3：case后不能是范围
switch (score) {
    case 90...100:  // 错误！不能表示范围
        printf("A\\n");
        break;
}
```""",
                    "summary": "switch语句中break用于退出，缺少break会导致case穿透，多个case可执行同一代码",
                    "code_example": """#include <stdio.h>

int main(void) {
    int score = 85;
    int grade = score / 10;

    switch (grade) {
        case 10:
        case 9:
            printf("A（优秀）\\n");
            break;
        case 8:
            printf("B（良好）\\n");
            break;
        case 7:
        case 6:
            printf("C（及格）\\n");
            break;
        default:
            printf("D（不及格）\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了case穿透的用法，多个case执行同一代码",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["switch语句基础", "break语句"],
                    "tips": ["break防止穿透", "善用穿透简化代码", "case后必须是常量"],
                    "common_mistakes": ["忘记break", "case后不是常量表达式", "混淆穿透和错误"]
                },
                {
                    "name": "switch应用实例",
                    "order_index": 3,
                    "content": """## switch应用实例

### 一、计算器菜单

```c
#include <stdio.h>

void calculator(void) {
    double a, b, result;
    char op;
    int valid = 1;

    printf("===== 简单计算器 =====\\n");
    printf("输入格式：a op b（如 3 + 5）\\n");
    scanf("%lf %c %lf", &a, &op, &b);

    switch (op) {
        case '+':
            result = a + b;
            break;
        case '-':
            result = a - b;
            break;
        case '*':
            result = a * b;
            break;
        case '/':
            if (b != 0) {
                result = a / b;
            } else {
                printf("错误：除数不能为零\\n");
                valid = 0;
            }
            break;
        default:
            printf("错误：无效运算符 %c\\n", op);
            valid = 0;
    }

    if (valid) {
        printf("%.2f %c %.2f = %.2f\\n", a, op, b, result);
    }
}

int main(void) {
    calculator();
    return 0;
}
```

### 二、学生成绩管理系统菜单

```c
#include <stdio.h>
#include <string.h>

void show_menu(void) {
    printf("\\n===== 学生成绩管理系统 =====\\n");
    printf("1. 添加学生成绩\\n");
    printf("2. 查看成绩列表\\n");
    printf("3. 查询学生成绩\\n");
    printf("4. 修改学生成绩\\n");
    printf("5. 删除学生成绩\\n");
    printf("0. 退出系统\\n");
    printf("请选择：");
}

int main(void) {
    int choice;

    while (1) {
        show_menu();
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                printf("-> 添加学生成绩功能\\n");
                break;
            case 2:
                printf("-> 查看成绩列表功能\\n");
                break;
            case 3:
                printf("-> 查询学生成绩功能\\n");
                break;
            case 4:
                printf("-> 修改学生成绩功能\\n");
                break;
            case 5:
                printf("-> 删除学生成绩功能\\n");
                break;
            case 0:
                printf("退出系统，再见！\\n");
                return 0;
            default:
                printf("无效选择，请重新输入\\n");
        }
    }

    return 0;
}
```

### 三、日期计算器

```c
#include <stdio.h>

int main(void) {
    int month, days;

    printf("输入月份（1-12）：");
    scanf("%d", &month);

    switch (month) {
        case 1:
        case 3:
        case 5:
        case 7:
        case 8:
        case 10:
        case 12:
            days = 31;
            break;
        case 4:
        case 6:
        case 9:
        case 11:
            days = 30;
            break;
        case 2:
            days = 28;
            break;
        default:
            printf("无效月份\\n");
            return 1;
    }

    printf("%d月有%d天\\n", month, days);

    return 0;
}
```

### 四、使用建议

1. switch适合处理离散的、互斥的选项
2. 菜单驱动程序常用switch
3. 不要忘记default处理无效选项
4. 复杂条件判断仍用if-else""",
                    "summary": "switch常用于菜单驱动程序、日期计算等实际应用场景",
                    "code_example": """#include <stdio.h>

int main(void) {
    int month;
    printf("输入月份（1-12）：");
    scanf("%d", &month);

    switch (month) {
        case 1: case 3: case 5: case 7: case 8: case 10: case 12:
            printf("%d月有31天\\n", month);
            break;
        case 4: case 6: case 9: case 11:
            printf("%d月有30天\\n", month);
            break;
        case 2:
            printf("%d月有28天\\n", month);
            break;
        default:
            printf("无效月份\\n");
    }

    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "演示了用switch判断每月天数，利用case穿透",
                    "difficulty": 1,
                    "importance": 3,
                    "related_points": ["switch语句基础", "switch语句深入"],
                    "tips": ["switch适合离散值选择", "菜单程序常用switch", "不要忘记default"],
                    "common_mistakes": ["忘记default", "break位置错误", "case常量重复"]
                }
            ]
        }
    ]
}


async def generate():
    """生成第2章全部小节知识点"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 查找C语言课程
        result = await db.execute(select(Course).where(Course.code == "C"))
        course = result.scalar_one_or_none()

        if not course:
            print("C语言课程不存在")
            return

        # 查找或创建第2章
        result = await db.execute(
            select(Chapter).where(Chapter.course_id == course.id, Chapter.order_index == 2)
        )
        chapter = result.scalar_one_or_none()

        if not chapter:
            chapter = Chapter(
                course_id=course.id,
                title=CHAPTER_DATA["chapter_title"],
                description=CHAPTER_DATA["chapter_description"],
                order_index=2,
                estimated_minutes=180,
                difficulty_tags=["基础", "选择结构"],
                skill_tags=["if语句", "switch语句", "关系运算", "逻辑运算"]
            )
            db.add(chapter)
            await db.flush()
            print(f"创建章节: {chapter.title}")

        total_kp = 0

        # 创建各小节
        for section_data in CHAPTER_DATA["sections"]:
            # 查找或创建小节
            result = await db.execute(
                select(Section).where(Section.chapter_id == chapter.id, Section.order_index == section_data["order_index"])
            )
            section = result.scalar_one_or_none()

            if not section:
                section = Section(
                    chapter_id=chapter.id,
                    title=section_data["title"],
                    description=section_data["description"],
                    order_index=section_data["order_index"]
                )
                db.add(section)
                await db.flush()

            # 删除现有知识点
            await db.execute(text("DELETE FROM section_knowledge_points WHERE section_id = :sid"), {"sid": section.id})

            # 插入知识点
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
        print(f"\\n第2章生成完成！共{len(CHAPTER_DATA['sections'])}个小节，{total_kp}个知识点")


if __name__ == "__main__":
    asyncio.run(generate())
