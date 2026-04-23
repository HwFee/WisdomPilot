"""Generate Chapter 7: 构造数据类型与应用 - 按教学大纲生成"""
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
    "chapter_title": "构造数据类型与应用",
    "chapter_description": "学习结构体、共用体和枚举类型等构造数据类型",
    "sections": [
        {
            "title": "结构体基础",
            "description": "结构体、结构体指针、结构体与函数、位段等",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "结构体的定义与使用",
                    "order_index": 1,
                    "content": """## 结构体的定义与使用

### 一、为什么需要结构体

数组只能存储相同类型的数据，当需要存储不同类型相关数据时需要结构体：

```c
// 存储学生信息
// 用数组无法同时存储姓名、年龄、成绩
char name[20];
int age;
float score;

// 用结构体可以封装
struct Student {
    char name[20];
    int age;
    float score;
};
```

### 二、结构体的定义

```c
struct 结构体名 {
    成员列表;
};

// 示例
struct Student {
    char name[20];
    int age;
    float score;
};
```

### 三、结构体变量的定义

```c
// 方式1：先定义结构体，再定义变量
struct Student {
    char name[20];
    int age;
    float score;
};
struct Student stu1, stu2;

// 方式2：定义结构体时直接定义变量
struct Student {
    char name[20];
    int age;
    float score;
} stu1, stu2;

// 方式3：使用typedef起别名
typedef struct {
    char name[20];
    int age;
    float score;
} Student;

Student stu1, stu2;  // 更简洁
```

### 四、结构体的内存对齐

```c
struct Example {
    char a;     // 1字节
    int b;      // 4字节
    char c;     // 1字节
};
```

**内存布局（假设4字节对齐）**：
```
偏移0: a (1字节) + 3字节填充
偏移4: b (4字节)
偏移8: c (1字节) + 3字节填充

结构体大小: 12字节
```

### 五、结构体成员的访问

```c
typedef struct {
    char name[20];
    int age;
    float score;
} Student;

// 定义变量
Student stu1;

// 使用点运算符访问成员
strcpy(stu1.name, "Alice");
stu1.age = 20;
stu1.score = 92.5;

// 初始化
Student stu2 = {"Bob", 19, 88.0};
```

### 六、结构体数组

```c
// 结构体数组
Student class[30];

// 初始化
Student class[3] = {
    {"Alice", 20, 92.5},
    {"Bob", 19, 88.0},
    {"Charlie", 21, 95.5}
};

// 访问
printf("%s\\n", class[0].name);
class[1].score = 90.0;
```

### 七、结构体嵌套

```c
struct Date {
    int year;
    int month;
    int day;
};

struct Student {
    char name[20];
    struct Date birthday;  // 嵌套另一个结构体
    float score;
};

struct Student stu = {
    "Alice",
    {2004, 5, 15},  // 嵌套结构体初始化
    92.5
};

printf("%d-%d-%d\\n", stu.birthday.year, stu.birthday.month, stu.birthday.day);
```""",
                    "summary": "结构体是不同类型数据的组合，用struct定义。结构体成员通过点运算符访问，可以嵌套。结构体有内存对齐问题，大小可能大于各成员之和",
                    "code_example": """typedef struct {
    char name[20];
    int age;
    float score;
} Student;

// 定义和初始化
Student stu1 = {"Alice", 20, 92.5};
stu1.score = 95.0;  // 修改成员

// 结构体数组
Student class[3] = {
    {"Alice", 20, 92.5},
    {"Bob", 19, 88.0}
};
printf("%s\\n", class[0].name);

// 嵌套结构体
struct Date { int year, month, day; };
struct Student { char name[20]; struct Date birthday; };
struct Student stu = {"Alice", {2004, 5, 15}};
printf("%d\\n", stu.birthday.year);""",
                    "code_language": "c",
                    "code_explanation": "结构体将不同类型数据组合在一起。stu.score访问成员，嵌套结构体用stu.birthday.year访问",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["结构体指针", "结构体与函数", "位段", "共用体"],
                    "tips": "结构体内存对齐可能造成空间浪费，可以用#pragma pack或重新安排成员顺序优化",
                    "common_mistakes": "1. 混淆结构体定义和变量定义；2. 结构体数组初始化格式错误；3. 嵌套结构体访问路径错误"
                },
                {
                    "name": "结构体指针",
                    "order_index": 2,
                    "content": """## 结构体指针

### 一、为什么使用结构体指针

- 提高效率：大结构体作为参数传递时，复制开销大
- 动态分配：需要动态创建结构体对象
- 链表等数据结构的基础

### 二、结构体指针的定义

```c
typedef struct {
    char name[20];
    int age;
    float score;
} Student;

Student stu = {"Alice", 20, 92.5};
Student *p = &stu;  // 指向stu的指针
```

### 三、通过指针访问成员

```c
// 方式1：使用*运算符（需要括号）
(*p).age = 21;  // 因为.优先级高于*

// 方式2：使用箭头运算符（更常用）
p->age = 21;    // 与上面等价

// 完整示例
printf("姓名: %s\\n", p->name);
printf("年龄: %d\\n", p->age);
printf("成绩: %.1f\\n", p->score);
```

### 四、指针运算符对比

| 运算符 | 含义 | 示例 |
|--------|------|------|
| . | 直接访问成员 | stu.age |
| -> | 通过指针访问成员 | p->age |
| *p.member | 先解引用再访问 | (*p).age |

```c
Student stu = {"Alice", 20, 92.5};
Student *p = &stu;

// 三种方式等价
stu.age == (*p).age == p->age
```

### 五、结构体指针作为函数参数

```c
// 值传递：复制整个结构体
void printStudent(Student s) {
    printf("%s %d %.1f\\n", s.name, s.age, s.score);
}

// 指针传递：只传地址，更高效
void printStudentPtr(Student *p) {
    printf("%s %d %.1f\\n", p->name, p->age, p->score);
}

int main() {
    Student stu = {"Alice", 20, 92.5};
    printStudent(stu);        // 值传递，复制结构体
    printStudentPtr(&stu);   // 指针传递，只传地址
    return 0;
}
```

### 六、修改结构体的函数

```c
// 用指针修改结构体
void updateScore(Student *p, float newScore) {
    p->score = newScore;
}

// 交换两个学生
void swapStudents(Student *a, Student *b) {
    Student temp = *a;  // 复制a指向的结构体
    *a = *b;            // 复制b指向的结构体到a
    *b = temp;          // 复制temp到b
}

int main() {
    Student s1 = {"Alice", 20, 92.5};
    Student s2 = {"Bob", 19, 88.0};

    swapStudents(&s1, &s2);
    printf("%s %s\\n", s1.name, s2.name);  // Bob Alice
    return 0;
}
```

### 七、指向结构体数组的指针

```c
Student class[3] = {
    {"Alice", 20, 92.5},
    {"Bob", 19, 88.0},
    {"Charlie", 21, 95.0}
};

Student *p = class;  // 指向数组第一个元素

// 访问
p[0].score;     // class[0].score
(p + 1)->score; // class[1].score
(p + 2)->name;  // class[2].name

// 遍历
for (Student *p = class; p < class + 3; p++) {
    printf("%s %.1f\\n", p->name, p->score);
}
```""",
                    "summary": "结构体指针通过->访问成员，比值传递更高效。指针可用于修改结构体、动态分配、链表等数据结构",
                    "code_example": """typedef struct {
    char name[20];
    int age;
    float score;
} Student;

Student stu = {"Alice", 20, 92.5};
Student *p = &stu;

// 访问成员
p->age = 21;          // 修改年龄
printf("%s\\n", p->name);  // Alice

// 函数参数传递
void update(Student *p) {
    p->score = 95.0;  // 通过指针修改
}
update(&stu);""",
                    "code_language": "c",
                    "code_explanation": "p->age通过指针访问成员等价于(*p).age。传递结构体指针比复制整个结构体更高效",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["结构体基础", "结构体与函数", "动态分配结构体", "链表"],
                    "tips": "结构体作为函数参数时，如果不需要修改，优先使用const Student *p传递指针更高效",
                    "common_mistakes": "1. 忘记&取地址符；2. 混淆->和.的使用；3. 忘记指针需要初始化"
                },
                {
                    "name": "结构体与函数",
                    "order_index": 3,
                    "content": """## 结构体与函数

### 一、结构体作为函数参数

```c
typedef struct {
    char name[20];
    int age;
    float score;
} Student;

// 1. 值传递：复制整个结构体
void printStudent(Student s) {
    printf("%s %d %.1f\\n", s.name, s.age, s.score);
}

// 2. 指针传递：只传地址
void printStudentPtr(Student *p) {
    printf("%s %d %.1f\\n", p->name, p->age, p->score);
}

// 3. const指针传递：保护数据
void printStudentConst(const Student *p) {
    // p->score = 100;  // 编译错误，不能修改
    printf("%s %d %.1f\\n", p->name, p->age, p->score);
}
```

### 二、返回结构体的函数

```c
// 返回结构体
Student createStudent(const char *name, int age, float score) {
    Student s;
    strncpy(s.name, name, 19);
    s.name[19] = '\\0';
    s.age = age;
    s.score = score;
    return s;  // 返回结构体副本
}

// 返回结构体指针
Student* copyStudent(const Student *src) {
    Student *p = malloc(sizeof(Student));
    if (p) {
        *p = *src;  // 复制整个结构体
    }
    return p;
}

// 返回静态结构体
Student* getDefaultStudent() {
    static Student defaultStu = {"Unknown", 0, 0.0};
    return &defaultStu;
}
```

### 三、结构体作为返回值类型

```c
// 计算两点之间的距离
typedef struct {
    double x;
    double y;
} Point;

double distance(Point p1, Point p2) {
    double dx = p2.x - p1.x;
    double dy = p2.y - p1.y;
    return sqrt(dx * dx + dy * dy);
}

// 返回中点
Point midpoint(Point p1, Point p2) {
    Point mid;
    mid.x = (p1.x + p2.x) / 2;
    mid.y = (p1.y + p2.y) / 2;
    return mid;
}

int main() {
    Point a = {0, 0};
    Point b = {3, 4};
    printf("距离: %.2f\\n", distance(a, b));  // 5.00
    Point c = midpoint(a, b);
    printf("中点: (%.1f, %.1f)\\n", c.x, c.y);  // (1.5, 2.0)
    return 0;
}
```

### 四、函数返回结构体指针的注意事项

```c
// 错误：返回局部变量的指针
Student* createStudentError() {
    Student s;  // 局部变量，在栈上
    return &s;  // 危险！函数结束后s不再有效
}

// 正确：使用malloc分配堆内存
Student* createStudentOK(const char *name, int age) {
    Student *p = malloc(sizeof(Student));
    if (p) {
        strncpy(p->name, name, 19);
        p->age = age;
    }
    return p;  // 调用者需要free
}

// 或返回静态局部变量
Student* getStudent() {
    static Student s = {"Default", 20, 90.0};
    return &s;  // 安全，但数据会被覆盖
}
```

### 五、综合示例：学生管理函数

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef struct {
    char name[20];
    int age;
    float score;
} Student;

// 比较函数（用于排序）
int compareStudent(const void *a, const void *b) {
    Student *s1 = (Student*)a;
    Student *s2 = (Student*)b;
    if (s1->score != s2->score)
        return s2->score > s1->score ? 1 : -1;  // 按分数降序
    return strcmp(s1->name, s2->name);
}

// 打印学生信息
void printStudent(const Student *p) {
    printf("%-15s %3d %6.1f\\n", p->name, p->age, p->score);
}

// 打印所有学生
void printAllStudents(const Student *arr, int n) {
    printf("%-15s %3s %6s\\n", "Name", "Age", "Score");
    printf("--------------------------------\\n");
    for (int i = 0; i < n; i++) {
        printStudent(&arr[i]);
    }
}

int main() {
    Student class[] = {
        {"Alice", 20, 92.5},
        {"Bob", 19, 88.0},
        {"Charlie", 21, 95.0},
        {"Diana", 20, 92.5}
    };
    int n = sizeof(class) / sizeof(class[0]);

    printf("排序前:\\n");
    printAllStudents(class, n);

    qsort(class, n, sizeof(Student), compareStudent);

    printf("\\n排序后（按分数降序）:\\n");
    printAllStudents(class, n);

    return 0;
}
```""",
                    "summary": "结构体可以作为函数参数和返回值。值传递复制结构体，指针传递更高效。返回指针时不能返回局部变量地址",
                    "code_example": """// 值传递
void print(Student s) {
    printf("%s %d\\n", s.name, s.age);
}

// 指针传递（高效）
void update(Student *p) {
    p->score = 95.0;
}

// 返回结构体
Student create(const char *name, int age) {
    Student s;
    strncpy(s.name, name, 19);
    s.age = age;
    return s;  // 返回副本
}

// 比较函数（用于qsort）
int cmp(const void *a, const void *b) {
    return ((Student*)b)->score - ((Student*)a)->score;  // 降序
}""",
                    "code_language": "c",
                    "code_explanation": "结构体值传递会复制整个结构体，指针传递只传地址。qsort需要比较函数返回int",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["结构体基础", "结构体指针", "typedef与结构体", "链表"],
                    "tips": "大结构体作为函数参数时用指针传递更高效，如不需修改加const保护",
                    "common_mistakes": "1. 返回指向局部变量的指针；2. 大结构体用值传递导致性能问题；3. qsort比较函数返回类型错误"
                }
            ]
        },
        {
            "title": "位段与共用体",
            "description": "位段的概念和使用，以及共用体的定义、使用方法，共用体与结构体的区别与联系",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "位段",
                    "order_index": 1,
                    "content": """## 位段

### 一、位段的概念

位段是一种特殊的结构体成员，允许指定成员占用的位数：

```c
struct Flags {
    unsigned int a : 1;  // 占1位
    unsigned int b : 2;  // 占2位
    unsigned int c : 5;  // 占5位
};
```

### 二、位段的定义

```c
struct 结构体名 {
    类型 成员名 : 位数;
};

// 示例：IP头部
struct IPHeader {
    unsigned int version : 4;    // 版本号，4位
    unsigned int headerLen : 4;  // 头部长度，4位
    unsigned int type : 8;       // 服务类型，8位
    unsigned int totalLen : 16;  // 总长度，16位
};
```

### 三、位段的特点

| 特点 | 说明 |
|------|------|
| 只能是整型类型 | int、unsigned int、signed int |
| 位数不能超过类型宽度 | int最多32位 |
| 不能取地址 | &struct.member无效 |
| 跨平台行为可能不同 | 位域的字节顺序不确定 |

### 四、位段的使用

```c
struct Flags {
    unsigned int a : 1;  // 0或1
    unsigned int b : 2;  // 0-3
    unsigned int c : 3;  // 0-7
};

int main() {
    struct Flags f = {0};

    f.a = 1;    // 只能设置0或1
    f.b = 3;    // 只能设置0-3
    f.c = 7;    // 只能设置0-7

    printf("a=%d, b=%d, c=%d\\n", f.a, f.b, f.c);
    printf("结构体大小: %zu\\n", sizeof(struct Flags));
    return 0;
}
```

### 五、位段的内存布局

```c
struct Test {
    unsigned int a : 3;  // 0-7
    unsigned int b : 1;  // 0-1
    unsigned int c : 4;  // 0-15
};

sizeof(struct Test) == sizeof(int) == 4字节
```

### 六、无名位段和填充位段

```c
struct Example {
    unsigned int a : 3;
    unsigned int : 5;     // 无名位段，填充5位不使用
    unsigned int b : 8;
};
```

### 七、位段的应用场景

**1. 网络协议头部**
```c
struct TCPHeader {
    unsigned int srcPort : 16;
    unsigned int dstPort : 16;
    unsigned int seqNum : 32;
    // ...
};
```

**2. 硬件寄存器映射**
```c
struct ControlRegister {
    unsigned int enable : 1;
    unsigned int mode : 2;
    unsigned int data : 12;
    unsigned int : 1;      // 保留位
    unsigned int error : 1;
};
```

**3. 压缩存储**
```c
struct RGB {
    unsigned int r : 8;
    unsigned int g : 8;
    unsigned int b : 8;
    unsigned int a : 8;
};

printf("%zu\\n", sizeof(struct RGB));  // 4字节，而非16字节
```""",
                    "summary": "位段允许指定结构体成员占用的位数，用于紧凑存储和硬件寄存器映射。位段只能是整型，不能取地址",
                    "code_example": """struct Flags {
    unsigned int a : 1;  // 1位：0-1
    unsigned int b : 3;  // 3位：0-7
    unsigned int c : 4;  // 4位：0-15
};

struct Flags f = {0};
f.a = 1;
f.b = 5;
f.c = 12;
printf("%d\\n", sizeof(f));  // 4字节

// 协议头部示例
struct IPHeader {
    unsigned int ver : 4;
    unsigned int hlen : 4;
    unsigned int type : 8;
    unsigned int len : 16;
};""",
                    "code_language": "c",
                    "code_explanation": "位段a占1位只能存0或1，b占3位可存0-7。位段紧凑存储但跨平台可能有差异",
                    "difficulty": 2,
                    "importance": 3,
                    "related_points": ["结构体基础", "共用体", "内存对齐", "位运算"],
                    "tips": "位段用于需要压缩存储或操作特定位的场景，但跨平台使用时要注意字节顺序",
                    "common_mistakes": "1. 位段宽度超过类型宽度；2. 对位段成员取地址；3. 假设位段内存布局跨平台一致"
                },
                {
                    "name": "共用体",
                    "order_index": 2,
                    "content": """## 共用体

### 一、共用体的概念

共用体（Union）是一种特殊的数据类型，所有成员共享同一段内存：

```c
union Data {
    int i;
    float f;
    char c;
};

union Data d;
d.i = 10;      // i占用内存
d.f = 3.14;    // f覆盖i的内存
d.c = 'A';      // c覆盖f的内存
// d现在只保存c的值，i和f的内存被覆盖
```

### 二、共用体与结构体的区别

| 特性 | 结构体 | 共用体 |
|------|--------|--------|
| 内存 | 各成员独立内存 | 所有成员共享同一内存 |
| 大小 | 所有成员大小之和 | 最大成员的大小 |
| 同时性 | 所有成员同时存在 | 同一时间只有一个成员有效 |

### 三、共用体的定义

```c
union 共用体名 {
    成员列表;
};

// 示例
union Data {
    int i;
    float f;
    char str[20];
};
```

### 四、共用体的大小

```c
union Data {
    int i;         // 4字节
    double f;     // 8字节
    char c;       // 1字节
};

printf("%zu\\n", sizeof(union Data));  // 8字节（最大成员）
```

### 五、共用体的使用场景

**1. 节省内存**
```c
// 需要存储整数或浮点数，但不同时存储
union Number {
    int intVal;
    double doubleVal;
};

// 存储布尔值或整数
union Flag {
    unsigned int flags;
    struct {
        unsigned int enabled : 1;
        unsigned int visible : 1;
        unsigned int value : 30;
    } bits;
};
```

**2. 数据类型转换**
```c
union FloatBits {
    float f;
    unsigned int bits;
};

float f = 3.14;
unsigned int bits = *(unsigned int*)&f;  // 直接访问浮点数的位模式
```

**3. 标记联合**
```c
enum Type { TYPE_INT, TYPE_FLOAT, TYPE_STRING };

union Value {
    int i;
    float f;
    char s[20];
};

struct Variant {
    enum Type type;
    union Value value;
};

void printVariant(struct Variant *v) {
    switch (v->type) {
        case TYPE_INT:    printf("%d\\n", v->value.i); break;
        case TYPE_FLOAT:  printf("%.2f\\n", v->value.f); break;
        case TYPE_STRING: printf("%s\\n", v->value.s); break;
    }
}
```

### 六、共用体的初始化

```c
union Data d1 = {10};           // 初始化第一个成员
union Data d2 = {.f = 3.14};   // 指定初始化（C99）

// 初始化列表
union Data d3 = {.c = 'A'};     // 初始化char成员
```

### 七、共用体与结构体结合

```c
struct Student {
    char name[20];
    int age;
    union {
        float gpa;           // 方式1：GPA
        struct {             // 方式2：各科成绩
            float math;
            float english;
            float science;
        } scores;
    } record;
};

int main() {
    struct Student s1 = {"Alice", 20, .record.gpa = 3.8};
    struct Student s2 = {"Bob", 19, .record.scores = {85, 92, 88}};

    printf("%s GPA: %.2f\\n", s1.name, s1.record.gpa);
    printf("%s Math: %.1f\\n", s2.name, s2.record.scores.math);
    return 0;
}
```""",
                    "summary": "共用体所有成员共享同一段内存，大小是最大成员的大小。用于节省内存、数据类型转换、标记联合等场景",
                    "code_example": """union Data {
    int i;
    float f;
    char c;
};

union Data d;
d.i = 10;      // i有效
d.f = 3.14;    // f有效，覆盖i的内存
printf("%d\\n", d.i);  // 错误：f的位模式被解释为int

// 标记联合
enum Type { INT, FLOAT };
struct Variant {
    enum Type type;
    union { int i; float f; };
};
struct Variant v = {FLOAT, .f = 3.14};""",
                    "code_language": "c",
                    "code_explanation": "共用体成员共享内存，赋值给一个成员会覆盖其他成员的值。标记联合用type字段记录当前哪个成员有效",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["结构体基础", "位段", "枚举类型", "内存布局"],
                    "tips": "共用体同一时间只有一个成员有效，通常需要配合类型标记使用",
                    "common_mistakes": "1. 误以为共用体所有成员同时有效；2. 混淆结构体和共用体；3. 忘记使用标记记录当前有效的成员"
                }
            ]
        },
        {
            "title": "枚举类型",
            "description": "枚举类型的定义及使用方法",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "枚举类型",
                    "order_index": 1,
                    "content": """## 枚举类型

### 一、枚举的概念

枚举（Enum）是一种派生数据类型，由命名的整型常量组成：

```c
// 定义枚举类型
enum Weekday {
    SUNDAY,    // 0
    MONDAY,    // 1
    TUESDAY,   // 2
    WEDNESDAY, // 3
    THURSDAY,  // 4
    FRIDAY,    // 5
    SATURDAY   // 6
};
```

### 二、枚举的定义方式

```c
// 方式1：先定义枚举类型，再定义变量
enum Weekday day1, day2;

// 方式2：定义枚举类型时定义变量
enum Weekday {
    SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY
} day1, day2;

// 方式3：使用typedef
typedef enum {
    SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY
} Weekday;

Weekday today = MONDAY;
```

### 三、枚举值的设置

```c
// 默认从0开始
enum Color { RED, GREEN, BLUE };  // 0, 1, 2

// 指定值
enum Level {
    LOW = 1,    // 1
    MEDIUM = 5, // 5
    HIGH = 10   // 10
};

// 部分指定
enum Status {
    PENDING = 100,  // 100
    RUNNING,         // 101
    SUCCESS,         // 102
    FAILED           // 103
};
```

### 四、枚举的使用

```c
enum Weekday { SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY };

void printDay(enum Weekday day) {
    switch (day) {
        case SUNDAY:    printf("Sunday\\n"); break;
        case MONDAY:    printf("Monday\\n"); break;
        case TUESDAY:   printf("Tuesday\\n"); break;
        // ...
    }
}

int main() {
    enum Weekday today = WEDNESDAY;
    printDay(today);  // Wednesday

    // 枚举可以用于数组下标
    const char *dayNames[] = {
        "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    };
    printf("%s\\n", dayNames[today]);  // Wednesday

    return 0;
}
```

### 五、枚举与typedef

```c
// 推荐用法：typedef + 枚举
typedef enum {
    SUCCESS = 0,
    ERROR_INVALID_INPUT = -1,
    ERROR_NOT_FOUND = -2,
    ERROR_PERMISSION = -3
} ErrorCode;

// 使用
ErrorCode err = SUCCESS;
if (err != SUCCESS) {
    printf("发生错误\\n");
}
```

### 六、枚举的优点

1. **提高可读性**：用有意义的名称代替数字
   ```c
   // 差
   if (status == 1)  // 1是什么意思？

   // 好
   enum Status { PENDING, RUNNING, SUCCESS, FAILED };
   if (status == SUCCESS)
   ```

2. **提高可维护性**：修改枚举值只在一处
   ```c
   enum { MAX_STUDENTS = 100 };  // 改为1000很方便
   ```

3. **类型安全**：编译器检查类型
   ```c
   enum Color { RED, GREEN, BLUE };
   enum Size { SMALL, MEDIUM, LARGE };
   enum Color c = RED;
   // c = SMALL;  // 编译警告：类型不匹配
   ```

### 七、枚举的底层实现

```c
enum Weekday { SUNDAY, MONDAY, TUESDAY };
// SUNDAY = 0, MONDAY = 1, TUESDAY = 2

int main() {
    enum Weekday day = MONDAY;
    printf("%d\\n", day);  // 输出1

    // 可以进行数学运算
    day = day + 1;  // day变成TUESDAY
    day++;           // day变成SUNDAY（循环）

    // 可以作为整数用在数组大小等地方
    const char *names[] = {
        [SUNDAY] = "星期天",
        [MONDAY] = "星期一"
    };
    return 0;
}
```""",
                    "summary": "枚举是命名整型常量的集合，从0开始编号，可指定值。用于提高代码可读性和类型安全，可配合switch使用",
                    "code_example": """typedef enum {
    SUCCESS = 0,
    ERROR = -1
} Result;

typedef enum {
    JAN = 1, FEB, MAR, APR, MAY, JUN,
    JUL, AUG, SEP, OCT, NOV, DEC
} Month;

Month m = JAN;
switch (m) {
    case JAN: printf("January\\n"); break;
    case FEB: printf("February\\n"); break;
}

const char *names[] = {"Sun", "Mon", "Tue"};
printf("%s\\n", names[m]);  // January""",
                    "code_language": "c",
                    "code_explanation": "枚举值默认从0开始，可以指定值。枚举可以用作数组下标，switch语句是枚举的经典用法",
                    "difficulty": 1,
                    "importance": 4,
                    "related_points": ["结构体基础", "共用体", "typedef", "switch语句"],
                    "tips": "枚举配合switch语句是常见用法。可以用typedef简化枚举类型定义",
                    "common_mistakes": "1. 枚举值写错或重复；2. 混淆枚举类型；3. 忘记枚举值从0开始"
                }
            ]
        }
    ]
}


async def save_chapter7(db):
    """保存第7章数据到数据库"""

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
        total = await save_chapter7(db)
        if total:
            print(f"\n第7章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
