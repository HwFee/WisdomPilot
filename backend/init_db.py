"""
一键初始化脚本 - 初始化课程和章节数据
用于新用户克隆项目后快速启动

使用方法：
    cd backend
    python init_db.py
"""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section


# 3门课程数据
COURSES = [
    {"code": "C", "name": "C语言程序设计", "description": "C语言基础语法、指针、内存管理、算法实现", "difficulty_level": 1, "icon": "c-icon"},
    {"code": "CPP", "name": "C++程序设计", "description": "C++面向对象、STL模板库、Modern C++特性", "difficulty_level": 2, "icon": "cpp-icon"},
    {"code": "Python", "name": "Python程序设计", "description": "Python基础语法、数据结构、网络编程、人工智能应用", "difficulty_level": 1, "icon": "python-icon"},
]

# C语言章节（作为示例，其他课程可以后续添加）
C_LANGUAGE_CHAPTERS = [
    {"order_index": 1, "title": "C语言入门", "description": "学习C语言的基本概念，包括变量、数据类型、输入输出等基础知识"},
    {"order_index": 2, "title": "变量与数据类型", "description": "学习C语言中的基本数据类型、变量定义和常量"},
    {"order_index": 3, "title": "运算符与表达式", "description": "学习算术运算符、关系运算符、逻辑运算符及表达式计算"},
    {"order_index": 4, "title": "流程控制", "description": "学习if语句、switch语句、for循环、while循环等流程控制结构"},
    {"order_index": 5, "title": "数组与字符串", "description": "学习一维数组、二维数组、字符数组和字符串处理"},
    {"order_index": 6, "title": "函数", "description": "学习函数的定义、调用、参数传递和递归"},
    {"order_index": 7, "title": "指针基础", "description": "学习指针的概念、指针运算、指针与数组"},
    {"order_index": 8, "title": "指针进阶", "description": "学习指针与函数、指针数组、多级指针"},
    {"order_index": 9, "title": "结构体与联合体", "description": "学习结构体的定义、使用、结构体数组、链表基础"},
    {"order_index": 10, "title": "文件操作", "description": "学习文件的打开、关闭、读写操作"},
]

