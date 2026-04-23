"""Generate Chapter 5: 相同数据类型集合 - 按教学大纲生成"""
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
    "chapter_title": "相同数据类型集合",
    "chapter_description": "学习C语言的数组与字符串，包括一维数组、二维数组、字符数组、字符串处理函数",
    "sections": [
        {
            "title": "数组的基本概念",
            "description": "数组与数组元素的概念",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "数组的基本概念与定义",
                    "order_index": 1,
                    "content": """## 数组的基本概念与定义

### 一、为什么需要数组

当需要存储大量相同类型的数据时，使用多个变量非常不便：

```c
// 存储100个学生的成绩
int score1, score2, score3, ..., score100;  // 太麻烦了！

// 使用数组
int scores[100];  // 一个数组保存100个整数
```

### 二、数组的定义

```c
类型说明符 数组名[常量表达式];

// 示例
int grades[10];      // 10个整数的数组
float prices[5];     // 5个浮点数的数组
char name[20];       // 20个字符的数组
```

### 三、数组的组成

```
int arr[5];

内存布局：
┌─────┬─────┬─────┬─────┬─────┐
│ arr[0] │ arr[1] │ arr[2] │ arr[3] │ arr[4] │
└─────┴─────┴─────┴─────┴─────┘
  ↓       ↓       ↓       ↓       ↓
 地址连续存放
```

### 四、数组元素

- **下标（索引）**：从0开始，最大为 元素个数-1
- **数组名**：代表数组首元素的地址（常量指针）
- **数组大小**：必须是常量表达式，不能是变量

### 五、数组的内存特点

1. **连续性**：数组元素在内存中连续存放
2. **同类型**：所有元素类型相同
3. **随机访问**：可通过下标直接访问任意元素
4. **固定大小**：数组大小在定义时确定，运行期间不能改变

### 六、数组定义示例

```c
// 各种类型的数组
int numbers[10];          // 整型数组
float temperatures[365];   // 浮点型数组
char letters[52];         // 字符型数组
double data[1000];        // 双精度数组

// 定义时初始化
int arr[5] = {1, 2, 3, 4, 5};      // 完全初始化
int arr2[5] = {1, 2};               // 部分初始化，其余为0
int arr3[] = {1, 2, 3, 4, 5};      // 自动确定大小为5
```""",
                    "summary": "数组是相同类型元素的集合，用连续内存存储。数组定义格式为 类型 数组名[大小]，下标从0开始，数组大小必须是常量",
                    "code_example": """// 数组定义与基本操作
int scores[5] = {85, 92, 78, 96, 88};

int main() {
    // 访问数组元素
    printf("第一个成绩：%d\\n", scores[0]);  // 85
    printf("第三个成绩：%d\\n", scores[2]);  // 78

    // 遍历数组
    for (int i = 0; i < 5; i++) {
        printf("%d ", scores[i]);
    }
    printf("\\n");

    // 修改数组元素
    scores[0] = 90;
    printf("修改后第一个成绩：%d\\n", scores[0]);
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "数组scores包含5个整数，scores[i]访问第i+1个元素（因为下标从0开始）。数组在内存中连续存放",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["一维数组", "二维数组", "数组初始化", "数组作为函数参数"],
                    "tips": "数组下标从0开始，最后一个元素下标是 数组长度-1。定义数组时大小必须是常量，不能是变量",
                    "common_mistakes": "1. 数组下标越界，如访问scores[5]（数组只有5个元素，下标0-4）；2. 混淆数组长度和下标范围；3. 定义数组时用变量作为大小"
                },
                {
                    "name": "数组的存储与内存模型",
                    "order_index": 2,
                    "content": """## 数组的存储与内存模型

### 一、数组的内存分配

```c
int arr[3];
```

**内存布局：**
```
假设arr地址为2000：
地址：  2000    2004    2008
      ┌──────┬──────┬──────┐
      │arr[0]│arr[1]│arr[2]│
      └──────┴──────┴──────┘
每个int占4个字节（假设int=4字节）
```

### 二、数组名作为地址

```c
int arr[5] = {10, 20, 30, 40, 50};

int main() {
    printf("arr = %p\\n", arr);           // 数组首地址
    printf("&arr[0] = %p\\n", &arr[0]);  // 第一个元素地址
    printf("arr + 1 = %p\\n", arr + 1);   // 第二个元素地址
    printf("&arr[1] = %p\\n", &arr[1]);   // 第二个元素地址
    // arr和&arr[0]的值相同
    return 0;
}
```

### 三、指针算术与数组

```c
int arr[5] = {10, 20, 30, 40, 50};

int main() {
    int *p = arr;  // p指向arr[0]

    // 指针算术
    printf("*p = %d\\n", *p);      // 10，p指向arr[0]
    printf("*(p+1) = %d\\n", *(p+1)); // 20，p+1指向arr[1]
    printf("*(p+2) = %d\\n", *(p+2)); // 30，p+2指向arr[2]

    // 指针遍历数组
    for (int i = 0; i < 5; i++) {
        printf("%d ", *(p + i));  // 等价于arr[i]
    }
    printf("\\n");
    return 0;
}
```

### 四、数组名与指针的区别

| 特性 | 数组名 | 指针变量 |
|------|--------|----------|
| 类型 | 常量指针 | 变量 |
| 赋值 | 不能赋值给指针变量 | 可以指向其他地址 |
| 运算 | 数组名 + n 表示第n个元素地址 | 指针可以加减 |
| sizeof | sizeof(数组名) 得到整个数组大小 | sizeof(指针) 得到指针大小 |
| &操作 | &数组名 得到数组指针 | &指针 得到指针的地址 |

```c
int arr[5];
int *p = arr;

printf("sizeof(arr) = %zu\\n", sizeof(arr));  // 5 * sizeof(int) = 20
printf("sizeof(p) = %zu\\n", sizeof(p));      // 指针大小 = 8（64位系统）
```

### 五、数组下标越界问题

```c
int arr[3] = {1, 2, 3};

int main() {
    // 合法访问
    printf("%d\\n", arr[0]);  // OK
    printf("%d\\n", arr[2]);  // OK

    // 越界访问（危险！）
    printf("%d\\n", arr[3]);  // 未定义行为！可能输出任意值
    printf("%d\\n", arr[100]); // 更危险！可能崩溃

    return 0;
}
```

**越界后果：**
- 可能读取到任意垃圾值
- 可能修改其他变量（栈破坏）
- 可能导致程序崩溃
- 编译器不会检查越界

### 六、多维数组的存储

```c
int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
```

**内存布局（按行存储）：**
```
┌────┬────┬────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │
└────┴────┴────┴────┴────┴────┘
matrix[0]          matrix[1]
```

### 七、变长数组（C99）

C99支持使用变量定义数组大小：

```c
int n = 10;
int arr[n];  // 变长数组，n可以是变量

int main() {
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }
    return 0;
}
```

**注意**：变长数组不能在定义时初始化""",
                    "summary": "数组在内存中连续存放，数组名是常量指针指向首元素。数组下标越界是常见错误，变长数组C99支持用变量定义大小",
                    "code_example": """// 数组存储与指针算术
int arr[5] = {10, 20, 30, 40, 50};
int *p = arr;

printf("sizeof(arr) = %zu\\n", sizeof(arr));  // 20（5*4字节）
printf("sizeof(p) = %zu\\n", sizeof(p));      // 8（64位指针）

// 指针遍历
for (int i = 0; i < 5; i++) {
    printf("%d ", *(p + i));  // 等价于arr[i]
}

// 下标越界危险
printf("%d\\n", arr[10]);  // 危险！数组只有5个元素""",
                    "code_language": "c",
                    "code_explanation": "数组名arr作为指针指向首元素，指针算术p+i等价于&arr[i]。sizeof(arr)是整个数组大小，sizeof(p)是指针大小",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["一维数组", "指针基础", "数组与函数", "二维数组"],
                    "tips": "数组下标越界是C语言最常见的错误之一，因为编译器不检查。务必确保下标在0到n-1范围内",
                    "common_mistakes": "1. 数组下标越界；2. 混淆数组名和指针；3. 用sizeof(数组名)计算元素个数；4. 变长数组在定义时初始化"
                }
            ]
        },
        {
            "title": "一维数组详解",
            "description": "一维数组的存储形式、定义、初始化及使用方法",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "一维数组的初始化",
                    "order_index": 1,
                    "content": """## 一维数组的初始化

### 一、初始化的方式

**1. 定义时完全初始化**
```c
int arr[5] = {1, 2, 3, 4, 5};
// arr[0]=1, arr[1]=2, arr[2]=3, arr[3]=4, arr[4]=5
```

**2. 定义时部分初始化**
```c
int arr[5] = {1, 2};
// arr[0]=1, arr[1]=2, arr[2]=0, arr[3]=0, arr[4]=0
// 未初始化的元素自动为0
```

**3. 定义时全部不初始化**
```c
int arr[5];
// arr[0]=?, arr[1]=?, arr[2]=?, arr[3]=?, arr[4]=?
// 局部数组初始值为垃圾值，全局数组自动初始化为0
```

**4. 省略数组大小**
```c
int arr[] = {1, 2, 3, 4, 5};
// 编译器自动计算大小为5
```

**5. 静态数组初始化**
```c
void func() {
    static int arr[5];  // 静态数组，自动初始化为0
    // arr[0]=0, arr[1]=0, arr[2]=0, arr[3]=0, arr[4]=0
}
```

### 二、不同存储类别的初始化差异

```c
int global_arr[5];          // 全局数组，自动初始化为0
static int static_arr[5];  // 静态数组，自动初始化为0

int main() {
    int local_arr[5];       // 局部数组，初始值为垃圾值
    static int static_local[5];  // 静态局部数组，初始化为0
    return 0;
}
```

### 三、初始化规则详解

```c
// 1. 初始化列表元素个数 <= 数组大小
int a[5] = {1, 2};           // OK, a = {1, 2, 0, 0, 0}

// 2. 初始化列表元素个数 > 数组大小（错误）
// int b[3] = {1, 2, 3, 4, 5};  // 错误！

// 3. 初始化列表可以指定下标
int c[5] = {[0] = 1, [4] = 5};  // C99特性，c = {1, 0, 0, 0, 5}

// 4. 字符数组的特殊初始化
char str1[] = {'H', 'e', 'l', 'l', 'o', '\\0'};  // 手动加结束符
char str2[] = "Hello";                            // 自动加结束符
char str3[6] = "Hello";                          // 完全匹配
```

### 四、C99指定初始化器

```c
// 使用指定初始化器（C99）
int arr[10] = {[0] = 1, [5] = 5, [9] = 9};
// arr = {1, 0, 0, 0, 0, 5, 0, 0, 0, 9}

// 可以初始化范围
int arr2[10] = {[0 ... 4] = 1, [5 ... 9] = 2};
// arr2 = {1, 1, 1, 1, 1, 2, 2, 2, 2, 2}
```

### 五、数组初始化的应用

```c
// 1. 求和初始化
int sum = 0;
int arr[] = {10, 20, 30, 40, 50};
int n = sizeof(arr) / sizeof(arr[0]);

for (int i = 0; i < n; i++) {
    sum += arr[i];
}
printf("总和 = %d\\n", sum);

// 2. 初始化为相同值
int arr2[5];
for (int i = 0; i < 5; i++) {
    arr2[i] = 0;  // 或使用 memset(arr2, 0, sizeof(arr2))
}

// 3. 初始化为序列
int arr3[10];
for (int i = 0; i < 10; i++) {
    arr3[i] = i + 1;  // 1, 2, 3, ..., 10
}
```""",
                    "summary": "一维数组初始化方式：完全初始化、部分初始化（其余为0）、不初始化（局部为垃圾值）、省略大小初始化。静态和全局数组自动初始化为0",
                    "code_example": """// 数组初始化示例
int a[5] = {1, 2};           // a = {1, 2, 0, 0, 0}
int b[] = {1, 2, 3};         // b大小自动为3
char str[] = "Hello";         // 包含'\\0'，大小为6

// 全局数组自动初始化
int global[5];  // 全为0

int main() {
    // 局部数组是垃圾值
    int local[5];  // 垃圾值
    static int static_arr[5];  // 全为0

    // 计算数组大小
    int arr[] = {1, 2, 3, 4, 5};
    int n = sizeof(arr) / sizeof(arr[0]);  // n = 5
    printf("数组大小：%d\\n", n);
    return 0;
}""",
                    "code_language": "c",
                    "code_explanation": "部分初始化的数组其余元素自动为0。计算数组元素个数用 sizeof(arr)/sizeof(arr[0])",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["一维数组基本操作", "数组与函数", "字符数组", "数组的存储模型"],
                    "tips": "局部数组不会自动初始化为0，可能包含垃圾值。静态数组和全局数组自动初始化为0",
                    "common_mistakes": "1. 误以为局部数组会自动初始化为0；2. 初始化列表元素个数大于数组大小；3. 忘记字符数组要加结束符"
                },
                {
                    "name": "一维数组的基本操作",
                    "order_index": 2,
                    "content": """## 一维数组的基本操作

### 一、数组的遍历

```c
// 方法1：下标遍历
int arr[] = {10, 20, 30, 40, 50};
int n = sizeof(arr) / sizeof(arr[0]);

for (int i = 0; i < n; i++) {
    printf("%d ", arr[i]);
}
printf("\\n");

// 方法2：指针遍历
for (int *p = arr; p < arr + n; p++) {
    printf("%d ", *p);
}
printf("\\n");

// 方法3：指针算术
for (int *p = arr, *end = arr + n; p < end; p++) {
    printf("%d ", *p);
}
```

### 二、数组的查找

**1. 顺序查找**
```c
int search(int arr[], int n, int key) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == key) {
            return i;  // 找到返回下标
        }
    }
    return -1;  // 未找到返回-1
}
```

**2. 二分查找（适用于有序数组）**
```c
int binarySearch(int arr[], int n, int key) {
    int left = 0, right = n - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;  // 防止溢出

        if (arr[mid] == key) {
            return mid;  // 找到
        } else if (arr[mid] < key) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;  // 未找到
}
```

### 三、数组的插入与删除

**1. 插入元素**
```c
// 在指定位置插入元素
int insert(int arr[], int n, int pos, int value) {
    if (pos < 0 || pos > n || n >= 100) {
        return -1;  // 位置无效或数组满
    }

    // 从后向前移动元素
    for (int i = n - 1; i >= pos; i--) {
        arr[i + 1] = arr[i];
    }
    arr[pos] = value;
    return n + 1;  // 返回新长度
}
```

**2. 删除元素**
```c
// 删除指定位置的元素
int delete(int arr[], int n, int pos) {
    if (pos < 0 || pos >= n) {
        return -1;  // 位置无效
    }

    // 从前向后移动元素
    for (int i = pos; i < n - 1; i++) {
        arr[i] = arr[i + 1];
    }
    return n - 1;  // 返回新长度
}
```

### 四、数组的反转

```c
// 方法1：交换
void reverse(int arr[], int n) {
    for (int i = 0, j = n - 1; i < j; i++, j--) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

// 方法2：指针
void reverse_ptr(int arr[], int n) {
    int *left = arr;
    int *right = arr + n - 1;
    while (left < right) {
        int temp = *left;
        *left++ = *right;
        *right-- = temp;
    }
}
```

### 五、数组的排序

**冒泡排序**
```c
void bubbleSort(int arr[], int n) {
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
```

**选择排序**
```c
void selectionSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int minIdx = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j;
            }
        }
        if (minIdx != i) {
            int temp = arr[i];
            arr[i] = arr[minIdx];
            arr[minIdx] = temp;
        }
    }
}
```

### 六、综合示例

```c
#include <stdio.h>

#define MAX 100

int main() {
    int arr[MAX] = {64, 25, 12, 22, 11};
    int n = 5;

    printf("原数组：");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\\n");

    // 排序
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }

    printf("排序后：");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\\n");

    // 二分查找
    int key = 25;
    int left = 0, right = n - 1;
    int found = -1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == key) {
            found = mid;
            break;
        } else if (arr[mid] < key) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    printf("%d在数组中的位置：%d\\n", key, found);

    return 0;
}
```""",
                    "summary": "一维数组基本操作包括遍历、查找（顺序/二分）、插入、删除、反转、排序。插入删除需要移动元素，排序常用冒泡和选择排序",
                    "code_example": """// 冒泡排序
int arr[] = {64, 34, 25, 12, 22};
int n = 5;

for (int i = 0; i < n - 1; i++) {
    for (int j = 0; j < n - 1 - i; j++) {
        if (arr[j] > arr[j + 1]) {
            int temp = arr[j];
            arr[j] = arr[j + 1];
            arr[j + 1] = temp;
        }
    }
}

// 二分查找（数组必须有序）
int binarySearch(int arr[], int n, int key) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == key) return mid;
        else if (arr[mid] < key) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}""",
                    "code_language": "c",
                    "code_explanation": "冒泡排序每轮将最大元素'冒泡'到最后。二分查找时间复杂度O(log n)但要求数组有序",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["数组初始化", "数组与函数", "二分查找", "排序算法"],
                    "tips": "插入删除操作要防止数组越界。二分查找前必须确保数组有序",
                    "common_mistakes": "1. 二分查找用于无序数组；2. 插入删除时移动元素方向错误；3. 排序算法边界条件错误"
                },
                {
                    "name": "一维数组与函数",
                    "order_index": 3,
                    "content": """## 一维数组与函数

### 一、数组作为函数参数

数组传递给函数时，退化为指针：

```c
// 函数声明
void printArray(int arr[], int n);
void printArray(int *arr, int n);  // 等价声明

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    printArray(arr, 5);  // arr退化为指针
    return 0;
}

void printArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
}
```

### 二、数组参数的特殊性

```c
void modifyArray(int arr[], int n) {
    arr[0] = 100;  // 直接修改原数组！
}

int main() {
    int arr[] = {1, 2, 3};
    modifyArray(arr, 3);
    printf("%d\\n", arr[0]);  // 输出100
    return 0;
}
```

**关键点**：
- 数组传递给函数不是值传递，而是地址传递
- 函数内部可以修改原数组
- 函数无法知道数组的真实大小，需要额外参数

### 三、计算数组大小的陷阱

```c
void wrongSize(int arr[]) {
    int n = sizeof(arr) / sizeof(arr[0]);  // 错误！
    // 在函数内，arr是指针，sizeof(arr)是指针大小
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int n = sizeof(arr) / sizeof(arr[0]);  // 正确，5
    return 0;
}
```

### 四、返回数组的函数

**1. 通过指针返回数组**
```c
int* createArray(int size) {
    int *arr = malloc(size * sizeof(int));
    for (int i = 0; i < size; i++) {
        arr[i] = i;
    }
    return arr;  // 返回指针
}

int main() {
    int *p = createArray(10);
    printf("%d\\n", p[5]);  // 5
    free(p);  // 记得释放内存
    return 0;
}
```

**2. 静态局部数组**
```c
int* getStaticArray() {
    static int arr[] = {1, 2, 3};  // 静态数组
    return arr;  // 安全，不会被销毁
}
```

### 五、数组函数综合示例

```c
#include <stdio.h>
#include <malloc.h>

// 数组作为输入参数
int sumArray(int arr[], int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
}

// 修改数组
void doubleArray(int arr[], int n) {
    for (int i = 0; i < n; i++) {
        arr[i] *= 2;
    }
}

// 复制数组
void copyArray(int dest[], int src[], int n) {
    for (int i = 0; i < n; i++) {
        dest[i] = src[i];
    }
}

// 动态数组
int* createArray(int size) {
    int *arr = malloc(size * sizeof(int));
    if (arr == NULL) {
        return NULL;  // 分配失败
    }
    for (int i = 0; i < size; i++) {
        arr[i] = i + 1;
    }
    return arr;
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int n = sizeof(arr) / sizeof(arr[0]);

    printf("和：%d\\n", sumArray(arr, n));  // 15

    doubleArray(arr, n);
    printf("翻倍：");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);  // 2 4 6 8 10
    }
    printf("\\n");

    // 动态数组
    int *dynamic = createArray(5);
    if (dynamic) {
        printf("动态数组：");
        for (int i = 0; i < 5; i++) {
            printf("%d ", dynamic[i]);
        }
        free(dynamic);  // 释放内存
    }
    printf("\\n");

    return 0;
}
```

### 六、const保护数组参数

```c
// 告诉调用者函数不会修改数组
void printArray(const int arr[], int n) {
    // arr[0] = 100;  // 编译错误！
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
}
```""",
                    "summary": "数组传递给函数时退化为指针，函数可以修改原数组。函数内无法用sizeof计算数组大小。动态数组需malloc分配、free释放，const可保护数组不被修改",
                    "code_example": """// 数组参数是地址传递
void modify(int arr[], int n) {
    arr[0] = 100;  // 修改原数组
}

int main() {
    int a[] = {1, 2, 3};
    modify(a, 3);
    printf("%d\\n", a[0]);  // 100
    return 0;
}

// 动态数组
int *create(int size) {
    int *p = malloc(size * sizeof(int));
    return p;  // 记得free
}""",
                    "code_language": "c",
                    "code_explanation": "数组参数arr[]在函数内退化为指针，修改arr[0]就是修改原数组。动态分配的内存在堆上，需要手动释放",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["一维数组基本操作", "指针基础", "动态内存分配", "数组初始化"],
                    "tips": "数组参数传递给函数时不会复制数据，会退化为指针。如果函数不需修改数组，用const保护",
                    "common_mistakes": "1. 在函数内用sizeof计算数组大小；2. malloc后忘记free；3. 返回指向栈内存的指针"
                }
            ]
        },
        {
            "title": "二维数组详解",
            "description": "二维数组的存储形式、定义、初始化及使用方法",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "二维数组的定义与初始化",
                    "order_index": 1,
                    "content": """## 二维数组的定义与初始化

### 一、二维数组的定义

```c
类型说明符 数组名[行数][列数];

// 示例
int matrix[3][4];   // 3行4列的整数矩阵
float table[5][3]; // 5行3列的浮点数表
```

### 二、二维数组的内存布局

```c
int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
```

**按行存储（行优先）**：
```
┌────┬────┬────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │
└────┴────┴────┴────┴────┴────┘
matrix[0]          matrix[1]
整个二维数组在内存中是连续的一维数组
```

### 三、二维数组的初始化

**1. 完全初始化**
```c
int a[2][3] = {
    {1, 2, 3},
    {4, 5, 6}
};
// 或紧凑形式
int a[2][3] = {1, 2, 3, 4, 5, 6};
```

**2. 部分初始化**
```c
int b[2][3] = {{1, 2}, {4}};
// b[0] = {1, 2, 0}
// b[1] = {4, 0, 0}

int c[2][3] = {1, 2, 3};  // 只初始化第一行
// c[0] = {1, 2, 3}
// c[1] = {0, 0, 0}
```

**3. 省略第一维大小**
```c
int d[][3] = {
    {1, 2, 3},
    {4, 5, 6}
};  // 编译器自动计算第一维为2
```

**4. 初始化为特殊值**
```c
// 初始化为全0
int e[3][4] = {0};  // 所有元素初始化为0

// 初始化为全1（需要逐个赋值）
int f[3][4];
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
        f[i][j] = 1;
    }
}
```

### 四、二维数组与一维数组的关系

```c
int matrix[2][3] = {1, 2, 3, 4, 5, 6};

int main() {
    // matrix[i][j] 等价于 *(*(matrix + i) + j)
    printf("%d\\n", matrix[0][2]);      // 3
    printf("%d\\n", *(matrix[0] + 2));  // 3
    printf("%d\\n", *(*(matrix + 0) + 2));  // 3

    // matrix[i] 是第i行的首地址（指针）
    // matrix[i] + j 是第i行第j列元素的地址
    // *(matrix[i] + j) 是第i行第j列元素的值

    // matrix是二维数组的地址，matrix + i是第i行的地址
    printf("matrix = %p\\n", matrix);
    printf("matrix + 1 = %p\\n", matrix + 1);  // 跳过一整行
    return 0;
}
```

### 五、二维数组的指针理解

```c
int matrix[2][3];

// matrix是指向数组的指针类型：int (*)[3]
int (*p)[3] = matrix;  // p指向包含3个int的数组

// 访问元素
p[0][0]   // 等价于 matrix[0][0]
p[1][2]   // 等价于 matrix[1][2]

// p + i 指向第i行
// *(p + i) 指向第i行首元素，类型为 int*
```

### 六、二维数组作为函数参数

```c
// 声明时必须指定第二维大小
void printMatrix(int matrix[][3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}

// 也可以用指针声明
void printMatrix2(int (*matrix)[3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}

int main() {
    int mat[2][3] = {{1, 2, 3}, {4, 5, 6}};
    printMatrix(mat, 2);
    return 0;
}
```""",
                    "summary": "二维数组按行连续存储，可以理解为数组的数组。初始化可以用{{}}分组或一维展开。第二维大小必须在函数参数中指定",
                    "code_example": """// 二维数组初始化
int a[2][3] = {{1, 2, 3}, {4, 5, 6}};
// 或 int a[2][3] = {1, 2, 3, 4, 5, 6};
// a[0] = {1, 2, 3}, a[1] = {4, 5, 6}

// 省略第一维
int b[][3] = {{1, 2, 3}, {4, 5, 6}};  // 自动计算为2

// 函数参数第二维必须指定
void print(int matrix[][3], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\\n");
    }
}""",
                    "code_language": "c",
                    "code_explanation": "二维数组{{1,2,3},{4,5,6}}按行存储，matrix[i][j]访问第i行第j列元素。函数参数matrix[][3]第二维3必须指定",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["一维数组", "二维数组操作", "指针与数组", "矩阵运算"],
                    "tips": "二维数组作为函数参数时，第二维的大小必须明确指定，因为编译器需要知道如何计算matrix[i][j]的地址",
                    "common_mistakes": "1. 函数参数第二维不指定；2. 混淆行列下标；3. 初始化时{}嵌套不正确"
                },
                {
                    "name": "二维数组的应用",
                    "order_index": 2,
                    "content": """## 二维数组的应用

### 一、矩阵的基本操作

```c
// 矩阵加法
void addMatrix(int a[][3], int b[][3], int c[][3], int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            c[i][j] = a[i][j] + b[i][j];
        }
    }
}

// 矩阵转置
void transpose(int a[][3], int at[][2], int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            at[j][i] = a[i][j];
        }
    }
}
```

### 二、矩阵乘法

```c
// 矩阵乘法：A(m×k) × B(k×n) = C(m×n)
void matrixMultiply(int A[][3], int B[][2], int C[][2],
                   int m, int k, int n) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            C[i][j] = 0;
            for (int t = 0; t < k; t++) {
                C[i][j] += A[i][t] * B[t][j];
            }
        }
    }
}
```

### 三、行列操作

```c
// 求每行最大元素
void rowMax(int matrix[][4], int rows) {
    for (int i = 0; i < rows; i++) {
        int max = matrix[i][0];
        for (int j = 1; j < 4; j++) {
            if (matrix[i][j] > max) {
                max = matrix[i][j];
            }
        }
        printf("第%d行最大：%d\\n", i, max);
    }
}

// 求每列和
void colSum(int matrix[][3], int rows) {
    for (int j = 0; j < 3; j++) {
        int sum = 0;
        for (int i = 0; i < rows; i++) {
            sum += matrix[i][j];
        }
        printf("第%d列和：%d\\n", j, sum);
    }
}

// 鞍点（行最大列最小的元素）
void saddlePoint(int matrix[][3], int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        // 找第i行最大元素及其列位置
        int maxCol = 0;
        for (int j = 1; j < cols; j++) {
            if (matrix[i][j] > matrix[i][maxCol]) {
                maxCol = j;
            }
        }
        // 检查是否是该列最小
        int isSaddle = 1;
        for (int k = 0; k < rows; k++) {
            if (matrix[k][maxCol] < matrix[i][maxCol]) {
                isSaddle = 0;
                break;
            }
        }
        if (isSaddle) {
            printf("鞍点：matrix[%d][%d] = %d\\n", i, maxCol, matrix[i][maxCol]);
        }
    }
}
```

### 四、杨辉三角

```c
// 打印杨辉三角
void yanghui(int n) {
    int tri[20][20];  // 假设不超过20行

    for (int i = 0; i < n; i++) {
        for (int j = 0; j <= i; j++) {
            if (j == 0 || j == i) {
                tri[i][j] = 1;  // 首尾为1
            } else {
                tri[i][j] = tri[i-1][j-1] + tri[i-1][j];
            }
            printf("%d ", tri[i][j]);
        }
        printf("\\n");
    }
}
```

### 五、综合示例：学生成绩表

```c
#include <stdio.h>

#define STUDENTS 3
#define COURSES 4

int main() {
    // 存储3个学生4门课的成绩
    int scores[STUDENTS][COURSES] = {
        {85, 92, 78, 96},
        {72, 88, 95, 80},
        {90, 76, 88, 92}
    };

    // 计算每个学生的平均分
    printf("每个学生的平均分：\\n");
    for (int i = 0; i < STUDENTS; i++) {
        int sum = 0;
        for (int j = 0; j < COURSES; j++) {
            sum += scores[i][j];
        }
        printf("学生%d：%.2f\\n", i + 1, (double)sum / COURSES);
    }

    // 计算每门课的平均分
    printf("\\n每门课的平均分：\\n");
    for (int j = 0; j < COURSES; j++) {
        int sum = 0;
        for (int i = 0; i < STUDENTS; i++) {
            sum += scores[i][j];
        }
        printf("课程%d：%.2f\\n", j + 1, (double)sum / STUDENTS);
    }

    // 找最高分学生和课程
    int maxScore = scores[0][0];
    int maxI = 0, maxJ = 0;
    for (int i = 0; i < STUDENTS; i++) {
        for (int j = 0; j < COURSES; j++) {
            if (scores[i][j] > maxScore) {
                maxScore = scores[i][j];
                maxI = i;
                maxJ = j;
            }
        }
    }
    printf("\\n最高分：学生%d的课程%d，成绩%d\\n", maxI + 1, maxJ + 1, maxScore);

    return 0;
}
```""",
                    "summary": "二维数组用于矩阵表示和操作：矩阵加法、转置、乘法、求行列和、鞍点查找等。也用于表格数据如学生成绩表",
                    "code_example": """// 矩阵转置
int A[2][3] = {{1, 2, 3}, {4, 5, 6}};
int AT[3][2];

for (int i = 0; i < 2; i++) {
    for (int j = 0; j < 3; j++) {
        AT[j][i] = A[i][j];
    }
}

// 杨辉三角
int tri[6][6];
for (int i = 0; i < 6; i++) {
    for (int j = 0; j <= i; j++) {
        if (j == 0 || j == i) tri[i][j] = 1;
        else tri[i][j] = tri[i-1][j-1] + tri[i-1][j];
        printf("%d ", tri[i][j]);
    }
    printf("\\n");
}""",
                    "code_language": "c",
                    "code_explanation": "矩阵转置将A[i][j]存到AT[j][i]。杨辉三角性质：首尾为1，其他位置等于肩上两数之和",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["二维数组定义", "一维数组应用", "指针与数组", "排序查找"],
                    "tips": "二维数组用于表格或矩阵数据时，注意行列下标的含义。嵌套循环中外层控制行，内层控制列",
                    "common_mistakes": "1. 混淆行列下标导致数据访问错误；2. 矩阵乘法维度不匹配；3. 循环边界错误导致越界"
                }
            ]
        },
        {
            "title": "字符数组与字符串",
            "description": "字符类型的数组、字符串的概念、字符串与字符类型的区别与联系、字符串处理函数",
            "order_index": 4,
            "knowledge_points": [
                {
                    "name": "字符数组与字符串基础",
                    "order_index": 1,
                    "content": """## 字符数组与字符串基础

### 一、字符数组

```c
// 定义字符数组
char str[6];

// 逐个字符初始化
char str1[6] = {'H', 'e', 'l', 'l', 'o', '\\0'};

// 用字符串常量初始化
char str2[] = "Hello";  // 自动添加'\\0'

// 指定大小
char str3[10] = "Hello";  // 'H','e','l','l','o','\\0',后三位为0
```

### 二、字符数组的内存布局

```
char str[] = "Hello";

内存：
┌────┬────┬────┬────┬────┬────┐
│ 'H'│ 'e'│ 'l'│ 'l'│ 'o'│ '\\0'│
└────┴────┴────┴────┴────┴────┘
索引：  0    1    2    3    4    5
```

### 三、字符串结束标志 '\\0'

**重要**：C语言字符串以 '\\0'（ASCII码0）结尾

```c
// 如果没有'\\0'，就不是标准字符串
char str1[] = {'H', 'e', 'l', 'l', 'o'};  // 不是字符串，是字符数组
char str2[] = {'H', 'e', 'l', 'l', 'o', '\\0'};  // 是字符串

// 字符串常量自动包含'\\0'
char *p = "Hello";  // 实际存储：'H','e','l','l','o','\\0'
```

### 四、字符串与字符数组的区别

| 特性 | 字符数组 | 字符串常量指针 |
|------|----------|----------------|
| 定义 | char s[10] = "abc"; | char *s = "abc"; |
| 内存位置 | 栈/全局区 | 文字常量区（只读） |
| 可修改性 | 可以修改 | 不能修改（未定义） |
| 大小确定 | 编译时确定 | 运行时确定 |
| sizeof | 数组大小 | 指针大小 |

```c
// 字符数组 - 可以修改
char s1[] = "Hello";
s1[0] = 'h';  // OK

// 字符串常量 - 不要修改
char *s2 = "Hello";
s2[0] = 'h';  // 危险！未定义行为
```

### 五、字符数组的输入输出

```c
char name[50];

// 使用scanf输入字符串（遇到空格停止）
printf("输入姓名：");
scanf("%s", name);  // 不用&，数组名就是地址
printf("Hello, %s!\\n", name);

// 使用gets（不安全，已废弃）
gets(name);  // 可能缓冲区溢出

// 使用fgets（安全，推荐）
fgets(name, sizeof(name), stdin);  // 最多读取sizeof(name)-1个字符
name[strcspn(name, "\\n")] = '\\0';  // 去掉换行符
```

### 六、字符数组的遍历

```c
char str[] = "Hello";

int main() {
    // 方法1：下标遍历
    for (int i = 0; str[i] != '\\0'; i++) {
        putchar(str[i]);
    }

    // 方法2：指针遍历
    for (char *p = str; *p != '\\0'; p++) {
        putchar(*p);
    }

    // 方法3：用strlen（需要string.h）
    for (int i = 0; i < strlen(str); i++) {
        putchar(str[i]);
    }
}
```""",
                    "summary": "字符串是以'\\0'结尾的字符数组。字符数组用单引号逐个初始化，字符串常量用双引号自动加'\\0'。字符串常量指针不可修改，字符数组可以",
                    "code_example": """// 字符数组定义
char s1[] = "Hello";                    // 6个字节（含\\0）
char s2[] = {'H', 'e', 'l', 'l', 'o', '\\0'};  // 等价
char s3[10] = "Hello";                   // 前6个有效

// 字符串常量指针
char *p = "Hello";  // 指向常量区，不要修改*p

// 安全输入
char name[100];
fgets(name, sizeof(name), stdin);
name[strcspn(name, "\\n")] = '\\0';  // 去掉换行符""",
                    "code_language": "c",
                    "code_explanation": "char s1[] = \"Hello\" 自动添加结束符\\0。char *p = \"Hello\" 指向只读常量区，不能通过p修改字符串",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["字符串处理函数", "字符数组与字符串", "指针与字符串", "输入输出函数"],
                    "tips": "字符串常量指针指向只读内存，不要试图修改它。用fgets代替gets防止缓冲区溢出",
                    "common_mistakes": "1. 忘记字符串结束符'\\0'；2. 修改字符串常量指针指向的内容；3. 字符数组大小计算错误"
                },
                {
                    "name": "字符串处理函数",
                    "order_index": 2,
                    "content": """## 字符串处理函数

C语言标准库 <string.h> 提供了丰富的字符串处理函数。

### 一、strlen - 字符串长度

```c
#include <string.h>

size_t strlen(const char *s);

// 返回字符串长度（不含结束符\\0）
char str[] = "Hello";
printf("%zu\\n", strlen(str));  // 5
```

### 二、strcpy / strncpy - 字符串复制

```c
// strcpy - 完全复制（不安全）
char dest[20];
strcpy(dest, "Hello");  // 复制到dest

// strncpy - 限制复制长度（安全）
char dest[20];
strncpy(dest, "Hello World", sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\\0';  // 确保结束符

// 错误：目标缓冲区太小
// char small[3];
// strcpy(small, "Hello");  // 缓冲区溢出！
```

### 三、strcat / strncat - 字符串连接

```c
char str1[20] = "Hello";
char str2[] = " World";

// strcat - 连接两个字符串
strcat(str1, str2);  // str1变成"Hello World"

// strncat - 限制连接长度
char str3[20] = "Hello";
strncat(str3, str2, 3);  // "Hello Wo"（最多3个字符）
```

### 四、strcmp / strncmp - 字符串比较

```c
// strcmp - 比较两个字符串
// 返回值：0表示相等，<0表示s1<s2，>0表示s1>s2
char s1[] = "apple";
char s2[] = "banana";

if (strcmp(s1, s2) == 0) {
    printf("相等\\n");
} else {
    printf("不相等\\n");
}

// strncmp - 比较前n个字符
strncmp(s1, s2, 3);  // 只比较前3个字符
```

### 五、sprintf / sscanf - 字符串格式化

```c
// sprintf - 格式化写入字符串
char buf[100];
int age = 25;
float gpa = 3.8;
sprintf(buf, "Name: %s, Age: %d, GPA: %.2f", "Tom", age, gpa);
printf("%s\\n", buf);

// sscanf - 从字符串格式化读取
char info[] = "25 3.8";
int a;
float g;
sscanf(info, "%d %f", &a, &g);
printf("%d %.2f\\n", a, g);
```

### 六、字符串转换函数

```c
#include <stdlib.h>

// 字符串转整数
int i = atoi("123");        // "123" -> 123
int i2 = atoi("-456");      // "-456" -> -456

// 字符串转长整数
long l = atol("123456");

// 字符串转浮点数
double d = atof("3.14");

// 更安全的转换（带错误检查）
int i = strtol("123", NULL, 10);   // 基数为10
double d = strtod("3.14", NULL);
```

### 七、综合示例

```c
#include <stdio.h>
#include <string.h>

int main() {
    char s1[100] = "Hello";
    char s2[] = "World";
    char s3[100];

    // 复制
    strcpy(s3, s1);
    printf("复制：%s\\n", s3);

    // 连接
    strcat(s1, " ");
    strcat(s1, s2);
    printf("连接：%s\\n", s1);

    // 比较
    printf("比较：%d\\n", strcmp("apple", "banana"));  // 负数

    // 长度
    printf("长度：%zu\\n", strlen("Hello"));

    // 格式化
    char buf[100];
    sprintf(buf, "%s-%d", "Test", 123);
    printf("格式化：%s\\n", buf);

    // 转换
    printf("转换：%d, %.2f\\n", atoi("100"), atof("3.14"));

    return 0;
}
```""",
                    "summary": "字符串处理函数包括：strlen(长度)、strcpy/strncpy(复制)、strcat/strncat(连接)、strcmp/strncmp(比较)、sprintf/sscanf(格式化)、atoi/atof(转换)",
                    "code_example": """#include <string.h>

char s1[100] = "Hello", s2[] = "World";

// 复制
strcpy(s1, s2);  // s1变成"World"

// 连接
strcat(s1, "!");  // s1变成"World!"

// 比较（字典序）
strcmp("apple", "banana");  // < 0

// 长度（不含\\0）
strlen("Hello");  // 5

// 安全复制
strncpy(dest, src, n - 1);
dest[n - 1] = '\\0';""",
                    "code_language": "c",
                    "code_explanation": "strcpy不安全可能溢出，用strncpy更安全。strcmp按ASCII码比较字符。strlen返回字符串长度不含结束符",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["字符数组基础", "字符串输入输出", "字符分类函数", "atoi/itoa"],
                    "tips": "使用strcpy/strcat前确保目标缓冲区够大。优先使用strncpy/strncat。strcmp返回0表示相等",
                    "common_mistakes": "1. strcpy目标缓冲区太小导致溢出；2. strcmp比较结果误用；3. strlen返回长度含结束符"
                },
                {
                    "name": "字符串深入应用",
                    "order_index": 3,
                    "content": """## 字符串深入应用

### 一、字符串数组

```c
// 字符串数组 - 每个元素都是字符串
char names[][20] = {
    "Alice",
    "Bob",
    "Charlie"
};

// 访问
printf("%s\\n", names[0]);  // Alice
printf("%c\\n", names[1][0]);  // B

// 遍历
int n = sizeof(names) / sizeof(names[0]);
for (int i = 0; i < n; i++) {
    printf("%s\\n", names[i]);
}
```

### 二、命令行参数

```c
int main(int argc, char *argv[]) {
    // argc: 参数个数（程序名算第1个）
    // argv: 参数数组
    // argv[0] 是程序名
    // argv[1] 是第一个参数

    printf("程序名：%s\\n", argv[0]);
    for (int i = 1; i < argc; i++) {
        printf("参数%d：%s\\n", i, argv[i]);
    }
    return 0;
}
```

### 三、字符串查找与替换

```c
// 查找子串
char *strstr(const char *haystack, const char *needle);
char text[] = "Hello World";
char *p = strstr(text, "World");  // 找到返回指针
if (p) {
    printf("找到：%s\\n", p);  // "World"
}

// 简单替换（原地）
void replaceChar(char *str, char old, char new) {
    for (int i = 0; str[i] != '\\0'; i++) {
        if (str[i] == old) {
            str[i] = new;
        }
    }
}
```

### 四、字符串分割

```c
#include <string.h>

// 用strtok分割字符串
char str[] = "apple,banana,cherry";
const char delim[] = ",";
char *token;

token = strtok(str, delim);  // 第一次调用
while (token != NULL) {
    printf("%s\\n", token);
    token = strtok(NULL, delim);  // 后续调用用NULL
}

// 输出：
// apple
// banana
// cherry
```

### 五、字符分类函数

```c
#include <ctype.h>

char c = '5';

// 判断字符类型
isalpha(c);   // 是否字母
isdigit(c);   // 是否数字
isalnum(c);   // 是否字母或数字
isspace(c);   // 是否空白字符
isupper(c);   // 是否大写
islower(c);   // 是否小写

// 字符转换
toupper('a');  // 'A'
tolower('A');  // 'a'

// 应用：字符串转大写
void toUpperStr(char *str) {
    for (int i = 0; str[i] != '\\0'; i++) {
        str[i] = toupper(str[i]);
    }
}
```

### 六、综合示例：字符串处理工具箱

```c
#include <stdio.h>
#include <string.h>
#include <ctype.h>

// 统计各类字符
void countChars(const char *str) {
    int letters = 0, digits = 0, spaces = 0, others = 0;
    for (int i = 0; str[i] != '\\0'; i++) {
        if (isalpha(str[i])) letters++;
        else if (isdigit(str[i])) digits++;
        else if (isspace(str[i])) spaces++;
        else others++;
    }
    printf("字母:%d 数字:%d 空格:%d 其他:%d\\n",
           letters, digits, spaces, others);
}

// 反转字符串
void reverseString(char *str) {
    int len = strlen(str);
    for (int i = 0, j = len - 1; i < j; i++, j--) {
        char temp = str[i];
        str[i] = str[j];
        str[j] = temp;
    }
}

// 判断回文
int isPalindrome(const char *str) {
    int len = strlen(str);
    for (int i = 0, j = len - 1; i < j; i++, j--) {
        if (str[i] != str[j]) {
            return 0;
        }
    }
    return 1;
}

int main() {
    char text[100];
    fgets(text, sizeof(text), stdin);
    text[strcspn(text, "\\n")] = '\\0';

    countChars(text);

    reverseString(text);
    printf("反转：%s\\n", text);

    printf("回文：%s\\n", isPalindrome(text) ? "是" : "否");

    return 0;
}
```""",
                    "summary": "字符串深入应用包括：字符串数组、命令行参数、子串查找(strstr)、字符串分割(strtok)、字符分类(ctype.h)。综合可用于字符统计、回文判断等",
                    "code_example": """// 字符串分割
char str[] = "apple,banana,cherry";
char *token = strtok(str, ",");
while (token) {
    printf("%s\\n", token);
    token = strtok(NULL, ",");
}

// 子串查找
char *p = strstr("Hello World", "World");  // 返回指针

// 字符分类
if (isdigit(c)) printf("是数字\\n");
if (isalpha(c)) printf("是字母\\n");
c = toupper(c);  // 转大写""",
                    "code_language": "c",
                    "code_explanation": "strtok第一次用原字符串调用，后续用NULL继续分割。strstr返回找到的子串指针，未找到返回NULL",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["字符串处理函数", "字符数组基础", "指针与字符串", "命令行参数"],
                    "tips": "strtok会修改原字符串，不适合用于常量字符串。字符分类函数需要ctype.h头文件",
                    "common_mistakes": "1. strtok第二次还用原字符串而非NULL；2. 忽略字符串被修改；3. 字符分类函数参数溢出"
                }
            ]
        },
        {
            "title": "指针与字符串",
            "description": "指针变量、字符串指针变量与字符串的关系",
            "order_index": 5,
            "knowledge_points": [
                {
                    "name": "指针与字符串的关系",
                    "order_index": 1,
                    "content": """## 指针与字符串的关系

### 一、字符串的两种表示方式

```c
// 方式1：字符数组
char str1[] = "Hello";
// str1是数组名，是常量指针，指向' H'

// 方式2：字符指针
char *str2 = "Hello";
// str2是指针变量，指向字符串常量"Hello"
```

### 二、两种方式的区别

| 特性 | char str[] | char *str |
|------|------------|-----------|
| 存储位置 | 栈/全局区 | 栈（指针）+ 常量区（字符串） |
| 大小 | 固定（编译时确定） | 指针大小（8字节） |
| 可修改 | 可以 | 不可以（未定义） |
| 初始化 | 定义时必须 | 可以后赋值 |

```c
char s1[] = "Hello";
char *s2 = "Hello";

s1[0] = 'h';  // OK
s2[0] = 'h';  // 危险！可能崩溃（常量区只读）
```

### 三、指针操作字符串

```c
char *p = "Hello World";

int main() {
    // 指针遍历
    while (*p != '\\0') {
        putchar(*p);
        p++;
    }
    printf("\\n");

    // 指针算术
    printf("%c\\n", *(p + 6));  // 'W'

    // 指向字符串中间
    char *p2 = p + 6;  // 指向"World"
    printf("%s\\n", p2);  // "World"
    return 0;
}
```

### 四、字符串数组与指针数组

```c
// 字符串数组 - 每个字符串是独立数组
char names[3][20] = {"Alice", "Bob", "Charlie"};
names[0][0] = 'a';  // 可以修改

// 指针数组 - 每个元素是指向字符串的指针
char *names2[] = {"Alice", "Bob", "Charlie"};
// names2[i]指向常量区的字符串，不能修改

// 指针数组更节省空间（指针大小 vs 固定数组大小）
```

### 五、const与字符串指针

```c
// const指针 - 不能通过指针修改字符串
const char *p = "Hello";  // 推荐写法
// p[0] = 'h';  // 编译错误

// 指针const - 指针本身不能改变
char *const p2 = "Hello";
// p2 = "World";  // 编译错误

// 两者都不能修改
const char *const p3 = "Hello";  // 都不能修改
```

### 六、字符串作为函数参数

```c
// 字符串参数退化为指针
int stringLength(const char *s) {
    int len = 0;
    while (s[len] != '\\0') {
        len++;
    }
    return len;
}

// 更简洁的写法
int stringLength(const char *s) {
    const char *p = s;
    while (*p != '\\0') {
        p++;
    }
    return p - s;
}
```

### 七、返回字符串的函数

```c
// 返回静态字符串
const char* getMessage() {
    return "Hello";  // 返回字符串常量
}

// 使用static在函数内创建字符串
const char* getDate() {
    static char date[20];
    sprintf(date, "2026-04-21");
    return date;  // 返回静态数组，不会被销毁
}

// 错误：返回局部变量地址
const char* getError() {
    char msg[] = "Error";  // 局部数组，函数结束销毁
    return msg;  // 危险！返回后访问未定义
}
```""",
                    "summary": "字符串可用字符数组或字符指针表示。字符指针指向字符串常量（只读），字符数组内容可修改。字符串参数退化为指针，const保护字符串不被修改",
                    "code_example": """// 字符数组 vs 字符指针
char s1[] = "Hello";   // 可修改
char *s2 = "Hello";    // 不可修改

// 指针遍历
const char *p = "Hello";
while (*p) putchar(*p++);

// 指针数组（字符串数组）
const char *days[] = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};

// 返回字符串
const char* greet() {
    return "Hello";  // 返回字符串常量
}""",
                    "code_language": "c",
                    "code_explanation": "char s1[]在栈上创建可修改，char *s2指向只读常量区。指针遍历字符串时遇到\\0结束",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["字符数组", "字符串处理函数", "指针基础", "函数返回指针"],
                    "tips": "不确定能否修改时，用const char *。返回字符串的函数要避免返回局部变量",
                    "common_mistakes": "1. 通过char *指针修改字符串常量；2. 返回局部字符串数组；3. 混淆字符数组和字符指针"
                },
                {
                    "name": "指针数组与字符串数组",
                    "order_index": 2,
                    "content": """## 指针数组与字符串数组

### 一、指针数组的概念

```c
// 指针数组 - 数组元素是指针
char *names[3];  // 3个char*元素的数组

// 每个元素都是指针
names[0] = "Alice";
names[1] = "Bob";
names[2] = "Charlie";
```

### 二、字符串数组的两种方式

```c
// 方式1：二维字符数组
char grid[3][20] = {"Alice", "Bob", "Charlie"};
// grid[i]是char[20]，是数组不是指针

// 方式2：指针数组
const char *ptrs[3] = {"Alice", "Bob", "Charlie"};
// ptrs[i]是char*，是指向字符串常量的指针
```

### 三、两种方式的对比

| 特性 | char name[N][M] | const char *name[] |
|------|-----------------|-------------------|
| 内存占用 | M×N字节 | 指针数组+N×字符串长度 |
| 字符串可修改 | 可以 | 不能 |
| 初始化大小 | 固定 | 灵活 |
| 访问方式 | name[i][j] | name[i][j] |

```c
// 二维数组可以修改
char names[3][20] = {"Alice", "Bob"};
names[0][0] = 'a';  // OK

// 指针数组不能修改
const char *names2[3] = {"Alice", "Bob"};
names2[0][0] = 'a';  // 未定义行为！
```

### 四、指针数组的典型应用

**1. 命令行参数**
```c
int main(int argc, char *argv[]) {
    // argv是指针数组
    // argv[0]是程序名
    // argv[1]是第一个参数
    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = %s\\n", i, argv[i]);
    }
}
```

**2. 星期名称数组**
```c
const char *weekday[] = {
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
};

printf("%s\\n", weekday[0]);  // Monday
```

**3. 菜单选项**
```c
const char *menu[] = {
    "1. New Game",
    "2. Load Game",
    "3. Save Game",
    "4. Quit"
};

for (int i = 0; i < 4; i++) {
    printf("%s\\n", menu[i]);
}
```

### 五、指向指针的指针

```c
const char *names[] = {"Alice", "Bob", "Charlie"};
const char **p = names;  // 指向指针的指针

// 访问元素
printf("%s\\n", *p);     // "Alice"
printf("%s\\n", *(p+1)); // "Bob"
printf("%c\\n", **p);    // 'A'

// 二维访问
printf("%c\\n", p[0][1]); // 'l'
```

### 六、综合示例：字符串排序

```c
#include <stdio.h>
#include <string.h>

const char *names[] = {
    "Charlie",
    "Alice",
    "Bob",
    "Diana"
};
int n = sizeof(names) / sizeof(names[0]);

int main() {
    // 排序指针数组（不移动字符串本身）
    for (int i = 0; i < n - 1; i++) {
        for (int j = i + 1; j < n; j++) {
            if (strcmp(names[i], names[j]) > 0) {
                const char *temp = names[i];
                names[i] = names[j];
                names[j] = temp;
            }
        }
    }

    printf("排序后：\\n");
    for (int i = 0; i < n; i++) {
        printf("%s\\n", names[i]);
    }

    return 0;
}
```""",
                    "summary": "指针数组是元素为指针的数组，常用于字符串数组。字符串数组有两种方式：二维字符数组（可修改）和指针数组（更节省空间但不可修改）。指向指针的指针用于操作指针数组",
                    "code_example": """// 指针数组
const char *days[] = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};
printf("%s\\n", days[0]);  // "Mon"

// 字符串排序（移动指针而非字符串）
for (int i = 0; i < n - 1; i++) {
    for (int j = i + 1; j < n; j++) {
        if (strcmp(s[i], s[j]) > 0) {
            const char *temp = s[i];
            s[i] = s[j];
            s[j] = temp;
        }
    }
}

// 指向指针的指针
const char **pp = days;
printf("%s\\n", *pp);  // "Mon"
printf("%c\\n", **pp); // 'M'""",
                    "code_language": "c",
                    "code_explanation": "指针数组days存储指向字符串常量的指针，排序时只交换指针不移动字符串。pp是指向指针的指针",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["指针基础", "字符串指针", "指针与数组", "命令行参数"],
                    "tips": "排序字符串数组时，移动指针比移动字符串效率高。指针数组元素默认为const char*，不要尝试修改",
                    "common_mistakes": "1. 尝试修改指针数组指向的字符串常量；2. 混淆二维数组和指针数组的访问方式；3. 排序时移动字符串而非指针"
                }
            ]
        }
    ]
}


async def save_chapter5(db):
    """保存第5章数据到数据库"""

    # 查找C语言课程
    result = await db.execute(
        select(Course).where(Course.name.like('%C语言%'))
    )
    course = result.scalar_one_or_none()
    if not course:
        print("错误：未找到C语言课程！")
        return None

    # 查找或创建第5章
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
        total = await save_chapter5(db)
        if total:
            print(f"\n第5章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
