"""Generate Chapter 1 Section 2: 基本数据类型与变量 - 按教学大纲生成"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.models.section import Section
from app.models.section_knowledge_point import SectionKnowledgePoint
from sqlalchemy import select, text


# 第一章第2节：教学大纲内容
# 1.2 C语言的基本数据类型、标识符、变量和常量、格式化输出函数

SECTION_DATA = {
    "section_title": "基本数据类型与变量",
    "section_description": "C语言的基本数据类型、标识符、变量和常量、格式化输出函数",
    "order_index": 2,
    "estimated_minutes": 25,
    "knowledge_points": [
        {
            "name": "基本数据类型",
            "order_index": 1,
            "content": """## 基本数据类型

C语言的基本数据类型是程序设计的基础，用于定义变量的类型。

### 一、数据类型分类

```
基本数据类型
├── 整型 (int)
│   ├── short (短整型)
│   ├── int (整型)
│   ├── long (长整型)
│   └── long long (双长整型)
├── 字符型 (char)
├── 浮点型
│   ├── float (单精度)
│   └── double (双精度)
└── 枚举类型 (enum)
```

### 二、整型 (int)

**定义**：用于表示整数

**占用空间**：通常4个字节（32位系统）

**取值范围**：-2,147,483,648 ~ 2,147,483,647

**示例**
```c
int age = 20;        // 整型变量
int score = 100;      // 整型变量
int temperature = -10; // 负整数
```

### 三、字符型 (char)

**定义**：用于表示单个字符

**占用空间**：1个字节（8位）

**取值范围**：-128 ~ 127 或 0 ~ 255（无符号）

**字符表示**
```c
char grade = 'A';     // 用单引号括起来
char digit = '5';     // 字符'5'不是数字5
char newline = '\\n'; // 转义字符
```

**ASCII编码**
- 'A' = 65, 'Z' = 90
- 'a' = 97, 'z' = 122
- '0' = 48, '9' = 57

### 四、浮点型

**float（单精度浮点型）**
```c
float height = 175.5f;   // 必须加f或F后缀
float pi = 3.14F;       // F后缀
```
- 占用空间：4个字节
- 精度：约6位有效数字

**double（双精度浮点型）**
```c
double price = 99.99;     // 默认小数是double
double pi = 3.141592653;  // 更精确
```
- 占用空间：8个字节
- 精度：约15位有效数字

### 五、各类型占用空间

| 类型 | 典型占用空间 | 取值范围 | 示例 |
|------|-------------|----------|------|
| int | 4字节 | -2.1B ~ 2.1B | 100, -50 |
| short | 2字节 | -32768 ~ 32767 | 100 |
| long | 4或8字节 | 约±21亿或更大 | 100L |
| char | 1字节 | -128~127 | 'A' |
| float | 4字节 | ±3.4e38 | 3.14f |
| double | 8字节 | ±1.7e308 | 3.14 |

### 六、sizeof运算符

使用sizeof运算符可以查看类型或变量占用的字节数。

```c
#include <stdio.h>

int main(void) {
    printf("int占%zu字节\\n", sizeof(int));
    printf("char占%zu字节\\n", sizeof(char));
    printf("float占%zu字节\\n", sizeof(float));
    printf("double占%zu字节\\n", sizeof(double));

    int a;
    printf("变量a占%zu字节\\n", sizeof(a));

    return 0;
}
```

### 七、注意事项

1. 选择合适的数据类型可以节省内存
2. 浮点常量默认是double类型
3. float变量赋值时建议加f后缀
4. 字符用单引号，字符串用双引号
5. 整数相除结果取整""",
            "summary": "C语言基本数据类型包括整型、字符型、浮点型，每种类型有不同的取值范围和占用空间",
            "code_example": """#include <stdio.h>