# C语言第一章"C语言入门"的小节
C_CHAPTER1_SECTIONS = [
    {
        "order_index": 1,
        "title": "程序的基本结构",
        "description": "了解C程序的基本组成部分，包括预处理指令、main函数、语句等",
        "content": """## C程序的基本结构

一个完整的C程序通常包含以下几个部分：

### 1. 预处理指令
```c
#include <stdio.h>
```
这是预处理指令，告诉编译器在编译前包含标准输入输出库。

### 2. main函数
```c
int main() {
    // 程序代码
    return 0;
}
```
main函数是程序的入口点，每个C程序都必须有一个main函数。

### 3. 语句
每条语句以分号(;)结尾，例如：
```c
printf("Hello, World!\\n");
```

### 完整示例
```c
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
```

### 要点总结
- `#include` 用于引入头文件
- `main()` 是程序入口
- 每条语句以 `;` 结尾
- `return 0` 表示程序正常结束
""",
        "estimated_minutes": 15,
        "learning_objectives": ["理解C程序的基本组成", "了解预处理指令的作用", "掌握main函数的基本写法"]
    },
    {
        "order_index": 2,
        "title": "第一个C程序",
        "description": "编写并运行第一个C语言程序，学习printf函数的使用",
        "content": """## 第一个C程序：Hello World

让我们来编写经典的第一个C程序：

```c
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
```

### 程序详解

1. **`#include <stdio.h>`**
   - 包含标准输入输出头文件
   - 使我们可以使用 `printf` 等函数

2. **`int main()`**
   - 定义主函数，返回类型为int
   - 程序从这里开始执行

3. **`printf("Hello, World!\\n");`**
   - 输出字符串到屏幕
   - `\\n` 是换行符

4. **`return 0;`**
   - 返回0表示程序正常结束
   - 非0值通常表示错误

### printf函数

`printf` 是最常用的输出函数：

```c
printf("格式字符串", 参数1, 参数2, ...);
```

常用格式符：
- `%d` - 整数
- `%f` - 浮点数
- `%c` - 字符
- `%s` - 字符串

### 示例

```c
#include <stdio.h>

int main() {
    int age = 18;
    printf("我今年 %d 岁\\n", age);
    return 0;
}
```

### 要点总结
- `printf` 用于输出信息到屏幕
- 使用格式符输出变量的值
- `\\n` 表示换行
""",
        "estimated_minutes": 20,
        "learning_objectives": ["能够编写简单的C程序", "掌握printf函数的基本用法", "理解程序的编译运行过程"]
    },
    {
        "order_index": 3,
        "title": "编译与运行",
        "description": "学习如何使用编译器编译和运行C程序",
        "content": """## 编译与运行C程序

### 什么是编译？

C语言是编译型语言，需要将源代码转换为机器码才能执行：

```
源代码(.c) → 编译器 → 可执行文件 → 运行
```

### 常用编译器

1. **GCC (GNU Compiler Collection)**
   - 最常用的C编译器
   - 跨平台支持

2. **Clang**
   - LLVM项目的一部分
   - 错误提示更友好

3. **MSVC**
   - 微软Visual Studio自带
   - Windows平台常用

### GCC基本用法

```bash
# 编译并生成可执行文件
gcc hello.c -o hello

# 运行程序
./hello        # Linux/macOS
hello          # Windows
```

### 编译过程

1. **预处理**：处理 `#include`、`#define` 等
   ```bash
   gcc -E hello.c -o hello.i
   ```

2. **编译**：转换为汇编代码
   ```bash
   gcc -S hello.i -o hello.s
   ```

3. **汇编**：生成目标文件
   ```bash
   gcc -c hello.s -o hello.o
   ```

4. **链接**：生成可执行文件
   ```bash
   gcc hello.o -o hello
   ```

### 常见编译选项

| 选项 | 说明 |
|------|------|
| `-o filename` | 指定输出文件名 |
| `-Wall` | 显示所有警告 |
| `-g` | 包含调试信息 |
| `-O2` | 优化级别2 |

### 完整示例

```bash
# 编译并显示警告
gcc -Wall hello.c -o hello

# 运行
./hello

# 输出
Hello, World!
```

### 要点总结
- C程序需要编译后才能运行
- GCC是最常用的编译器
- 使用 `-Wall` 查看所有警告
- 分步编译有助于理解程序构建过程
""",
        "estimated_minutes": 15,
        "learning_objectives": ["理解编译的概念和过程", "掌握GCC的基本使用方法", "能够独立编译运行C程序"]
    },
    {
        "order_index": 4,
        "title": "基本输入输出",
        "description": "学习scanf和printf函数，实现基本的输入输出操作",
        "content": """## 基本输入输出

### printf 输出函数

`printf` 用于格式化输出：

```c
int printf(const char *format, ...);
```

#### 常用格式符

| 格式符 | 说明 | 示例 |
|--------|------|------|
| `%d` | 有符号十进制整数 | `printf("%d", 42);` |
| `%f` | 浮点数 | `printf("%f", 3.14);` |
| `%c` | 单个字符 | `printf("%c", 'A');` |
| `%s` | 字符串 | `printf("%s", "Hello");` |
| `%%` | 百分号本身 | `printf("%%");` |

#### 格式控制

```c
// 宽度控制
printf("%5d\\n", 42);     // 输出: "   42"
printf("%-5d\\n", 42);    // 输出: "42   "

// 精度控制
printf("%.2f\\n", 3.14159);  // 输出: "3.14"
printf("%8.2f\\n", 3.14);    // 输出: "    3.14"
```

### scanf 输入函数

`scanf` 用于格式化输入：

```c
int scanf(const char *format, ...);
```

#### 基本用法

```c
#include <stdio.h>

int main() {
    int age;
    printf("请输入你的年龄: ");
    scanf("%d", &age);  // 注意: 使用 & 取地址
    printf("你今年 %d 岁\\n", age);
    return 0;
}
```

#### 重要提示

1. **必须使用 `&` 取地址符**
   ```c
   int num;
   scanf("%d", &num);  // 正确 ✓
   scanf("%d", num);   // 错误 ✗
   ```

2. **字符串不需要 `&`**
   ```c
   char name[50];
   scanf("%s", name);  // 正确，数组名本身就是地址
   ```

3. **scanf 读取字符串遇到空格会停止**
   ```c
   char str[50];
   scanf("%s", str);  // 输入 "Hello World"
                       // str 只得到 "Hello"
   ```

### 综合示例

```c
#include <stdio.h>

int main() {
    char name[50];
    int age;
    float height;

    printf("请输入姓名: ");
    scanf("%s", name);

    printf("请输入年龄: ");
    scanf("%d", &age);

    printf("请输入身高(米): ");
    scanf("%f", &height);

    printf("\\n--- 个人信息 ---\\n");
    printf("姓名: %s\\n", name);
    printf("年龄: %d 岁\\n", age);
    printf("身高: %.2f 米\\n", height);

    return 0;
}
```

### 返回值

- `printf` 返回输出的字符数
- `scanf` 返回成功读取的变量数

```c
int count = printf("Hello\\n");  // count = 6
int read = scanf("%d", &num);    // read = 1 (成功读取1个)
```

### 要点总结
- `printf` 用于格式化输出，`scanf` 用于格式化输入
- `scanf` 需要使用 `&` 取地址（字符串除外）
- 格式符控制输出的格式和精度
- 注意 `scanf` 读取字符串时会以空格分隔
""",
        "estimated_minutes": 25,
        "learning_objectives": ["熟练使用printf进行格式化输出", "掌握scanf进行用户输入", "理解格式符的用法", "注意scanf的地址符使用"]
    },
]


