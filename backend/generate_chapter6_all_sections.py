"""Generate Chapter 6: 深入模块化设计与应用 - 按教学大纲生成"""
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
    "chapter_title": "深入模块化设计与应用",
    "chapter_description": "学习算法的基本概念、排序算法、函数递归调用、指针数组在函数中的应用",
    "sections": [
        {
            "title": "算法的基本概念",
            "description": "算法的基本概念及设计要点",
            "order_index": 1,
            "knowledge_points": [
                {
                    "name": "算法的基本概念",
                    "order_index": 1,
                    "content": """## 算法的基本概念

### 一、什么是算法

**算法**是对特定问题求解步骤的描述，是有限指令序列。

简单来说：算法就是解决问题的步骤和方法。

### 二、算法的特性

| 特性 | 说明 | 示例 |
|------|------|------|
| 有穷性 | 算法必须在有限步骤内结束 | 不能无限循环 |
| 确定性 | 每一步都有明确定义 | 不能有二义性 |
| 可行性 | 每一步都能执行 | 不能有无法实现的步骤 |
| 输入 | 算法有零个或多个输入 | |
| 输出 | 算法至少有一个输出 | |

### 三、算法的描述方法

**1. 自然语言描述**
```
步骤1：输入两个数a和b
步骤2：如果a>b，交换a和b
步骤3：输出a和b
```

**2. 流程图描述**
```
┌─────────────────────┐
│      开始           │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│    输入a, b          │
└─────────┬───────────┘
          ↓
      ┌───┴───┐
      │ a>b?  │
      └───┬───┘
     ┌────┴────┐
     ↓         ↓
   ┌─┴──────┐  ┌──────────┐
   │交换a,b│  │不交换     │
   └─┬──────┘  └────┬─────┘
     └────┬─────┘
          ↓
┌─────────────────────┐
│      输出a, b       │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│      结束           │
└─────────────────────┘
```

**3. 伪代码描述**
```
BEGIN
    INPUT a, b
    IF a > b THEN
        temp = a
        a = b
        b = temp
    END IF
    OUTPUT a, b
END
```

**4. C语言代码**
```c
if (a > b) {
    int temp = a;
    a = b;
    b = temp;
}
```

### 四、算法评价标准

| 标准 | 说明 |
|------|------|
| 正确性 | 算法必须能正确解决问题 |
| 时间复杂度 | 执行时间随问题规模的增长趋势 |
| 空间复杂度 | 占用内存空间随问题规模的增长趋势 |
| 可读性 | 算法易于理解和维护 |
| 健壮性 | 能处理非法输入 |

### 五、算法复杂度基础

**时间复杂度**：T(n) = O(f(n))
- O(1)：常数时间
- O(log n)：对数时间
- O(n)：线性时间
- O(n log n)：线性对数时间
- O(n²)：平方时间
- O(2ⁿ)：指数时间

**空间复杂度**：S(n) = O(f(n))

### 六、简单算法示例

**交换两个数**
```c
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
```

**判断素数**
```c
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}
```

**求最大公约数（辗转相除法）**
```c
int gcd(int a, int b) {
    while (b != 0) {
        int t = a % b;
        a = b;
        b = t;
    }
    return a;
}
```""",
                    "summary": "算法是对问题求解步骤的描述，具有有穷性、确定性、可行性等特性。算法可以用自然语言、流程图、伪代码或代码描述，评价标准包括时间复杂度和空间复杂度",
                    "code_example": """// 判断素数 - O(sqrt(n))
int isPrime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}

// 辗转相除法求最大公约数 - O(log n)
int gcd(int a, int b) {
    while (b != 0) {
        int t = a % b;
        a = b;
        b = t;
    }
    return a;
}

// 交换两个数
void swap(int *a, int *b) {
    int t = *a; *a = *b; *b = t;
}""",
                    "code_language": "c",
                    "code_explanation": "素数判断只需检查到sqrt(n)即可。辗转相除法通过不断取余使问题规模缩小，效率很高",
                    "difficulty": 1,
                    "importance": 5,
                    "related_points": ["排序算法", "递归基础", "算法复杂度", "函数设计"],
                    "tips": "评价算法主要看时间复杂度和空间复杂度。选择算法时要考虑数据规模的大小",
                    "common_mistakes": "1. 忽略算法的有穷性；2. 复杂度分析错误；3. 忽略边界条件"
                }
            ]
        },
        {
            "title": "排序算法",
            "description": "简单的排序算法：冒泡排序、选择排序",
            "order_index": 2,
            "knowledge_points": [
                {
                    "name": "冒泡排序",
                    "order_index": 1,
                    "content": """## 冒泡排序

### 一、算法思想

冒泡排序是一种简单的交换排序，通过不断比较相邻元素并在需要时交换，使较大/较小的元素逐渐"冒泡"到序列的一端。

**核心思想**：每轮比较相邻元素，将本轮最大/最小的元素放到正确位置。

### 二、算法步骤

```
原始数组：[5, 3, 8, 4, 2]

第1轮：
  比较(5,3) → 交换 → [3, 5, 8, 4, 2]
  比较(5,8) → 不交换 → [3, 5, 8, 4, 2]
  比较(8,4) → 交换 → [3, 5, 4, 8, 2]
  比较(8,2) → 交换 → [3, 5, 4, 2, 8]
  第1轮结束，最大值8到达最后

第2轮：[3, 5, 4, 2, 8] → [3, 4, 5, 2, 8]
第3轮：[3, 4, 5, 2, 8] → [3, 4, 2, 5, 8]
第4轮：[3, 4, 2, 5, 8] → [2, 3, 4, 5, 8]
```

### 三、C语言实现

```c
void bubbleSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {           // 比较轮数
        for (int j = 0; j < n - 1 - i; j++) {   // 每轮比较次数
            if (arr[j] > arr[j + 1]) {
                // 交换
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}
```

### 四、算法分析

| 指标 | 值 | 说明 |
|------|------|------|
| 时间复杂度 | O(n²) | 最坏、平均，最好O(n) |
| 空间复杂度 | O(1) | 原地排序 |
| 稳定性 | 稳定 | 相等元素不交换 |

**最好情况**：数组已有序，只需比较O(n)，不交换
**最坏情况**：数组逆序，需要O(n²)次比较和交换

### 五、冒泡排序的优化

**优化1：提前结束标志**
```c
void bubbleSortOptimized(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int swapped = 0;  // 本轮是否交换过
        for (int j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
                swapped = 1;
            }
        }
        if (!swapped) break;  // 已排好序，提前结束
    }
}
```

**优化2：记录最后交换位置**
```c
void bubbleSortOptimized2(int arr[], int n) {
    int lastSwap = n - 1;
    while (lastSwap > 0) {
        int newLastSwap = 0;
        for (int j = 0; j < lastSwap; j++) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
                newLastSwap = j;  // 记录最后交换位置
            }
        }
        lastSwap = newLastSwap;  // 之后的部分已排好
    }
}
```

### 六、算法特点

**优点**：
- 实现简单，代码易懂
- 稳定排序（相等元素相对位置不变）
- 原地排序（不需要额外空间）

**缺点**：
- 时间复杂度O(n²)，效率低
- 不适合大规模数据排序""",
                    "summary": "冒泡排序通过相邻元素比较交换，每轮将最大元素冒泡到序列末端。时间复杂度O(n²)，空间复杂度O(1)，是稳定排序。可以通过提前结束标志和记录最后交换位置优化",
                    "code_example": """// 冒泡排序基础版
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

// 优化版：提前结束
void bubbleSortFast(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int swapped = 0;
        for (int j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
                swapped = 1;
            }
        }
        if (!swapped) break;
    }
}""",
                    "code_language": "c",
                    "code_explanation": "第i轮确定第n-i个位置（从后往前）的元素。优化版通过swapped标志检测数组是否已有序，可提前结束",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["选择排序", "插入排序", "快速排序", "排序算法比较"],
                    "tips": "冒泡排序虽然简单，但时间复杂度高。优化版本对接近有序的数组效率提升明显",
                    "common_mistakes": "1. 内层循环范围错误导致越界；2. 忘记交换元素；3. 混淆升序和降序排列"
                },
                {
                    "name": "选择排序",
                    "order_index": 2,
                    "content": """## 选择排序

### 一、算法思想

选择排序的工作原理：每次从待排序序列中选择最小/最大元素，放在已排序序列的末尾。

**核心思想**：每轮从未排序部分选择最小元素，与未排序部分的第一个元素交换。

### 二、算法步骤

```
原始数组：[64, 25, 12, 22, 11]

第1轮：
  从[64,25,12,22,11]选最小值11
  与第1个元素交换 → [11, 25, 12, 22, 64]

第2轮：
  从[25,12,22,64]选最小值12
  与第2个元素交换 → [11, 12, 25, 22, 64]

第3轮：
  从[25,22,64]选最小值22
  与第3个元素交换 → [11, 12, 22, 25, 64]

第4轮：
  从[25,64]选最小值25
  与第4个元素交换 → [11, 12, 22, 25, 64]
```

### 三、C语言实现

```c
void selectionSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int minIdx = i;  // 假设当前位置是最小值
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j;  // 找到更小的元素
            }
        }
        // 交换最小元素到位置i
        if (minIdx != i) {
            int temp = arr[i];
            arr[i] = arr[minIdx];
            arr[minIdx] = temp;
        }
    }
}
```

### 四、算法分析

| 指标 | 值 | 说明 |
|------|------|------|
| 时间复杂度 | O(n²) | 比较次数固定O(n²)，交换次数最多O(n) |
| 空间复杂度 | O(1) | 原地排序 |
| 稳定性 | 不稳定 | 相等元素可能改变相对位置 |

**特点**：
- 不论数组初始状态如何，比较次数都是O(n²)
- 交换次数最多O(n)，适合写操作代价高的场景

### 五、选择排序与冒泡排序对比

| 特性 | 选择排序 | 冒泡排序 |
|------|----------|----------|
| 比较次数 | O(n²)，固定 | O(n²)，可优化 |
| 交换次数 | O(n)，最多n-1次 | O(n²)，最坏O(n²) |
| 稳定性 | 不稳定 | 稳定 |
| 适用场景 | 写操作代价高 | 读操作为主 |

### 六、选择排序的变形

**双向选择排序（鸡尾酒排序）**
```c
void cocktailSort(int arr[], int n) {
    int left = 0, right = n - 1;
    while (left < right) {
        // 从左向右，找最大元素
        int maxIdx = left;
        for (int i = left + 1; i <= right; i++) {
            if (arr[i] > arr[maxIdx]) {
                maxIdx = i;
            }
        }
        swap(&arr[maxIdx], &arr[right]);
        right--;

        if (left >= right) break;

        // 从右向左，找最小元素
        int minIdx = right;
        for (int i = right - 1; i >= left; i--) {
            if (arr[i] < arr[minIdx]) {
                minIdx = i;
            }
        }
        swap(&arr[minIdx], &arr[left]);
        left++;
    }
}
```

### 七、排序算法复杂度总结

| 算法 | 时间复杂度 | 空间复杂度 | 稳定性 |
|------|------------|------------|--------|
| 冒泡排序 | O(n²) | O(1) | 稳定 |
| 选择排序 | O(n²) | O(1) | 不稳定 |
| 插入排序 | O(n²) | O(1) | 稳定 |
| 希尔排序 | O(n^1.3) | O(1) | 不稳定 |
| 快速排序 | O(n log n) | O(log n) | 不稳定 |
| 归并排序 | O(n log n) | O(n) | 稳定 |
| 堆排序 | O(n log n) | O(1) | 不稳定 |""",
                    "summary": "选择排序每轮从未排序部分选择最小元素放到已排序末尾。时间复杂度O(n²)，空间O(1)，但交换次数少。不稳定排序",
                    "code_example": """// 选择排序
void selectionSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        int minIdx = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j;
            }
        }
        if (minIdx != i) {
            swap(&arr[i], &arr[minIdx]);
        }
    }
}

// 双向选择排序
void cocktailSort(int arr[], int n) {
    int left = 0, right = n - 1;
    while (left < right) {
        int maxIdx = left, minIdx = right;
        // 同时找最大最小
        for (int i = left; i <= right; i++) {
            if (arr[i] > arr[maxIdx]) maxIdx = i;
            if (arr[i] < arr[minIdx]) minIdx = i;
        }
        swap(&arr[maxIdx], &arr[right--]);
        swap(&arr[minIdx], &arr[left++]);
    }
}""",
                    "code_language": "c",
                    "code_explanation": "选择排序固定比较n(n-1)/2次，但最多交换n-1次。比冒泡排序交换次数少，适合交换成本高的场景",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["冒泡排序", "插入排序", "快速排序", "排序算法比较"],
                    "tips": "选择排序不稳定，但交换次数少。当写操作（swap）比比较代价高时，选择排序可能优于冒泡排序",
                    "common_mistakes": "1. 忘记交换最小元素到正确位置；2. 混淆minIdx和i；3. 选择排序是不稳定的"
                },
                {
                    "name": "排序算法综合分析",
                    "order_index": 3,
                    "content": """## 排序算法综合分析

### 一、插入排序

```c
void insertionSort(int arr[], int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i];  // 待插入元素
        int j = i - 1;
        // 将比key大的元素向后移动
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;  // 插入到正确位置
    }
}
```

**特点**：
- 对接近有序的数组效率高，最好O(n)
- 稳定排序
- 适合小规模数据或基本有序的数据

### 二、希尔排序（插入排序的改进）

```c
void shellSort(int arr[], int n) {
    // 使用希尔增量序列
    for (int gap = n / 2; gap > 0; gap /= 2) {
        // 对每个子序列进行插入排序
        for (int i = gap; i < n; i++) {
            int temp = arr[i];
            int j = i;
            while (j >= gap && arr[j - gap] > temp) {
                arr[j] = arr[j - gap];
                j -= gap;
            }
            arr[j] = temp;
        }
    }
}
```

### 三、快速排序（分治策略）

```c
// 分区函数
int partition(int arr[], int low, int high) {
    int pivot = arr[high];  // 选择最后一个元素作为基准
    int i = low - 1;

    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

// 快速排序
void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
```

### 四、排序算法选择指南

| 数据规模 | 推荐算法 | 原因 |
|----------|----------|------|
| n ≤ 50 | 插入排序 | 实现简单，对小数据高效 |
| n ≤ 10000 | 希尔排序 | 比O(n²)快，代码简单 |
| n很大 | 快速排序/归并排序/堆排序 | O(n log n) |
| 接近有序 | 插入排序 | 最好O(n) |
| 需要稳定排序 | 归并排序 | 稳定O(n log n) |

### 五、实际应用中的排序

```c
// 综合示例：成绩排序
#include <stdio.h>
#include <string.h>

typedef struct {
    char name[20];
    int score;
} Student;

int compareStudent(const void *a, const void *b) {
    Student *s1 = (Student *)a;
    Student *s2 = (Student *)b;
    return s2->score - s1->score;  // 降序
}

int main() {
    Student students[] = {
        {"Alice", 85},
        {"Bob", 92},
        {"Charlie", 78}
    };
    int n = sizeof(students) / sizeof(students[0]);

    qsort(students, n, sizeof(Student), compareStudent);

    for (int i = 0; i < n; i++) {
        printf("%s: %d\\n", students[i].name, students[i].score);
    }
    return 0;
}
```

### 六、算法复杂度深入理解

```c
// O(n²)算法 vs O(n log n)算法 对比
// n = 1000 时
// 冒泡排序：约 1,000,000 次比较
// 快速排序：约 10,000 次比较

// 实际效率对比
void benchmark() {
    int arr1[1000], arr2[1000];
    // 生成相同随机数据
    // bubbleSort(arr1, 1000);   // 约1ms
    // quickSort(arr2, 0, 999);  // 约0.1ms
}
```""",
                    "summary": "排序算法包括插入排序、希尔排序、快速排序等。不同算法适用于不同场景：插入排序适合小规模和接近有序的数据，快速排序适合大规模数据",
                    "code_example": """// 插入排序
void insertionSort(int arr[], int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i], j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j--];
        }
        arr[j + 1] = key;
    }
}

// 快速排序
void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

// qsort使用示例
qsort(arr, n, sizeof(int), cmpInt);""",
                    "code_language": "c",
                    "code_explanation": "插入排序对接近有序的数组效率很高。快速排序是实际应用中最常用的排序算法，平均O(n log n)",
                    "difficulty": 3,
                    "importance": 5,
                    "related_points": ["冒泡排序", "选择排序", "算法复杂度", "查找算法"],
                    "tips": "C标准库提供qsort函数，可以对任意类型数据进行排序。排序前根据数据特点选择合适算法",
                    "common_mistakes": "1. 快速排序基准选择不当导致最坏情况；2. 不考虑数据特点盲目选择排序算法；3. 排序算法实现有bug"
                }
            ]
        },
        {
            "title": "递归函数",
            "description": "递归调用的定义、设计要点及应用实例",
            "order_index": 3,
            "knowledge_points": [
                {
                    "name": "递归基础",
                    "order_index": 1,
                    "content": """## 递归基础

### 一、什么是递归

**递归**：函数调用自身的行为称为递归。

```c
// 最简单的递归
void countdown(int n) {
    if (n <= 0) return;      // 递归终止条件
    printf("%d ", n);
    countdown(n - 1);         // 调用自身
}

int main() {
    countdown(5);  // 输出：5 4 3 2 1
    return 0;
}
```

### 二、递归的两个必要条件

1. **递归终止条件**：函数必须有一个或不调用自己的路径
2. **递归推进**：每次递归调用都应更接近终止条件

```c
// 正确递归
int sum(int n) {
    if (n == 1) return 1;   // 终止条件
    return n + sum(n - 1);   // 推进
}

// 错误递归（没有终止条件）
int infiniteRecursion(int n) {
    return n + infiniteRecursion(n);  // 无限递归，栈溢出！
}
```

### 三、递归的执行过程

```c
int factorial(int n) {
    if (n == 0 || n == 1) return 1;
    return n * factorial(n - 1);
}

factorial(4) 的执行过程：
factorial(4)
    ↓
4 * factorial(3)
        ↓
    3 * factorial(2)
            ↓
        2 * factorial(1)
                ↓
            返回 1
        返回 2 * 1 = 2
    返回 3 * 2 = 6
返回 4 * 6 = 24
```

### 四、递归的栈帧

```
调用 factorial(4) 时的栈：
┌─────────────────┐
│ factorial(4)     │ ← top
├─────────────────┤
│ factorial(3)     │
├─────────────────┤
│ factorial(2)     │
├─────────────────┤
│ factorial(1)     │
└─────────────────┘
    ↓ 栈展开（返回）
```

### 五、递归的经典示例

**1. 阶乘**
```c
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

**2. 斐波那契数列**
```c
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}
```

**3. 求和**
```c
int sumArray(int arr[], int n) {
    if (n <= 0) return 0;
    return arr[n - 1] + sumArray(arr, n - 1);
}
```

**4. 反转字符串**
```c
void reverseString(char *str, int left, int right) {
    if (left >= right) return;
    char temp = str[left];
    str[left] = str[right];
    str[right] = temp;
    reverseString(str, left + 1, right - 1);
}
```

### 六、递归的优缺点

**优点**：
- 代码简洁，逻辑清晰
- 适合将大问题分解为相似小问题
- 自然地实现树和图的遍历

**缺点**：
- 调用开销大（函数调用、入栈、出栈）
- 栈空间有限，可能栈溢出
- 可能存在重复计算（如斐波那契数列）""",
                    "summary": "递归是函数调用自身，需满足终止条件和递归推进。递归将大问题分解为相似小问题，但有调用开销和栈溢出风险",
                    "code_example": """// 阶乘递归
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// 斐波那契数列
int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

// 求数组和
int sum(int arr[], int n) {
    if (n == 0) return 0;
    return arr[0] + sum(arr + 1, n - 1);
}

int main() {
    printf("%d\\n", factorial(5));  // 120
    printf("%d\\n", fib(10));       // 55
    int arr[] = {1, 2, 3, 4, 5};
    printf("%d\\n", sum(arr, 5));   // 15
}""",
                    "code_language": "c",
                    "code_explanation": "factorial(5) = 5*4*3*2*1 = 120，每次调用减少问题规模直到n=1终止。斐波那契有大量重复计算",
                    "difficulty": 2,
                    "importance": 5,
                    "related_points": ["递归与循环", "递归优化", "汉诺塔问题", "分治策略"],
                    "tips": "每次递归调用必须使问题规模减小，否则会无限递归。递归深度受栈空间限制",
                    "common_mistakes": "1. 忘记递归终止条件导致无限递归；2. 递归深度过大导致栈溢出；3. 斐波那契递归有大量重复计算"
                },
                {
                    "name": "递归与循环的对比",
                    "order_index": 2,
                    "content": """## 递归与循环的对比

### 一、递归与循环的关系

所有递归都能用循环实现，反之亦然。

```c
// 递归版本：计算阶乘
int factorialRec(int n) {
    if (n <= 1) return 1;
    return n * factorialRec(n - 1);
}

// 循环版本：计算阶乘
int factorialLoop(int n) {
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}
```

### 二、什么时候用递归

| 场景 | 推荐 | 原因 |
|------|------|------|
| 问题可分解为相似的子问题 | 递归 | 自然表达 |
| 树/图的遍历 | 递归 | 直观简洁 |
| 分治算法 | 递归 | 天然的分治结构 |
| 数据规模小，栈空间充足 | 递归 | 代码简洁 |

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单线性遍历 | 循环 | 无调用开销 |
| 对性能要求高 | 循环 | 无栈开销 |
| 递归深度可能很大 | 循环 | 避免栈溢出 |

### 三、递归转循环的方法

**方法1：使用栈模拟递归**
```c
// 递归版本：前序遍历二叉树
void preorderRecursive(Node *root) {
    if (root == NULL) return;
    visit(root);
    preorderRecursive(root->left);
    preorderRecursive(root->right);
}

// 循环版本：使用栈
void preorderLoop(Node *root) {
    if (root == NULL) return;
    Stack s;
    push(&s, root);
    while (!isEmpty(&s)) {
        Node *node = pop(&s);
        visit(node);
        if (node->right) push(&s, node->right);
        if (node->left) push(&s, node->left);
    }
}
```

**方法2：尾递归优化**
```c
// 尾递归版本
int sumTailRec(int n, int acc) {
    if (n == 0) return acc;
    return sumTailRec(n - 1, acc + n);
}

// 编译器可将尾递归优化为循环
int sumLoop(int n) {
    int acc = 0;
    while (n > 0) {
        acc += n;
        n--;
    }
    return acc;
}
```

### 四、汉诺塔问题

```c
// 递归解法
void hanoi(int n, char from, char to, char aux) {
    if (n == 1) {
        printf("把第1个盘子从%c移动到%c\\n", from, to);
        return;
    }
    hanoi(n - 1, from, aux, to);        // 将n-1个盘子从A移到B
    printf("把第%d个盘子从%c移动到%c\\n", n, from, to);
    hanoi(n - 1, aux, to, from);         // 将n-1个盘子从B移到C
}

int main() {
    hanoi(3, 'A', 'C', 'B');
    return 0;
}
```

**汉诺塔移动次数**：2ⁿ - 1

### 五、递归深度与栈空间

```c
// 递归深度计算
// 栈大小通常约 1MB-8MB
// 每次函数调用约占用 几十到几百字节

// 约几千次递归调用后可能栈溢出
void deepRecursion(int n) {
    printf("%d\\n", n);
    deepRecursion(n + 1);  // 无限递归，直到栈溢出
}

// 安全的递归
void safeRecursion(int n, int limit) {
    if (n >= limit) return;  // 设置上限
    printf("%d\\n", n);
    safeRecursion(n + 1, limit);
}
```

### 六、性能对比示例

```c
// 计算斐波那契数列
// 递归版本有大量重复计算：O(2^n)
int fibRec(int n) {
    if (n <= 1) return n;
    return fibRec(n - 1) + fibRec(n - 2);
}

// 循环版本：O(n)
int fibLoop(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// 记忆化递归：O(n)
int fibMemo(int n, int memo[]) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];
    memo[n] = fibMemo(n - 1, memo) + fibMemo(n - 2, memo);
    return memo[n];
}
```""",
                    "summary": "递归和循环可以互相转换。递归适合问题本身有递归结构时，循环适合简单遍历。汉诺塔等经典问题用递归更清晰，但要注意栈溢出风险",
                    "code_example": """// 斐波那契 - 循环版本（推荐）
int fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int t = a + b;
        a = b;
        b = t;
    }
    return b;
}

// 汉诺塔
void hanoi(int n, char from, char to, char aux) {
    if (n == 1) {
        printf("%c -> %c\\n", from, to);
        return;
    }
    hanoi(n - 1, from, aux, to);
    printf("%c -> %c\\n", from, to);
    hanoi(n - 1, aux, to, from);
}""",
                    "code_language": "c",
                    "code_explanation": "fib循环版本只用O(n)时间。hanoi问题递归解法非常简洁，但移动次数是指数级",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["递归基础", "递归优化", "分治算法", "算法复杂度"],
                    "tips": "能用循环解决的就不用递归，除非递归代码更清晰或问题本身是递归结构",
                    "common_mistakes": "1. 斐波那契递归版本复杂度是O(2^n)；2. 忽略递归深度限制；3. 递归算法没有记忆化"
                },
                {
                    "name": "递归设计技巧与常见问题",
                    "order_index": 3,
                    "content": """## 递归设计技巧与常见问题

### 一、递归设计的基本步骤

**1. 明确递归函数的功能**
```c
// 明确：计算arr[0..n-1]的和
int sum(int arr[], int n) {
    // ...
}
```

**2. 找到递归终止条件**
```c
// n == 0 时，没有元素，返回0
int sum(int arr[], int n) {
    if (n == 0) return 0;
    // ...
}
```

**3. 假设子问题已解决，构造递归调用**
```c
int sum(int arr[], int n) {
    if (n == 0) return 0;
    // 假设sum(arr, n-1)已经算出arr[0..n-2]的和
    // 加上arr[n-1]就是答案
    return sum(arr, n - 1) + arr[n - 1];
}
```

### 二、递归的常见模式

**模式1：线性递归**
```c
// 遍历链表
void traverse(Node *head) {
    if (head == NULL) return;
    visit(head);
    traverse(head->next);
}
```

**模式2：尾递归**
```c
// 尾递归：递归调用是函数的最后一个操作
int factorial(int n, int acc) {
    if (n == 0) return acc;
    return factorial(n - 1, acc * n);
}
// 编译器可优化为循环
```

**模式3：树形递归（分治）**
```c
// 二叉树遍历
void traverse(Node *root) {
    if (root == NULL) return;
    // 前序
    traverse(root->left);
    // 中序
    traverse(root->right);
    // 后序
}
```

### 三、递归与数学归纳法

递归与数学归纳法本质相同：

**数学归纳法**：
- 证明n=1时成立
- 假设n=k时成立，证明n=k+1时成立

**递归**：
- 终止条件（n=1时返回）
- 递归调用（假设n-1成立，计算n）

```c
// 证明：1 + 2 + ... + n = n(n+1)/2
int sum(int n) {
    if (n == 1) return 1;
    return sum(n - 1) + n;  // 假设sum(n-1)正确
}
```

### 四、递归的常见错误

**1. 递归层次过深**
```c
// 错误：10000层递归会栈溢出
void recurse(int n) {
    if (n == 0) return;
    recurse(n - 1);  // 10000层递归
}
```

**2. 重复计算问题**
```c
// 斐波那契递归有大量重复计算
// fib(5) = fib(4) + fib(3)
// fib(4) = fib(3) + fib(2)  // fib(3)重复计算了！
// 应该用记忆化或循环
```

**3. 边界条件错误**
```c
// 错误：n==0时应返回0，不是1
int sum(int arr[], int n) {
    // if (n == 0) return 1;  // 错误
    if (n == 0) return 0;     // 正确
    return sum(arr, n - 1) + arr[n - 1];
}
```

### 五、记忆化递归（备忘录模式）

```c
#define MAX_N 1000
int memo[MAX_N];  // 记忆化数组，-1表示未计算

int fibMemo(int n) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];  // 已计算过
    memo[n] = fibMemo(n - 1) + fibMemo(n - 2);
    return memo[n];
}
```

### 六、分治策略的递归实现

```c
// 归并排序 - 分治策略
void merge(int arr[], int left, int mid, int right) {
    // 合并两个有序数组
}

void mergeSort(int arr[], int left, int right) {
    if (left >= right) return;

    int mid = left + (right - left) / 2;

    // 分：递归排序两个子数组
    mergeSort(arr, left, mid);
    mergeSort(arr, mid + 1, right);

    // 治：合并有序子数组
    merge(arr, left, mid, right);
}
```""",
                    "summary": "递归设计应明确功能、找准终止条件、用子问题构造递归。记忆化递归解决重复计算问题。分治策略天然适合递归实现",
                    "code_example": """// 记忆化斐波那契
int fibMemo(int n, int *memo) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo);
}

// 归并排序（分治）
void mergeSort(int arr[], int left, int right) {
    if (left >= right) return;
    int mid = (left + right) / 2;
    mergeSort(arr, left, mid);      // 排序左半
    mergeSort(arr, mid + 1, right); // 排序右半
    merge(arr, left, mid, right);   // 合并
}""",
                    "code_language": "c",
                    "code_explanation": "记忆化通过memo数组存储已计算结果，避免重复计算。归并排序递归将数组不断二分直到只有一个元素，然后合并",
                    "difficulty": 3,
                    "importance": 4,
                    "related_points": ["递归基础", "递归与循环", "分治算法", "排序算法"],
                    "tips": "递归函数应有明确的终止条件和推进方向。分治策略递归的子问题规模应大致相等",
                    "common_mistakes": "1. 斐波那契不用记忆化会超时；2. 递归深度估算错误；3. 分治时子问题划分不均匀"
                }
            ]
        },
        {
            "title": "指针数组与函数",
            "description": "指针、数组在函数设计中的要点及重要用途",
            "order_index": 4,
            "knowledge_points": [
                {
                    "name": "指针数组与函数参数",
                    "order_index": 1,
                    "content": """## 指针数组与函数参数

### 一、指针数组的概念

```c
// 指针数组：数组元素是指针
int *ptrArr[10];     // 10个int*元素的数组
char *strArr[5];    // 5个char*元素的数组（字符串数组）
```

### 二、指针数组作为函数参数

```c
// 打印字符串数组
void printStrings(char *arr[], int n) {
    for (int i = 0; i < n; i++) {
        printf("%s\\n", arr[i]);
    }
}

int main() {
    const char *names[] = {
        "Alice",
        "Bob",
        "Charlie"
    };
    printStrings(names, 3);
    return 0;
}
```

### 三、指针数组与二维数组的区别

```c
// 二维字符数组
char names1[3][20] = {"Alice", "Bob", "Charlie"};
// names1[i] 是 char[20]，是数组，值是字符串的副本

// 指针数组
const char *names2[] = {"Alice", "Bob", "Charlie"};
// names2[i] 是 char*，值是指向字符串常量的指针
```

| 特性 | char name[][20] | const char *name[] |
|------|-----------------|-------------------|
| 内存占用 | 60字节 | 3个指针+字符串 |
| 字符串可修改 | name[i][j]可改 | 不可修改 |
| 初始化 | 必须指定大小 | 自动计算大小 |
| 灵活性 | 低 | 高 |

### 四、修改字符串数组的元素

```c
int main() {
    // 字符串数组（常量指针）
    const char *names[] = {"one", "two", "three"};

    // 可以改变指针指向
    names[0] = "ZERO";  // OK，改变指针指向

    // 不能修改字符串内容
    // names[0][0] = 'O';  // 错误！

    // 如果需要修改，使用二维数组
    char names2[][10] = {"one", "two", "three"};
    names2[0][0] = 'O';  // OK，可以修改

    return 0;
}
```

### 五、指针数组的综合应用

**1. 星期查询**
```c
const char *weekdayNames[] = {
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
};

const char* getWeekdayName(int day) {
    if (day >= 1 && day <= 7) {
        return weekdayNames[day - 1];
    }
    return "Invalid";
}
```

**2. 命令处理**
```c
const char *commands[] = {
    "help", "quit", "add", "delete", "list"
};

int findCommand(const char *cmd) {
    for (int i = 0; i < 5; i++) {
        if (strcmp(cmd, commands[i]) == 0) {
            return i;
        }
    }
    return -1;
}
```

### 六、指向指针的指针

```c
int main() {
    const char *names[] = {"Alice", "Bob"};
    const char **p = names;  // 指向指针的指针

    // 访问方式
    printf("%s\\n", *p);     // Alice，等价于names[0]
    printf("%s\\n", *(p+1)); // Bob，等价于names[1]
    printf("%c\\n", **p);    // 'A'

    // 二级指针遍历
    for (const char **pp = names; pp < names + 2; pp++) {
        printf("%s\\n", *pp);
    }
    return 0;
}
```""",
                    "summary": "指针数组是元素为指针的数组，字符串指针数组每个元素指向字符串常量。指向指针的指针用于操作指针数组。二维字符数组和指针数组都可存储字符串",
                    "code_example": """// 指针数组作为函数参数
void printAll(const char *arr[], int n) {
    for (int i = 0; i < n; i++) {
        printf("%s\\n", arr[i]);
    }
}

// 指向指针的指针
const char *names[] = {"Hello", "World"};
const char **p = names;  // p指向names[0]
printf("%s\\n", *p);     // Hello
printf("%c\\n", **p);    // H""",
                    "code_language": "c",
                    "code_explanation": "指针数组arr[]作为参数时退化为指向指针的指针。*p获取字符串，**p获取首字符",
                    "difficulty": 2,
                    "importance": 4,
                    "related_points": ["指针基础", "字符串数组", "命令行参数", "动态指针数组"],
                    "tips": "指针数组比二维数组更节省空间，但不能修改字符串内容（如果指向常量区）",
                    "common_mistakes": "1. 混淆指针数组和二维数组；2. 通过指针数组修改字符串常量；3. 忽略const的正确使用"
                },
                {
                    "name": "函数指针与回调",
                    "order_index": 2,
                    "content": """## 函数指针与回调

### 一、函数指针的概念

函数指针是指向函数的指针变量。

```c
// 函数指针声明
返回类型 (*指针名)(参数类型列表);

// 示例
int (*pFunc)(int, int);  // 指向返回int、接收两个int的函数
void (*pPrint)(const char*);  // 指向返回void、接收const char*的函数
```

### 二、函数指针的使用

```c
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

int main() {
    int (*p)(int, int) = add;  // p指向add函数
    printf("%d\\n", p(3, 2));   // 输出5，调用add(3,2)

    p = sub;                    // p指向sub函数
    printf("%d\\n", p(3, 2));   // 输出1，调用sub(3,2)

    return 0;
}
```

### 三、函数指针作为函数参数（回调）

```c
// 回调函数类型
typedef int (*CompareFunc)(int, int);

// 查找最大值
int findMax(int arr[], int n, CompareFunc cmp) {
    int maxIdx = 0;
    for (int i = 1; i < n; i++) {
        if (cmp(arr[i], arr[maxIdx]) > 0) {
            maxIdx = i;
        }
    }
    return arr[maxIdx];
}

// 比较函数
int ascending(int a, int b) { return a > b ? 1 : -1; }
int descending(int a, int b) { return a < b ? 1 : -1; }

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    printf("最大值(升序): %d\\n", findMax(arr, 8, ascending));
    printf("最大值(降序): %d\\n", findMax(arr, 8, descending));
    return 0;
}
```

### 四、qsort的回调函数

```c
#include <stdlib.h>

int compareInt(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);  // 升序
}

int compareIntDesc(const void *a, const void *b) {
    return (*(int*)b - *(int*)a);  // 降序
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = sizeof(arr) / sizeof(arr[0]);

    qsort(arr, n, sizeof(int), compareInt);

    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    return 0;
}
```

### 五、通用查找函数

```c
typedef int (*Predicate)(const void*);

void* findIf(void *arr, int n, size_t elemSize, Predicate pred) {
    char *p = (char*)arr;
    for (int i = 0; i < n; i++) {
        if (pred(p + i * elemSize)) {
            return p + i * elemSize;
        }
    }
    return NULL;
}

// 使用示例
int isEven(const void *p) {
    return (*(int*)p) % 2 == 0;
}

int main() {
    int arr[] = {1, 3, 5, 7, 8};
    int *found = findIf(arr, 5, sizeof(int), isEven);
    if (found) {
        printf("Found: %d\\n", *found);  // 8
    }
    return 0;
}
```

### 六、函数指针数组

```c
// 计算器菜单
typedef int (*Operation)(int, int);

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }
int div(int a, int b) { return b != 0 ? a / b : 0; }

int main() {
    Operation ops[] = {add, sub, mul, div};
    const char *opNames[] = {"+", "-", "*", "/"};

    int a = 10, b = 3;
    for (int i = 0; i < 4; i++) {
        printf("%d %s %d = %d\\n", a, opNames[i], b, ops[i](a, b));
    }
    return 0;
}
```""",
                    "summary": "函数指针指向函数，可作为函数参数实现回调。qsort使用回调函数实现通用排序。函数指针数组用于实现命令分发",
                    "code_example": """// 函数指针
int (*p)(int, int) = add;  // p指向add
p = sub;                     // p改为指向sub
printf("%d\\n", p(3, 2));    // 输出1

// qsort回调
int cmp(const void *a, const void *b) {
    return *(int*)a - *(int*)b;
}
qsort(arr, n, sizeof(int), cmp);

// 函数指针数组
Operation ops[] = {add, sub, mul, div};
ops[0](10, 5);  // add(10,5) = 15""",
                    "code_language": "c",
                    "code_explanation": "函数指针p可以指向不同函数，实现运行时选择。qsort通过CompareFunc回调实现通用排序，不需要知道元素类型",
                    "difficulty": 3,
                    "importance": 4,
                    "related_points": ["指针数组", "typedef用法", "函数基础", "回调函数"],
                    "tips": "函数指针常用于回调、策略模式、命令分发等场景。使用typedef可以让函数指针更易读",
                    "common_mistakes": "1. 函数指针声明语法错误；2. 没有正确解引用函数指针；3. 回调函数签名与期望不匹配"
                }
            ]
        },
        {
            "title": "综合应用实例",
            "description": "使用排序算法、函数递归调用等知识去拓展计算器及学生成绩档案管理系统",
            "order_index": 5,
            "knowledge_points": [
                {
                    "name": "排序算法综合应用",
                    "order_index": 1,
                    "content": """## 排序算法综合应用

### 一、学生成绩管理系统

```c
#include <stdio.h>
#include <string.h>

#define MAX_STUDENTS 100
#define NAME_LEN 30

typedef struct {
    int id;
    char name[NAME_LEN];
    float scores[3];  // 三门课成绩
    float average;
} Student;

// 成绩比较函数
int compareByAverage(const void *a, const void *b) {
    Student *s1 = (Student*)a;
    Student *s2 = (Student*)b;
    if (s1->average < s2->average) return 1;   // 升序
    if (s1->average > s2->average) return -1;
    return strcmp(s1->name, s2->name);          // 同分按姓名
}

// 成绩统计
void calculateAverages(Student students[], int n) {
    for (int i = 0; i < n; i++) {
        float sum = 0;
        for (int j = 0; j < 3; j++) {
            sum += students[i].scores[j];
        }
        students[i].average = sum / 3;
    }
}

// 打印成绩单
void printReport(Student students[], int n) {
    printf("%-10s %-15s %-8s %-8s %-8s %-8s\\n",
           "ID", "Name", "Score1", "Score2", "Score3", "Average");
    printf("------------------------------------------------\\n");
    for (int i = 0; i < n; i++) {
        printf("%-10d %-15s %-8.1f %-8.1f %-8.1f %-8.2f\\n",
               students[i].id,
               students[i].name,
               students[i].scores[0],
               students[i].scores[1],
               students[i].scores[2],
               students[i].average);
    }
}

int main() {
    Student students[] = {
        {1001, "Alice", {85, 92, 78}, 0},
        {1002, "Bob", {72, 88, 95}, 0},
        {1003, "Charlie", {90, 76, 88}, 0},
        {1004, "Diana", {88, 95, 92}, 0}
    };
    int n = sizeof(students) / sizeof(students[0]);

    calculateAverages(students, n);

    printf("排序前：\\n");
    printReport(students, n);

    qsort(students, n, sizeof(Student), compareByAverage);

    printf("\\n排序后（按平均分降序）：\\n");
    printReport(students, n);

    return 0;
}
```

### 二、多字段排序

```c
typedef struct {
    int id;
    char name[20];
    int age;
    float score;
} Record;

// 先按分数降序，分数相同按年龄升序，再按姓名升序
int compareMulti(const void *a, const void *b) {
    Record *r1 = (Record*)a;
    Record *r2 = (Record*)b;

    if (r1->score != r2->score) {
        return r2->score > r1->score ? 1 : -1;  // 分数降序
    }
    if (r1->age != r2->age) {
        return r1->age < r2->age ? 1 : -1;       // 年龄升序
    }
    return strcmp(r1->name, r2->name);           // 姓名升序
}
```

### 三、链表排序

```c
typedef struct Node {
    int data;
    struct Node *next;
} Node;

Node* mergeSortedLists(Node *l1, Node *l2) {
    if (!l1) return l2;
    if (!l2) return l1;

    Node *result;
    if (l1->data <= l2->data) {
        result = l1;
        result->next = mergeSortedLists(l1->next, l2);
    } else {
        result = l2;
        result->next = mergeSortedLists(l1, l2->next);
    }
    return result;
}
```""",
                    "summary": "排序算法综合应用包括学生成绩管理系统（结构体排序）、多字段排序（qsort回调）、链表排序（归并）等实际场景",
                    "code_example": """// 结构体多字段排序
int compareStudent(const void *a, const void *b) {
    Student *s1 = (Student*)a, *s2 = (Student*)b;
    if (s1->score != s2->score)
        return s2->score > s1->score ? 1 : -1;  // 分数降序
    return strcmp(s1->name, s2->name);           // 姓名升序
}

// 成绩管理系统
qsort(students, n, sizeof(Student), compareStudent);""",
                    "code_language": "c",
                    "code_explanation": "qsort通过compareStudent回调实现多字段排序。compare函数返回正数表示a应排在b后面",
                    "difficulty": 3,
                    "importance": 4,
                    "related_points": ["排序算法", "qsort函数", "结构体", "递归排序"],
                    "tips": "qsort是C标准库提供的通用排序函数，可以对任意类型数据进行排序，只需提供比较函数",
                    "common_mistakes": "1. qsort比较函数返回类型错误；2. 结构体比较大小时用==而非strcmp；3. 忽略空指针检查"
                },
                {
                    "name": "递归与模块化综合应用",
                    "order_index": 2,
                    "content": """## 递归与模块化综合应用

### 一、递归模块化计算器

```c
#include <stdio.h>

typedef double (*BinaryOp)(double, double);

double add(double a, double b) { return a + b; }
double subtract(double a, double b) { return a - b; }
double multiply(double a, double b) { return a * b; }
double divide(double a, double b) { return b != 0 ? a / b : 0; }

// 递归计算表达式
double evaluate(double numbers[], char operators[], int n) {
    if (n == 1) return numbers[0];

    // 递归：先计算第一个运算符左右两边的表达式
    double left = evaluate(numbers, operators, n - 1);
    double right = numbers[n - 1];
    char op = operators[n - 2];

    switch (op) {
        case '+': return left + right;
        case '-': return left - right;
        case '*': return left * right;
        case '/': return right != 0 ? left / right : 0;
    }
    return 0;
}

// 使用函数指针数组的处理
double processExpression(double a, char op, double b) {
    BinaryOp ops[] = {add, subtract, multiply, divide};
    char opChars[] = {'+', '-', '*', '/'};

    for (int i = 0; i < 4; i++) {
        if (op == opChars[i]) {
            return ops[i](a, b);
        }
    }
    return 0;
}
```

### 二、学生档案递归处理

```c
#include <stdio.h>
#include <string.h>

typedef struct {
    char name[30];
    int age;
    float score;
} Student;

// 递归查找学生
Student* findStudent(Student students[], int n, const char *name) {
    if (n == 0) return NULL;
    if (strcmp(students[n-1].name, name) == 0) {
        return &students[n-1];
    }
    return findStudent(students, n - 1, name);
}

// 递归统计
int countAbove(Student students[], int n, float threshold) {
    if (n == 0) return 0;
    int count = countAbove(students, n - 1, threshold);
    if (students[n-1].score >= threshold) {
        count++;
    }
    return count;
}

// 递归计算平均分
float averageScore(Student students[], int n) {
    if (n == 0) return 0;
    return (averageScore(students, n - 1) * (n - 1) + students[n-1].score) / n;
}
```

### 三、树形结构的递归处理

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int value;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

// 创建节点
TreeNode* createNode(int value) {
    TreeNode *node = malloc(sizeof(TreeNode));
    node->value = value;
    node->left = node->right = NULL;
    return node;
}

// 递归插入
TreeNode* insert(TreeNode *root, int value) {
    if (root == NULL) return createNode(value);
    if (value < root->value) {
        root->left = insert(root->left, value);
    } else {
        root->right = insert(root->right, value);
    }
    return root;
}

// 递归遍历
void inorder(TreeNode *root) {
    if (root == NULL) return;
    inorder(root->left);
    printf("%d ", root->value);
    inorder(root->right);
}

// 递归计算高度
int height(TreeNode *root) {
    if (root == NULL) return 0;
    int leftH = height(root->left);
    int rightH = height(root->right);
    return (leftH > rightH ? leftH : rightH) + 1;
}

// 递归释放
void freeTree(TreeNode *root) {
    if (root == NULL) return;
    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

int main() {
    TreeNode *root = NULL;
    int values[] = {50, 30, 70, 20, 40, 60, 80};
    int n = sizeof(values) / sizeof(values[0]);

    for (int i = 0; i < n; i++) {
        root = insert(root, values[i]);
    }

    printf("中序遍历: ");
    inorder(root);  // 20 30 40 50 60 70 80

    printf("\\n树高度: %d\\n", height(root));

    freeTree(root);
    return 0;
}
```

### 四、模块化程序设计原则

```c
// 模块化设计示例：学生成绩管理系统

// ========== student.h ==========
#ifndef STUDENT_H
#define STUDENT_H

typedef struct {
    int id;
    char name[30];
    float scores[3];
    float average;
} Student;

void initStudent(Student *s, int id, const char *name);
void calcAverage(Student *s);
int compareScore(const void *a, const void *b);

#endif

// ========== student.c ==========
#include "student.h"
#include <string.h>

void initStudent(Student *s, int id, const char *name) {
    s->id = id;
    strncpy(s->name, name, 29);
    s->name[29] = '\\0';
    for (int i = 0; i < 3; i++) s->scores[i] = 0;
    s->average = 0;
}

void calcAverage(Student *s) {
    float sum = s->scores[0] + s->scores[1] + s->scores[2];
    s->average = sum / 3;
}
```""",
                    "summary": "递归与模块化综合应用包括表达式求值、学生档案管理（递归查找统计）、二叉树结构（插入遍历）等模块化程序设计",
                    "code_example": """// 递归查找学生
Student* findStudent(Student arr[], int n, const char *name) {
    if (n == 0) return NULL;
    if (strcmp(arr[n-1].name, name) == 0) return &arr[n-1];
    return findStudent(arr, n-1, name);
}

// 二叉搜索树插入
TreeNode* insert(TreeNode *root, int val) {
    if (!root) return createNode(val);
    if (val < root->value) root->left = insert(root->left, val);
    else root->right = insert(root->right, val);
    return root;
}

// 递归树高度
int height(TreeNode *root) {
    if (!root) return 0;
    int h1 = height(root->left);
    int h2 = height(root->right);
    return (h1 > h2 ? h1 : h2) + 1;
}""",
                    "code_language": "c",
                    "code_explanation": "递归模块化将功能分解为独立函数，二叉搜索树递归插入利用树结构特点。height计算左右子树高度取较大者加1",
                    "difficulty": 3,
                    "importance": 4,
                    "related_points": ["递归函数", "模块化设计", "指针与结构体", "排序算法"],
                    "tips": "模块化程序将数据结构和操作分离，头文件声明接口，源文件实现细节",
                    "common_mistakes": "1. 递归忘记终止条件导致栈溢出；2. 二叉树操作忘记处理空指针；3. 模块间耦合度太高"
                }
            ]
        }
    ]
}


async def save_chapter6(db):
    """保存第6章数据到数据库"""

    # 查找C语言课程
    result = await db.execute(
        select(Course).where(Course.name.like('%C语言%'))
    )
    course = result.scalar_one_or_none()
    if not course:
        print("错误：未找到C语言课程！")
        return None

    # 查找或创建第6章
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
        total = await save_chapter6(db)
        if total:
            print(f"\n第6章生成完成，共{len(CHAPTER_DATA['sections'])}个小节，{total}个知识点")


if __name__ == "__main__":
    asyncio.run(main())