int main(void) {
    // 整型
    int age = 20;
    printf("年龄：%d\\n", age);

    // 字符型
    char grade = 'A';
    printf("等级：%c (ASCII: %d)\\n", grade, grade);

    // 浮点型
    float height = 175.5f;
    double pi = 3.141592653;
    printf("身高：%.1f\\n", height);
    printf("圆周率：%.10lf\\n", pi);

    // sizeof
    printf("\\n各类型占用字节数：\\n");
    printf("int占%zu字节\\n", sizeof(int));
    printf("char占%zu字节\\n", sizeof(char));
    printf("float占%zu字节\\n", sizeof(float));
    printf("double占%zu字节\\n", sizeof(double));

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了各种基本数据类型的定义和使用，以及sizeof运算符查看字节大小",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["变量与常量", "标识符", "printf函数"],
            "tips": ["选择合适的数据类型", "浮点常量默认是double类型", "float变量赋值加f后缀"],
            "common_mistakes": ["混淆int和float的区别", "忘记给浮点数字加小数点", "字符和字符串混淆"]
        },
        {
            "name": "标识符命名规则",
            "order_index": 2,
            "content": """## 标识符命名规则

标识符是用来命名变量、函数、数组、类型等的名称。

### 一、标识符的组成

**字符集**
- 字母：a-z, A-Z
- 数字：0-9
- 下划线：_

**命名规则**
1. 必须以字母或下划线开头
2. 不能以数字开头
3. 区分大小写
4. 不能使用关键字

### 二、合法与非法标识符

**合法标识符**
```c
int age;              // 合法
int student_age;      // 合法，以下划线分隔
int _value;           // 合法，以下划线开头
int maxScore;         // 合法，驼峰命名
int MAX;              // 合法，全大写（常量常用）
int _1test;           // 合法，以下划线开头
```

**非法标识符**
```c
int 2name;           // 错误：不能以数字开头
int my-age;           // 错误：不能使用连字符
int my name;          // 错误：不能包含空格
int int;              // 错误：不能使用关键字
int my.name;          // 错误：不能使用点号
```

### 三、C语言关键字（保留字）

关键字是C语言预先定义的，具有特殊含义，不能用作标识符。

| 关键字 | 说明 |
|--------|------|
| int, float, double, char | 数据类型 |
| if, else | 条件语句 |
| for, while, do | 循环语句 |
| switch, case, default | 多分支语句 |
| break, continue | 跳转语句 |
| return | 返回语句 |
| void | 空类型 |
| const | 常变量 |
| struct, union | 结构体/共用体 |
| enum | 枚举 |
| typedef | 类型定义 |
| static | 静态存储 |
| extern | 外部声明 |

### 四、命名建议

**有意义的命名**
```c
// 好命名
int student_age;      // 学生年龄
int total_score;      // 总分
double account_balance; // 账户余额

// 差命名
int a;                // 不知道a代表什么
int x1;               // 不直观
```

**命名风格**
```c
// 变量：使用小写字母，用下划线分隔
int student_age;
int total_score;

// 常量：全大写，用下划线分隔
#define MAX_SIZE 100
const int MIN_VALUE = 0;

// 函数：动词或动词短语
int calculate_sum();
void print_message();

// 自定义类型：帕斯卡命名
typedef struct StudentInfo StudentInfo;
```

### 五、驼峰命名法

**大驼峰（帕斯卡命名）**
```c
int StudentAge;       // 每个单词首字母大写
int TotalScore;       // 用于类型名
```

**小驼峰命名**
```c
int studentAge;       // 第一个单词小写，其余大写
int totalScore;       // 较少使用
```

### 六、注意事项

1. 使用有意义的名称
2. 保持命名风格一致
3. 避免使用单字母（循环变量除外）
4. 不要使用中文命名
5. 变量名不能是关键字""",
            "summary": "标识符由字母、数字、下划线组成，必须以字母或下划线开头，不能使用关键字",
            "code_example": """#include <stdio.h>

// 定义常量（常量全大写）
#define MAX_STUDENTS 100
#define PI 3.14159

int main(void) {
    // 合法的变量命名
    int student_age = 20;        // 学生年龄
    int total_score = 95;        // 总分
    char grade = 'A';            // 等级
    double account_balance = 1000.50; // 账户余额

    // 循环变量常用单字母
    for (int i = 0; i < 3; i++) {
        printf("第%d次循环\\n", i + 1);
    }

    printf("\\n学生信息：\\n");
    printf("年龄：%d岁\\n", student_age);
    printf("总分：%d\\n", total_score);
    printf("等级：%c\\n", grade);
    printf("余额：%.2f元\\n", account_balance);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了合法的标识符命名，包括有意义的变量名和常量名",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["变量与常量", "基本数据类型", "关键字"],
            "tips": ["用有意义的名字命名", "保持命名风格一致", "常量全大写"],
            "common_mistakes": ["使用中文命名", "以数字开头", "包含特殊字符", "使用关键字"]
        },
        {
            "name": "变量与常量",
            "order_index": 3,
            "content": """## 变量与常量

### 一、变量

**定义**：在程序运行过程中可以改变的量

**特点**
- 值可以修改
- 使用前必须先声明
- 占用内存空间

**声明与初始化**
```c
int age;          // 声明，未初始化（值不确定）
age = 20;         // 赋值

int score = 95;   // 声明时初始化

int a, b, c;      // 一次声明多个变量
a = b = c = 0;    // 连续赋值
```

### 二、常量

**定义**：在程序运行过程中不能改变的量

**分类**
1. **字面常量** - 直接写出的值
2. **const常量** - 用const修饰的变量
3. **宏常量** - 用#define定义的常量
4. **枚举常量** - 枚举类型中的常量

### 三、字面常量

```c
int a = 100;           // 整型常量
float b = 3.14f;       // 浮点常量
char c = 'A';          // 字符常量
char s[] = "Hello";    // 字符串常量
```

### 四、const常量

```c
const int MAX_SCORE = 100;   // const常量
const double PI = 3.14159;   // const常量

int main(void) {
    // MAX_SCORE = 200;  // 错误！常量不能修改
    printf("最高分：%d\\n", MAX_SCORE);
    return 0;
}
```

**特点**
- 必须初始化
- 不能修改
- 有类型检查
- 占用内存

### 五、宏常量（#define）

```c
#define PI 3.14159        // 圆周率
#define MAX_SIZE 100       // 最大数量
#define NEWLINE '\\n'      // 换行符

int main(void) {
    int r = 5;
    double area = PI * r * r;
    printf("圆的面积：%.2f%c", area, NEWLINE);
    return 0;
}
```

**特点**
- 没有类型检查
- 预处理时替换
- 不占用内存
- 建议加括号

**带参宏**
```c
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))

int main(void) {
    int m = MAX(10, 20);       // m = 20
    int s = SQUARE(5);         // s = 25
    return 0;
}
```

### 六、变量与常量的区别

| 特性 | 变量 | 常量 |
|------|------|------|
| 值可否改变 | 可以 | 不可以 |
| 定义方式 | 数据类型 变量名 | const/宏定义 |
| 内存占用 | 占用 | 宏常量不占用 |
| 类型检查 | 有 | 宏常量没有 |
| 初始化 | 可选 | const必须 |

### 七、注意事项

1. 常量定义后不能修改
2. const常量占用内存
3. 宏常量不占内存但没类型检查
4. 建议使用const代替宏常量
5. 宏常量建议加括号避免问题""",
            "summary": "变量是可变化的量，常量是不可变化的量，包括字面常量、const常量和宏常量",
            "code_example": """#include <stdio.h>

// 宏常量（没有类型检查，预处理时替换）
#define PI 3.14159
#define MAX_SIZE 100
#define PRINT_MSG printf("Hello\\n")

int main(void) {
    // 变量（可以修改）
    int count = 10;
    printf("count = %d\\n", count);

    count = 20;  // 修改变量
    printf("count = %d\\n", count);

    // const常量（不能修改）
    const int MIN_SIZE = 5;
    const double TAX_RATE = 0.13;

    printf("最小尺寸：%d\\n", MIN_SIZE);
    printf("税率：%.2f%%\\n", TAX_RATE * 100);

    // 宏常量使用
    double radius = 5.0;
    double area = PI * radius * radius;
    printf("圆面积：%.2f\\n", area);

    // 宏函数
    #define MAX(a, b) ((a) > (b) ? (a) : (b))
    #define SQUARE(x) ((x) * (x))

    int m = MAX(10, 20);
    int s = SQUARE(6);
    printf("最大值：%d，平方：%d\\n", m, s);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了变量、const常量和宏常量的使用方式和区别",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["基本数据类型", "标识符", "#define预处理"],
            "tips": ["习惯给常量加const保护", "宏常量注意加括号", "const常量有类型检查"],
            "common_mistakes": ["修改常量的值", "混淆常量和变量的用法", "宏常量忘记加括号"]
        },
        {
            "name": "格式化输出函数printf详解",
            "order_index": 4,
            "content": """## 格式化输出函数printf详解

printf是C语言中最核心的输出函数，需要深入理解。

### 一、函数原型

```c
#include <stdio.h>

int printf(const char *format, ...);
```

- 返回值：输出的字符数
- format：格式控制字符串
- ...：可变参数列表

### 二、格式控制字符串

**组成**
```
%[flags][width][.precision][length]specifier
```

**示例**
```c
printf("%-05d", 42);  // flags=-, width=05, specifier=d
```

### 三、flags（标志）

| 标志 | 含义 |
|------|------|
| - | 左对齐（默认右对齐） |
| + | 显示正负号 |
| 空格 | 正数前留空格 |
| # | 显示进制前缀（0x, 0） |
| 0 | 前导零填充 |

### 四、width（宽度）

```c
printf("%5d", 42);     // 输出：   42（宽度5，右对齐）
printf("%-5d", 42);    // 输出：42   （宽度5，左对齐）
printf("%05d", 42);    // 输出：00042（宽度5，前导零）
```

### 五、precision（精度）

```c
printf("%.2f", 3.14159);    // 输出：3.14（保留2位小数）
printf("%.4f", 3.14);       // 输出：3.1400（补0）
printf("%.2s", "Hello");     // 输出：He（截取前2个字符）
```

### 六、length（长度修饰符）

| 修饰符 | 含义 |
|--------|------|
| hh | char |
| h | short |
| l | long |
| ll | long long |
| L | long double |

```c
printf("%ld", 1234567890L);           // long
printf("%lld", 12345678901234LL);     // long long
printf("%.2Lf", 3.1415926535L);       // long double
```

### 七、specifier（格式说明符）

| 说明符 | 含义 | 示例 |
|--------|------|------|
| d, i | 有符号十进制整数 | printf("%d", -10); |
| u | 无符号十进制整数 | printf("%u", -1); // 输出4294967295 |
| o | 无符号八进制 | printf("%o", 64); // 输出100 |
| x, X | 十六进制 | printf("%x", 255); // 输出ff |
| f, F | 十进制浮点数 | printf("%f", 3.14); |
| e, E | 科学计数法 | printf("%e", 123.4); // 1.234e+02 |
| g, G | 自动选择 | printf("%g", 0.0000123); |
| c | 字符 | printf("%c", 'A'); |
| s | 字符串 | printf("%s", "Hello"); |
| p | 指针地址 | printf("%p", &var); |
| n | 写入字符数 | printf("Hello%n", &count); |

### 八、综合示例

```c
#include <stdio.h>

int main(void) {
    // 基本格式
    printf("%d\\n", 123);           // 123
    printf("%5d\\n", 123);           //   123
    printf("%-5d\\n", 123);          // 123

    // 浮点数
    printf("%.2f\\n", 3.14159);      // 3.14
    printf("%10.2f\\n", 3.14);      //       3.14
    printf("%-10.2f\\n", 3.14);     // 3.14

    // 进制转换
    printf("%d\\n", 255);            // 255
    printf("%o\\n", 255);            // 377
    printf("%x\\n", 255);            // ff
    printf("%X\\n", 255);            // FF

    // 字符串
    printf("%.4s\\n", "Hello");      // Hell

    // 组合
    printf("%05d\\n", 42);           // 00042
    printf("%+d\\n", 42);            // +42
    printf("%#x\\n", 255);           // 0xff

    return 0;
}
```

### 九、注意事项

1. 参数类型必须与格式说明符匹配
2. 参数个数必须与格式说明符个数匹配
3. 浮点数默认精度是6位
4. %s遇到\\0停止
5. 整数不能用%f""",
            "summary": "printf支持丰富的格式说明符，包括宽度、精度、进制转换等高级特性",
            "code_example": """#include <stdio.h>

int main(void) {
    int value = 255;

    // 基本输出
    printf("十进制：%d\\n", value);
    printf("八进制：%o\\n", value);
    printf("十六进制：%x\\n", value);

    // 宽度控制
    printf("%5d\\n", 42);    // 宽度5，右对齐
    printf("%-5d\\n", 42);   // 宽度5，左对齐
    printf("%05d\\n", 42);   // 前导零

    // 浮点数精度
    double pi = 3.1415926535;
    printf("%.2f\\n", pi);    // 3.14
    printf("%.10f\\n", pi);   // 3.1415926535

    // 字符串截取
    printf("%.4s\\n", "HelloWorld");

    // 正负号
    printf("%+d\\n", 42);
    printf("%+d\\n", -42);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了printf的宽度控制、精度控制、进制转换等高级特性",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["基本数据类型", "变量与常量", "转义字符"],
            "tips": ["格式字符串要用双引号", "注意宽度和精度的区别", "整数用%d，浮点数用%f"],
            "common_mistakes": ["忘记%符号", "整数用%f", "精度写错位置"]
        },
        {
            "name": "格式化输入函数scanf详解",
            "order_index": 5,
            "content": """## 格式化输入函数scanf详解

scanf是C语言中用于从标准输入读取数据的函数。

### 一、函数原型

```c
#include <stdio.h>

int scanf(const char *format, ...);
```

- 返回值：成功读取的数据项个数
- format：格式控制字符串
- ...：参数地址列表

### 二、返回值分析

```c
int a, b, c;
int count = scanf("%d%d%d", &a, &b, &c);

// count = 3：成功读取3个
// count = 2：只成功读取2个
// count = 0：一个都没成功
// count = EOF：遇到文件结束
```

### 三、常用格式说明符

| 说明符 | 含义 |
|--------|------|
| %d | 有符号十进制整数 |
| %i | 整数（自动识别进制） |
| %u | 无符号十进制整数 |
| %o | 八进制整数 |
| %x | 十六进制整数 |
| %f | float类型浮点数 |
| %lf | double类型浮点数 |
| %Lf | long double类型浮点数 |
| %c | 单个字符 |
| %s | 字符串（遇空白停止） |
| %[...] | 字符集合 |
| %% | 读入百分号 |

### 四、基本使用

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
    scanf("%s", name);  // 字符数组不用&

    printf("\\n年龄：%d岁\\n", age);
    printf("身高：%.1fcm\\n", height);
    printf("姓名：%s\\n", name);

    return 0;
}
```

### 五、地址运算符 &

**为什么需要&**
- scanf需要知道变量的地址
- &是取地址运算符
- 数组名本身就是地址，不需要&

**正确用法**
```c
int a;
scanf("%d", &a);  // 正确

char s[100];
scanf("%s", s);    // 正确，数组名是地址
```

### 六、跳过空白字符

**默认跳过**
- %d, %f, %s等会自动跳过开头空白
- 空白字符：空格、制表符、换行符

```c
scanf("%d", &a);  // 输入 "  123" 会被正确读取
```

**%c不跳过空白**
```c
char c1, c2;
scanf("%c%c", &c1, &c2);
// 输入 "ab"：c1='a', c2='b'
// 输入 "a b"：c1='a', c2=' '
```

**强制跳过空白**
```c
scanf(" %c", &c);  // 前面加空格，跳过所有空白
```

### 七、分隔符处理

**空格或回车分隔**
```c
scanf("%d%d", &a, &b);
// 可以输入：10 20 或 10<回车>20<回车>
```

**指定分隔符**
```c
scanf("%d,%d", &a, &b);  // 必须用逗号分隔
// 输入：10,20
```

**混合分隔**
```c
scanf("%d+%d", &a, &b);  // 格式中的符号要原样输入
// 输入：10+20
```

### 八、字符集合 %[...]

```c
// 只读取数字
scanf("%[0-9]", str);

// 只读取字母
scanf("%[a-zA-Z]", str);

// 读取字母和数字
scanf("%[a-zA-Z0-9]", str);

// 反向：读取不在集合中的字符
scanf("%[^,]", str);  // 读取逗号之前的所有字符
```

### 九、注意事项

1. 必须使用 & 符号（数组除外）
2. %s遇到空白字符停止
3. %c不跳过空白字符
4. 检查返回值判断输入是否成功
5. 格式字符串中的其他字符需要原样输入""",
            "summary": "scanf是格式化输入函数，需要使用&获取地址，支持多种格式说明符和返回值检查",
            "code_example": """#include <stdio.h>

int main(void) {
    int a, b;
    float f;
    char s[50];

    // 读取整数
    printf("输入两个整数（空格分隔）：");
    if (scanf("%d%d", &a, &b) == 2) {
        printf("a=%d, b=%d\\n", a, b);
    }

    // 读取浮点数
    printf("输入一个浮点数：");
    if (scanf("%f", &f) == 1) {
        printf("f=%.2f\\n", f);
    }

    // 读取字符串（不含空格）
    printf("输入字符串：");
    if (scanf("%s", s) == 1) {
        printf("s=%s\\n", s);
    }

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了scanf函数读取整数、浮点数和字符串的方法",
            "difficulty": 2,
            "importance": 5,
            "related_points": ["printf函数", "基本数据类型", "地址运算符"],
            "tips": ["scanf参数要加&符号", "注意检查返回值", "%s读取到空白字符停止"],
            "common_mistakes": ["忘记&符号", "%s用了&", "忽略返回值检查"]
        },
        {
            "name": "字符与字符串",
            "order_index": 6,
            "content": """## 字符与字符串

### 一、字符型 char

**定义**：用于存储单个字符

**表示方法**
```c
char c1 = 'A';         // 字母
char c2 = '5';         // 数字字符（不是整数5）
char c3 = '\\n';        // 转义字符
char c4 = 65;          // ASCII码（等同于'A'）
```

**字符输入输出**
```c
#include <stdio.h>

int main(void) {
    char c;
    printf("输入一个字符：");
    scanf("%c", &c);  // 注意%c不过滤空白
    printf("字符：%c，ASCII：%d\\n", c, c);
    return 0;
}
```

### 二、ASCII编码

**常用ASCII值**
| 字符 | ASCII | 说明 |
|------|-------|------|
| '0' | 48 | 数字0 |
| 'A' | 65 | 大写字母A |
| 'Z' | 90 | 大写字母Z |
| 'a' | 97 | 小写字母a |
| 'z' | 122 | 小写字母z |
| ' ' | 32 | 空格 |
| '\\n' | 10 | 换行符 |

**字符大小写转换**
```c
char upper = 'A';
char lower = upper + 32;  // 'a'

char c = 'a';
if (c >= 'a' && c <= 'z') {
    c = c - 32;  // 转为大写
}
```

### 三、字符串

**定义**：用双引号括起来的字符序列

**存储方式**
```c
char s1[] = "Hello";    // 自动确定长度
char s2[6] = "Hello";   // 显式指定（包含\\0）
char s3[10] = "Hello";  // 剩余部分自动补0
```

**字符串结束标志 \\0**
- ASCII码为0
- 标记字符串结束位置
- printf、scanf等函数依靠它判断长度

**字符串占用空间**
```c
"Hello"  // 占用6字节：H e l l o \\0
""       // 占用1字节：\\0
```

### 四、字符串输入输出

**%s格式**
```c
char name[20];
scanf("%s", name);      // 读到空白字符停止
printf("%s", name);     // 输出整个字符串
```

**gets函数（不安全，已废弃）**
```c
gets(str);  // 危险！不检查长度，可能溢出
```

**fgets函数（安全）**
```c
fgets(str, sizeof(str), stdin);  // 安全版本
```

### 五、字符串处理函数

**字符串长度 strlen**
```c
#include <string.h>
char s[] = "Hello";
int len = strlen(s);  // len = 5（不含\\0）
```

**字符串复制 strcpy**
```c
char dest[20];
strcpy(dest, "Hello");  // 复制到dest
```

**字符串连接 strcat**
```c
char s1[20] = "Hello";
char s2[] = "World";
strcat(s1, s2);  // s1变成"HelloWorld"
```

**字符串比较 strcmp**
```c
strcmp("abc", "abc");  // 返回0，相等
strcmp("abc", "abd");  // 返回负数，abc<abd
strcmp("ab", "abc");   // 返回负数，ab<abc
```

### 六、注意事项

1. 字符用单引号，字符串用双引号
2. 字符变量占1字节
3. 字符串末尾有\\0结束标志
4. 字符数组要足够大
5. strcpy、strcat不检查长度，可能溢出""",
            "summary": "字符用单引号占1字节，字符串用双引号以\\0结尾，字符数组要足够大",
            "code_example": """#include <stdio.h>
#include <string.h>

int main(void) {
    // 字符
    char c1 = 'A';
    char c2 = 65;  // ASCII码
    printf("c1=%c, c2=%c, ASCII=%d\\n", c1, c2, c1);

    // 字符串
    char s1[] = "Hello";
    char s2[10] = "World";
    printf("s1=%s, s2=%s\\n", s1, s2);

    // 字符串长度（不含\\0）
    printf("strlen(s1)=%zu\\n", strlen(s1));

    // 字符串连接
    strcat(s1, s2);  // HelloWorld
    printf("连接后：%s\\n", s1);

    // 字符串比较
    printf("strcmp(\"abc\",\"abc\")=%d\\n", strcmp("abc","abc"));

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了字符和字符串的区别，字符串处理函数的使用",
            "difficulty": 1,
            "importance": 5,
            "related_points": ["基本数据类型", "字符数组", "字符串函数"],
            "tips": ["字符用单引号，字符串用双引号", "字符串以\\0结尾", "字符数组要足够大"],
            "common_mistakes": ["字符和字符串混淆", "忘记\\0结束标志", "字符串数组长度不够"]
        },
        {
            "name": "类型转换",
            "order_index": 7,
            "content": """## 类型转换

### 一、类型转换的类型

**自动转换（隐式转换）**
- 编译器自动完成
- 通常由低精度向高精度转换

**强制转换（显式转换）**
- 程序员显式指定
- 使用(type)表达式

### 二、自动转换规则

**规则图**
```
char → short → int → long → float → double
         ↑                      ↑
       short ← unsigned ← —— ——↑
```

**整数提升**
```c
char c = 'A';    // char提升为int
int i = c + 32;  // c先转为int再运算
```

**运算中的转换**
```c
int a = 5, b = 2;
float c = a / b;   // 结果是2（整数除法）
float d = a / (float)b;  // 结果是2.5
```

### 三、赋值转换

**赋值时转换**
```c
int i = 3.14;   // i = 3，小数部分截断
double d = 10;  // d = 10.0，整数提升为double
```

**精度提升**
```c
float f = 3.14;    // 3.14是double，转为float
double d = 3.14f;  // 3.14f是float，转为double
```

### 四、强制类型转换

**语法**
```c
(type) expression
```

**示例**
```c
int a = 5, b = 2;
float c = (float)a / b;  // a强转为float，结果2.5
```

### 五、常见问题

**整数除法**
```c
int a = 5, b = 2;
printf("%d / %d = %d\\n", a, b, a / b);   // 2
printf("%d / %d = %.1f\\n", a, b, (float)a / b);  // 2.5
```

**混合运算**
```c
int a = 5, b = 2;
double c = a * 1.0 / b;  // 先转double再运算
```

**溢出问题**
```c
int a = 2000000000;
int b = a + a;  // 溢出，结果不确定
```

### 六、注意事项

1. 整数除法结果取整
2. 小数赋给整数会截断
3. 混合运算时注意类型提升
4. 避免溢出""",
            "summary": "类型转换包括自动转换和强制转换，整数除法会截断，小数赋给整数会丢失精度",
            "code_example": """#include <stdio.h>

int main(void) {
    // 整数除法问题
    int a = 5, b = 2;
    printf("%d / %d = %d\\n", a, b, a / b);           // 2
    printf("%d / %d = %.1f\\n", a, b, (float)a / b);   // 2.5

    // 强制类型转换
    double d = (double)a / b;
    printf("强制转换后：%.1f\\n", d);

    // 混合运算
    int i = 65;
    char c = (char)i;  // int强转为char
    printf("ASCII %d 对应字符：%c\\n", i, c);

    return 0;
}""",
            "code_language": "c",
            "code_explanation": "演示了整数除法和强制类型转换的使用",
            "difficulty": 1,
            "importance": 4,
            "related_points": ["基本数据类型", "变量与常量"],
            "tips": ["整数除法要转float", "小数赋给整数会截断", "注意运算中的类型提升"],
            "common_mistakes": ["整数除法丢失精度", "忘记强制转换", "溢出问题"]
        }
    ]
}


async def generate():
    """生成第1章第2节知识点"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 查找C语言课程和第1章
        result = await db.execute(select(Section).where(Section.order_index == 2, Section.title.like("%数据类型%")))
        section = result.scalar_one_or_none()

        if not section:
            # 尝试另一种方式查找
            from app.models.chapter import Chapter
            from app.models.course import Course
            result = await db.execute(
                select(Section)
                .join(Chapter, Section.chapter_id == Chapter.id)
                .join(Course, Chapter.course_id == Course.id)
                .where(Course.code == "C")
                .where(Chapter.order_index == 1)
                .where(Section.order_index == 2)
            )
            section = result.scalar_one_or_none()

        if not section:
            print("请先运行第1章第1节的生成脚本")
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
        print(f"\\n第1章第2节生成完成！")
        print(f"小节名称: {SECTION_DATA['section_title']}")
        print(f"知识点数量: {len(SECTION_DATA['knowledge_points'])}个")


if __name__ == "__main__":
    asyncio.run(generate())