async def init_all_data():
    """初始化所有数据"""
    print("Starting database initialization...")

    # 初始化数据库表结构
    await init_db()
    print("Database tables initialized")

    async with AsyncSessionLocal() as db:
        # 1. 初始化课程
        print("\nInitializing courses...")
        for course_data in COURSES:
            result = await db.execute(select(Course).where(Course.code == course_data["code"]))
            existing = result.scalar_one_or_none()
            if not existing:
                course = Course(**course_data)
                db.add(course)
                print(f"   + {course_data['code']}: {course_data['name']}")
            else:
                print(f"   = {course_data['code']}: already exists")

        await db.commit()

        # 2. 初始化C语言章节
        print("\nInitializing C language chapters...")
        c_course = (await db.execute(select(Course).where(Course.code == "C"))).scalar_one_or_none()
        if c_course:
            for chapter_data in C_LANGUAGE_CHAPTERS:
                result = await db.execute(
                    select(Chapter).where(Chapter.course_id == c_course.id, Chapter.order_index == chapter_data["order_index"])
                )
                existing_chapter = result.scalar_one_or_none()

                if not existing_chapter:
                    chapter = Chapter(
                        course_id=c_course.id,
                        order_index=chapter_data["order_index"],
                        title=chapter_data["title"],
                        description=chapter_data["description"],
                    )
                    db.add(chapter)
                    print(f"   + {chapter_data['title']}")
                else:
                    print(f"   = {chapter_data['title']}: already exists")

        await db.commit()

        # 3. 初始化C语言第一章的小节
        print("\nInitializing C language chapter 1 sections...")
        c_course = (await db.execute(select(Course).where(Course.code == "C"))).scalar_one_or_none()
        if c_course:
            # 获取第一章
            chapter1 = (await db.execute(
                select(Chapter).where(Chapter.course_id == c_course.id, Chapter.order_index == 1)
            )).scalar_one_or_none()

            if chapter1:
                for section_data in C_CHAPTER1_SECTIONS:
                    result = await db.execute(
                        select(Section).where(
                            Section.chapter_id == chapter1.id,
                            Section.order_index == section_data["order_index"]
                        )
                    )
                    existing_section = result.scalar_one_or_none()

                    if not existing_section:
                        section = Section(
                            chapter_id=chapter1.id,
                            order_index=section_data["order_index"],
                            title=section_data["title"],
                            description=section_data["description"],
                            content=section_data.get("content"),
                            estimated_minutes=section_data.get("estimated_minutes", 15),
                            learning_objectives=section_data.get("learning_objectives"),
                        )
                        db.add(section)
                        print(f"   + {section_data['title']}")
                    else:
                        print(f"   = {section_data['title']}: already exists")

        await db.commit()

        # 4. 统计数据
        courses_count = (await db.execute(select(Course))).scalars().all().__len__()
        chapters_count = (await db.execute(select(Chapter))).scalars().all().__len__()
        sections_count = (await db.execute(select(Section))).scalars().all().__len__()

        print("\n" + "="*50)
        print("Initialization complete!")
        print(f"   Courses: {courses_count}")
        print(f"   Chapters: {chapters_count}")
        print(f"   Sections: {sections_count}")
        print("="*50)
        print("\nTo start the backend server:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    asyncio.run(init_all_data())
