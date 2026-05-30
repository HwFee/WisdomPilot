'use client'

import { useRef, useEffect, useCallback, useState } from 'react'
import dynamic from 'next/dynamic'

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface CodeEditorPanelProps {
  value: string
  onChange: (value: string) => void
  language?: string
  readOnly?: boolean
  height?: string
}

// ========================================
// Phase 1: 增强的静态补全数据
// ========================================

// ========== C 语言 ==========
const C_KEYWORDS = [
  'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
  'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
  'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
  'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
]

const C_STDIO_FUNCTIONS = [
  { name: 'printf', snippet: 'printf("${1:format}", ${2:args})', detail: '格式化输出到标准输出' },
  { name: 'scanf', snippet: 'scanf("${1:format}", &${2:var})', detail: '从标准输入读取' },
  { name: 'puts', snippet: 'puts(${1:str})', detail: '输出字符串并换行' },
  { name: 'gets', snippet: 'gets(${1:str})', detail: '读取一行（不安全）' },
  { name: 'getchar', snippet: 'getchar()', detail: '读取一个字符' },
  { name: 'putchar', snippet: 'putchar(${1:ch})', detail: '输出一个字符' },
  { name: 'fgets', snippet: 'fgets(${1:str}, ${2:n}, ${3:stdin})', detail: '安全读取字符串' },
  { name: 'fputs', snippet: 'fputs(${1:str}, ${2:stdout})', detail: '输出字符串到流' },
  { name: 'fopen', snippet: 'fopen("${1:filename}", "${2:r}")', detail: '打开文件 (r/w/a/r+/w+/a+)' },
  { name: 'fclose', snippet: 'fclose(${1:fp})', detail: '关闭文件' },
  { name: 'fscanf', snippet: 'fscanf(${1:fp}, "${2:format}", &${3:var})', detail: '从文件格式化读取' },
  { name: 'fprintf', snippet: 'fprintf(${1:fp}, "${2:format}", ${3:args})', detail: '格式化输出到文件' },
  { name: 'fread', snippet: 'fread(${1:ptr}, ${2:size}, ${3:n}, ${4:fp})', detail: '二进制读取' },
  { name: 'fwrite', snippet: 'fwrite(${1:ptr}, ${2:size}, ${3:n}, ${4:fp})', detail: '二进制写入' },
  { name: 'feof', snippet: 'feof(${1:fp})', detail: '检查文件结束' },
  { name: 'rewind', snippet: 'rewind(${1:fp})', detail: '重置文件指针' },
  { name: 'sprintf', snippet: 'sprintf(${1:str}, "${2:format}", ${3:args})', detail: '格式化到字符串' },
  { name: 'sscanf', snippet: 'sscanf(${1:str}, "${2:format}", &${3:var})', detail: '从字符串读取' },
]

const C_STDLIB_FUNCTIONS = [
  { name: 'malloc', snippet: 'malloc(${1:size} * sizeof(${2:type}))', detail: '动态内存分配' },
  { name: 'calloc', snippet: 'calloc(${1:n}, sizeof(${2:type}))', detail: '分配并初始化为0' },
  { name: 'realloc', snippet: 'realloc(${1:ptr}, ${2:new_size})', detail: '重新分配内存' },
  { name: 'free', snippet: 'free(${1:ptr})', detail: '释放内存' },
  { name: 'exit', snippet: 'exit(${1:0})', detail: '退出程序 (0=正常, 1=异常)' },
  { name: 'atoi', snippet: 'atoi(${1:str})', detail: '字符串转整数' },
  { name: 'atof', snippet: 'atof(${1:str})', detail: '字符串转浮点数' },
  { name: 'atol', snippet: 'atol(${1:str})', detail: '字符串转长整数' },
  { name: 'itoa', snippet: 'itoa(${1:num}, ${2:str}, ${3:10})', detail: '整数转字符串' },
  { name: 'rand', snippet: 'rand()', detail: '生成随机数 (0-RAND_MAX)' },
  { name: 'srand', snippet: 'srand(${1:time(NULL)})', detail: '设置随机种子' },
  { name: 'abs', snippet: 'abs(${1:n})', detail: '整数绝对值' },
  { name: 'labs', snippet: 'labs(${1:n})', detail: '长整数绝对值' },
  { name: 'qsort', snippet: 'qsort(${1:arr}, ${2:n}, sizeof(${3:type}), ${4:compare})', detail: '快速排序' },
  { name: 'bsearch', snippet: 'bsearch(&${1:key}, ${2:arr}, ${3:n}, sizeof(${4:type}), ${5:compare})', detail: '二分查找' },
]

const C_STRING_FUNCTIONS = [
  { name: 'strlen', snippet: 'strlen(${1:str})', detail: '字符串长度' },
  { name: 'strcpy', snippet: 'strcpy(${1:dest}, ${2:src})', detail: '复制字符串' },
  { name: 'strncpy', snippet: 'strncpy(${1:dest}, ${2:src}, ${3:n})', detail: '复制前n个字符' },
  { name: 'strcat', snippet: 'strcat(${1:dest}, ${2:src})', detail: '连接字符串' },
  { name: 'strncat', snippet: 'strncat(${1:dest}, ${2:src}, ${3:n})', detail: '连接前n个字符' },
  { name: 'strcmp', snippet: 'strcmp(${1:s1}, ${2:s2})', detail: '比较字符串 (返回0相等)' },
  { name: 'strncmp', snippet: 'strncmp(${1:s1}, ${2:s2}, ${3:n})', detail: '比较前n个字符' },
  { name: 'strstr', snippet: 'strstr(${1:haystack}, ${2:needle})', detail: '查找子串' },
  { name: 'strchr', snippet: 'strchr(${1:str}, ${2:\'c\'})', detail: '查找字符首次出现' },
  { name: 'strrchr', snippet: 'strrchr(${1:str}, ${2:\'c\'})', detail: '查找字符最后出现' },
  { name: 'strtok', snippet: 'strtok(${1:str}, "${2:delim}")', detail: '分割字符串' },
  { name: 'memcpy', snippet: 'memcpy(${1:dest}, ${2:src}, ${3:n})', detail: '内存复制' },
  { name: 'memset', snippet: 'memset(${1:ptr}, ${2:0}, ${3:n})', detail: '内存填充' },
  { name: 'memcmp', snippet: 'memcmp(${1:s1}, ${2:s2}, ${3:n})', detail: '内存比较' },
]

const C_MATH_FUNCTIONS = [
  { name: 'sqrt', snippet: 'sqrt(${1:x})', detail: '平方根' },
  { name: 'pow', snippet: 'pow(${1:x}, ${2:n})', detail: 'x的n次幂' },
  { name: 'exp', snippet: 'exp(${1:x})', detail: 'e的x次幂' },
  { name: 'log', snippet: 'log(${1:x})', detail: '自然对数' },
  { name: 'log10', snippet: 'log10(${1:x})', detail: '以10为底的对数' },
  { name: 'sin', snippet: 'sin(${1:x})', detail: '正弦（弧度）' },
  { name: 'cos', snippet: 'cos(${1:x})', detail: '余弦（弧度）' },
  { name: 'tan', snippet: 'tan(${1:x})', detail: '正切（弧度）' },
  { name: 'asin', snippet: 'asin(${1:x})', detail: '反正弦' },
  { name: 'acos', snippet: 'acos(${1:x})', detail: '反余弦' },
  { name: 'atan', snippet: 'atan(${1:x})', detail: '反正切' },
  { name: 'floor', snippet: 'floor(${1:x})', detail: '向下取整' },
  { name: 'ceil', snippet: 'ceil(${1:x})', detail: '向上取整' },
  { name: 'round', snippet: 'round(${1:x})', detail: '四舍五入' },
  { name: 'fabs', snippet: 'fabs(${1:x})', detail: '浮点数绝对值' },
  { name: 'fmod', snippet: 'fmod(${1:x}, ${2:y})', detail: '浮点数取模' },
]

// C 语言常用代码模板
const C_SNIPPETS = [
  { name: 'main', snippet: 'int main() {\n\t${1:// code}\n\treturn 0;\n}', detail: '主函数模板', sortText: '0_main' },
  { name: 'main with args', snippet: 'int main(int argc, char *argv[]) {\n\t${1:// code}\n\treturn 0;\n}', detail: '带参数的主函数', sortText: '0_main' },
  { name: 'for', snippet: 'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t${3:// code}\n}', detail: 'for 循环', sortText: '1_for' },
  { name: 'fori', snippet: 'for (int i = 0; i < ${1:n}; i++) {\n\t${2:// code}\n}', detail: '简化 for 循环', sortText: '1_for' },
  { name: 'while', snippet: 'while (${1:condition}) {\n\t${2:// code}\n}', detail: 'while 循环', sortText: '1_while' },
  { name: 'do-while', snippet: 'do {\n\t${1:// code}\n} while (${2:condition});', detail: 'do-while 循环', sortText: '1_do' },
  { name: 'if', snippet: 'if (${1:condition}) {\n\t${2:// code}\n}', detail: 'if 语句', sortText: '1_if' },
  { name: 'if-else', snippet: 'if (${1:condition}) {\n\t${2:// code}\n} else {\n\t${3:// code}\n}', detail: 'if-else 语句', sortText: '1_if' },
  { name: 'switch', snippet: 'switch (${1:var}) {\n\tcase ${2:value}:\n\t\t${3:// code}\n\t\tbreak;\n\tdefault:\n\t\t${4:// code}\n}', detail: 'switch 语句', sortText: '1_switch' },
  { name: 'struct', snippet: 'struct ${1:Name} {\n\t${2:type} ${3:field};\n};', detail: '结构体定义', sortText: '2_struct' },
  { name: 'typedef struct', snippet: 'typedef struct {\n\t${1:type} ${2:field};\n} ${3:Name};', detail: 'typedef 结构体', sortText: '2_struct' },
  { name: 'function', snippet: '${1:return_type} ${2:function_name}(${3:params}) {\n\t${4:// code}\n\treturn ${5:value};\n}', detail: '函数定义', sortText: '2_func' },
  { name: 'array input', snippet: 'int arr[${1:100}];\nfor (int i = 0; i < ${2:n}; i++) {\n\tscanf("%d", &arr[i]);\n}', detail: '数组输入模板', sortText: '3_array' },
  { name: 'array output', snippet: 'for (int i = 0; i < ${1:n}; i++) {\n\tprintf("%d ", arr[i]);\n}\nprintf("\\n");', detail: '数组输出模板', sortText: '3_array' },
  { name: 'swap', snippet: 'void swap(int *a, int *b) {\n\tint temp = *a;\n\t*a = *b;\n\t*b = temp;\n}', detail: '交换函数', sortText: '2_func' },
  { name: 'max', snippet: 'int max(int a, int b) {\n\treturn a > b ? a : b;\n}', detail: '最大值函数', sortText: '2_func' },
  { name: 'min', snippet: 'int min(int a, int b) {\n\treturn a < b ? a : b;\n}', detail: '最小值函数', sortText: '2_func' },
  { name: 'include stdio', snippet: '#include <stdio.h>', detail: '标准输入输出头文件', sortText: '0_inc' },
  { name: 'include stdlib', snippet: '#include <stdlib.h>', detail: '标准库头文件', sortText: '0_inc' },
  { name: 'include string', snippet: '#include <string.h>', detail: '字符串处理头文件', sortText: '0_inc' },
  { name: 'include math', snippet: '#include <math.h>', detail: '数学函数头文件', sortText: '0_inc' },
]

// ========== C++ 语言 ==========
const CPP_KEYWORDS = [
  ...C_KEYWORDS,
  'alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit',
  'atomic_noexcept', 'bitand', 'bitor', 'catch', 'class', 'compl', 'concept',
  'const_cast', 'co_await', 'co_return', 'co_yield', 'decltype', 'delete',
  'dynamic_cast', 'explicit', 'export', 'false', 'friend', 'inline', 'mutable',
  'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or',
  'or_eq', 'private', 'protected', 'public', 'reflexpr', 'reinterpret_cast',
  'requires', 'static_assert', 'static_cast', 'synchronized', 'template', 'this',
  'thread_local', 'throw', 'true', 'try', 'typeid', 'typename', 'using', 'virtual',
  'xor', 'xor_eq',
]

const CPP_STL_CONTAINERS = [
  { name: 'vector', snippet: 'std::vector<${1:int}> ${2:vec}', detail: '动态数组 O(1)末尾插入' },
  { name: 'vector init', snippet: 'std::vector<${1:int}> ${2:vec}(${3:n}, ${4:0})', detail: '初始化n个元素的vector' },
  { name: 'list', snippet: 'std::list<${1:int}> ${2:lst}', detail: '双向链表 O(1)任意位置插入' },
  { name: 'deque', snippet: 'std::deque<${1:int}> ${2:dq}', detail: '双端队列 O(1)头尾插入' },
  { name: 'stack', snippet: 'std::stack<${1:int}> ${2:stk}', detail: '栈 LIFO' },
  { name: 'queue', snippet: 'std::queue<${1:int}> ${2:q}', detail: '队列 FIFO' },
  { name: 'priority_queue', snippet: 'std::priority_queue<${1:int}> ${2:pq}', detail: '优先队列（大根堆）' },
  { name: 'priority_queue min', snippet: 'std::priority_queue<${1:int}, std::vector<${1:int}>, std::greater<${1:int}>> ${2:pq}', detail: '小根堆' },
  { name: 'set', snippet: 'std::set<${1:int}> ${2:s}', detail: '有序集合 O(log n)' },
  { name: 'multiset', snippet: 'std::multiset<${1:int}> ${2:ms}', detail: '有序多重集合' },
  { name: 'unordered_set', snippet: 'std::unordered_set<${1:int}> ${2:us}', detail: '无序集合 O(1)' },
  { name: 'map', snippet: 'std::map<${1:int}, ${2:int}> ${3:m}', detail: '有序映射 O(log n)' },
  { name: 'multimap', snippet: 'std::multimap<${1:int}, ${2:int}> ${3:mm}', detail: '有序多重映射' },
  { name: 'unordered_map', snippet: 'std::unordered_map<${1:int}, ${2:int}> ${3:um}', detail: '无序映射 O(1)' },
  { name: 'pair', snippet: 'std::pair<${1:int}, ${2:int}> ${3:p}', detail: '键值对' },
  { name: 'make_pair', snippet: 'std::make_pair(${1:first}, ${2:second})', detail: '创建pair' },
]

const CPP_ALGORITHMS = [
  { name: 'sort', snippet: 'std::sort(${1:vec}.begin(), ${1:vec}.end())', detail: '排序 O(n log n)' },
  { name: 'sort desc', snippet: 'std::sort(${1:vec}.begin(), ${1:vec}.end(), std::greater<${2:int}>())', detail: '降序排序' },
  { name: 'stable_sort', snippet: 'std::stable_sort(${1:vec}.begin(), ${1:vec}.end())', detail: '稳定排序' },
  { name: 'reverse', snippet: 'std::reverse(${1:vec}.begin(), ${1:vec}.end())', detail: '反转' },
  { name: 'find', snippet: 'std::find(${1:vec}.begin(), ${1:vec}.end(), ${2:value})', detail: '查找元素' },
  { name: 'binary_search', snippet: 'std::binary_search(${1:vec}.begin(), ${1:vec}.end(), ${2:value})', detail: '二分查找' },
  { name: 'lower_bound', snippet: 'std::lower_bound(${1:vec}.begin(), ${1:vec}.end(), ${2:value})', detail: '第一个>=value的位置' },
  { name: 'upper_bound', snippet: 'std::upper_bound(${1:vec}.begin(), ${1:vec}.end(), ${2:value})', detail: '第一个>value的位置' },
  { name: 'max_element', snippet: 'std::max_element(${1:vec}.begin(), ${1:vec}.end())', detail: '最大元素迭代器' },
  { name: 'min_element', snippet: 'std::min_element(${1:vec}.begin(), ${1:vec}.end())', detail: '最小元素迭代器' },
  { name: 'accumulate', snippet: 'std::accumulate(${1:vec}.begin(), ${1:vec}.end(), ${2:0})', detail: '求和 (需要<numeric>)' },
  { name: 'count', snippet: 'std::count(${1:vec}.begin(), ${1:vec}.end(), ${2:value})', detail: '计数' },
  { name: 'replace', snippet: 'std::replace(${1:vec}.begin(), ${1:vec}.end(), ${2:old}, ${3:new})', detail: '替换' },
  { name: 'unique', snippet: 'std::unique(${1:vec}.begin(), ${1:vec}.end())', detail: '去重（需先排序）' },
  { name: 'nth_element', snippet: 'std::nth_element(${1:vec}.begin(), ${1:vec}.begin() + ${2:k}, ${1:vec}.end())', detail: '第k小元素' },
  { name: 'next_permutation', snippet: 'std::next_permutation(${1:vec}.begin(), ${1:vec}.end())', detail: '下一个排列' },
]

const CPP_IO_FUNCTIONS = [
  { name: 'cout', snippet: 'std::cout << ${1:value} << std::endl', detail: '标准输出换行' },
  { name: 'cin', snippet: 'std::cin >> ${1:var}', detail: '标准输入' },
  { name: 'endl', snippet: 'std::endl', detail: '换行并刷新缓冲区' },
  { name: 'cerr', snippet: 'std::cerr << ${1:error} << std::endl', detail: '标准错误输出' },
  { name: 'getline', snippet: 'std::getline(std::cin, ${1:str})', detail: '读取一行' },
  { name: 'scanf', snippet: 'scanf("${1:%d}", &${2:var})', detail: 'C风格输入' },
  { name: 'printf', snippet: 'printf("${1:%d}\\n", ${2:var})', detail: 'C风格输出' },
]

// C++ 常用代码模板
const CPP_SNIPPETS = [
  { name: 'main', snippet: 'int main() {\n\t${1:// code}\n\treturn 0;\n}', detail: '主函数模板', sortText: '0_main' },
  { name: 'main fastio', snippet: 'int main() {\n\tstd::ios::sync_with_stdio(false);\n\tstd::cin.tie(nullptr);\n\t${1:// code}\n\treturn 0;\n}', detail: '快速IO主函数', sortText: '0_main' },
  { name: 'for', snippet: 'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t${3:// code}\n}', detail: 'for 循环', sortText: '1_for' },
  { name: 'for auto', snippet: 'for (auto& ${1:elem} : ${2:container}) {\n\t${3:// code}\n}', detail: '范围for循环', sortText: '1_for' },
  { name: 'while', snippet: 'while (${1:condition}) {\n\t${2:// code}\n}', detail: 'while 循环', sortText: '1_while' },
  { name: 'if', snippet: 'if (${1:condition}) {\n\t${2:// code}\n}', detail: 'if 语句', sortText: '1_if' },
  { name: 'if-else', snippet: 'if (${1:condition}) {\n\t${2:// code}\n} else {\n\t${3:// code}\n}', detail: 'if-else 语句', sortText: '1_if' },
  { name: 'class', snippet: 'class ${1:Name} {\npublic:\n\t${2:// members}\nprivate:\n\t${3:// private members}\n};', detail: '类定义', sortText: '2_class' },
  { name: 'struct', snippet: 'struct ${1:Name} {\n\t${2:type} ${3:field};\n};', detail: '结构体定义', sortText: '2_struct' },
  { name: 'template function', snippet: 'template<typename ${1:T}>\n${2:T} ${3:function_name}(${4:params}) {\n\t${5:// code}\n}', detail: '模板函数', sortText: '2_func' },
  { name: 'lambda', snippet: 'auto ${1:func} = [](${2:params}) {\n\t${3:// code}\n};', detail: 'Lambda 表达式', sortText: '2_func' },
  { name: 'include bits', snippet: '#include <bits/stdc++.h>\nusing namespace std;', detail: '万能头文件（竞赛用）', sortText: '0_inc' },
  { name: 'include vector', snippet: '#include <vector>', detail: 'vector头文件', sortText: '0_inc' },
  { name: 'include algorithm', snippet: '#include <algorithm>', detail: '算法头文件', sortText: '0_inc' },
  { name: 'include map', snippet: '#include <map>', detail: 'map头文件', sortText: '0_inc' },
]

// ========== Python 语言 ==========
const PYTHON_KEYWORDS = [
  'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
  'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
  'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
  'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
]

const PYTHON_BUILTINS = [
  { name: 'print', snippet: 'print(${1:value})', detail: '打印输出' },
  { name: 'input', snippet: 'input(${1:prompt})', detail: '读取输入' },
  { name: 'len', snippet: 'len(${1:obj})', detail: '获取长度' },
  { name: 'range', snippet: 'range(${1:n})', detail: '生成0到n-1的序列' },
  { name: 'range step', snippet: 'range(${1:start}, ${2:stop}, ${3:step})', detail: '带步长的range' },
  { name: 'int', snippet: 'int(${1:value})', detail: '转换为整数' },
  { name: 'float', snippet: 'float(${1:value})', detail: '转换为浮点数' },
  { name: 'str', snippet: 'str(${1:value})', detail: '转换为字符串' },
  { name: 'list', snippet: 'list(${1:iterable})', detail: '转换为列表' },
  { name: 'dict', snippet: 'dict(${1:iterable})', detail: '创建字典' },
  { name: 'set', snippet: 'set(${1:iterable})', detail: '创建集合' },
  { name: 'tuple', snippet: 'tuple(${1:iterable})', detail: '创建元组' },
  { name: 'sorted', snippet: 'sorted(${1:iterable}, key=${2:None}, reverse=${3:False})', detail: '排序返回新列表' },
  { name: 'reversed', snippet: 'reversed(${1:iterable})', detail: '反转迭代器' },
  { name: 'enumerate', snippet: 'enumerate(${1:iterable}, start=${2:0})', detail: '带索引的枚举' },
  { name: 'zip', snippet: 'zip(${1:iter1}, ${2:iter2})', detail: '并行迭代' },
  { name: 'map', snippet: 'map(${1:func}, ${2:iterable})', detail: '映射函数' },
  { name: 'filter', snippet: 'filter(${1:func}, ${2:iterable})', detail: '过滤元素' },
  { name: 'sum', snippet: 'sum(${1:iterable}, start=${2:0})', detail: '求和' },
  { name: 'max', snippet: 'max(${1:iterable})', detail: '最大值' },
  { name: 'min', snippet: 'min(${1:iterable})', detail: '最小值' },
  { name: 'abs', snippet: 'abs(${1:n})', detail: '绝对值' },
  { name: 'round', snippet: 'round(${1:x}, ${2:ndigits})', detail: '四舍五入' },
  { name: 'pow', snippet: 'pow(${1:x}, ${2:n})', detail: '幂运算' },
  { name: 'open', snippet: 'open(${1:file}, mode="${2:r}")', detail: '打开文件' },
  { name: 'type', snippet: 'type(${1:obj})', detail: '获取类型' },
  { name: 'isinstance', snippet: 'isinstance(${1:obj}, ${2:class})', detail: '检查类型' },
  { name: 'hasattr', snippet: 'hasattr(${1:obj}, "${2:name}")', detail: '检查属性' },
  { name: 'getattr', snippet: 'getattr(${1:obj}, "${2:name}", ${3:default})', detail: '获取属性' },
  { name: 'any', snippet: 'any(${1:iterable})', detail: '任一为True' },
  { name: 'all', snippet: 'all(${1:iterable})', detail: '全部为True' },
]

const PYTHON_STRING_METHODS = [
  { name: 'split', snippet: '${1:str}.split("${2: }")', detail: '分割字符串' },
  { name: 'join', snippet: '"${1: }".join(${2:list})', detail: '连接字符串' },
  { name: 'strip', snippet: '${1:str}.strip()', detail: '去除首尾空白' },
  { name: 'lstrip', snippet: '${1:str}.lstrip()', detail: '去除左侧空白' },
  { name: 'rstrip', snippet: '${1:str}.rstrip()', detail: '去除右侧空白' },
  { name: 'replace', snippet: '${1:str}.replace(${2:old}, ${3:new})', detail: '替换字符串' },
  { name: 'find', snippet: '${1:str}.find(${2:substr})', detail: '查找子串位置' },
  { name: 'upper', snippet: '${1:str}.upper()', detail: '转大写' },
  { name: 'lower', snippet: '${1:str}.lower()', detail: '转小写' },
  { name: 'startswith', snippet: '${1:str}.startswith(${2:prefix})', detail: '检查前缀' },
  { name: 'endswith', snippet: '${1:str}.endswith(${3:suffix})', detail: '检查后缀' },
  { name: 'format', snippet: '${1:str}.format(${2:args})', detail: '格式化字符串' },
]

const PYTHON_LIST_METHODS = [
  { name: 'append', snippet: '${1:list}.append(${2:item})', detail: '末尾添加元素' },
  { name: 'extend', snippet: '${1:list}.extend(${2:iterable})', detail: '扩展列表' },
  { name: 'insert', snippet: '${1:list}.insert(${2:index}, ${3:item})', detail: '插入元素' },
  { name: 'remove', snippet: '${1:list}.remove(${2:value})', detail: '移除第一个匹配项' },
  { name: 'pop', snippet: '${1:list}.pop(${2:index})', detail: '弹出并返回元素' },
  { name: 'index', snippet: '${1:list}.index(${2:value})', detail: '查找元素索引' },
  { name: 'count', snippet: '${1:list}.count(${2:value})', detail: '统计元素出现次数' },
  { name: 'sort', snippet: '${1:list}.sort(reverse=${2:False})', detail: '原地排序' },
  { name: 'reverse', snippet: '${1:list}.reverse()', detail: '原地反转' },
  { name: 'copy', snippet: '${1:list}.copy()', detail: '浅拷贝' },
  { name: 'clear', snippet: '${1:list}.clear()', detail: '清空列表' },
]

// Python 常用代码模板
const PYTHON_SNIPPETS = [
  { name: 'for', snippet: 'for ${1:i} in range(${2:n}):\n    ${3:pass}', detail: 'for 循环', sortText: '1_for' },
  { name: 'for enumerate', snippet: 'for ${1:i}, ${2:item} in enumerate(${3:lst}):\n    ${4:pass}', detail: '带索引的for循环', sortText: '1_for' },
  { name: 'while', snippet: 'while ${1:condition}:\n    ${2:pass}', detail: 'while 循环', sortText: '1_while' },
  { name: 'if', snippet: 'if ${1:condition}:\n    ${2:pass}', detail: 'if 语句', sortText: '1_if' },
  { name: 'if-else', snippet: 'if ${1:condition}:\n    ${2:pass}\nelse:\n    ${3:pass}', detail: 'if-else 语句', sortText: '1_if' },
  { name: 'if-elif-else', snippet: 'if ${1:condition1}:\n    ${2:pass}\nelif ${3:condition2}:\n    ${4:pass}\nelse:\n    ${5:pass}', detail: 'if-elif-else 语句', sortText: '1_if' },
  { name: 'def', snippet: 'def ${1:function_name}(${2:params}):\n    ${3:pass}', detail: '函数定义', sortText: '2_func' },
  { name: 'def with return', snippet: 'def ${1:function_name}(${2:params}) -> ${3:ReturnType}:\n    ${4:pass}\n    return ${5:value}', detail: '带返回类型的函数', sortText: '2_func' },
  { name: 'class', snippet: 'class ${1:ClassName}:\n    def __init__(self${2:, params}):\n        ${3:pass}', detail: '类定义', sortText: '2_class' },
  { name: 'class with methods', snippet: 'class ${1:ClassName}:\n    def __init__(self, ${2:params}):\n        self.${3:attr} = ${4:value}\n    \n    def ${5:method}(self):\n        ${6:pass}', detail: '带方法的类', sortText: '2_class' },
  { name: 'try-except', snippet: 'try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}', detail: '异常处理', sortText: '3_try' },
  { name: 'try-except-finally', snippet: 'try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}\nfinally:\n    ${4:pass}', detail: '完整的异常处理', sortText: '3_try' },
  { name: 'with open', snippet: 'with open(${1:file}, "${2:r}") as f:\n    ${3:data = f.read()}', detail: '文件读取', sortText: '3_file' },
  { name: 'with open write', snippet: 'with open(${1:file}, "${2:w}") as f:\n    f.write(${3:data})', detail: '文件写入', sortText: '3_file' },
  { name: 'list comprehension', snippet: '[${1:x} for ${2:x} in ${3:iterable} if ${4:condition}]', detail: '列表推导式', sortText: '4_comp' },
  { name: 'dict comprehension', snippet: '{${1:k}: ${2:v} for ${3:item} in ${4:iterable}}', detail: '字典推导式', sortText: '4_comp' },
  { name: 'lambda', snippet: 'lambda ${1:params}: ${2:expression}', detail: 'Lambda 表达式', sortText: '2_func' },
  { name: 'input split', snippet: 'input().split()', detail: '读取并分割输入', sortText: '0_io' },
  { name: 'map int input', snippet: 'list(map(int, input().split()))', detail: '读取整数列表', sortText: '0_io' },
  { name: 'import sys', snippet: 'import sys\ninput = sys.stdin.readline', detail: '快速输入（竞赛用）', sortText: '0_imp' },
]

// ========== Java 语言 ==========
const JAVA_KEYWORDS = [
  'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
  'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
  'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
  'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package',
  'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp',
  'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient',
  'try', 'void', 'volatile', 'while', 'true', 'false', 'null'
]

const JAVA_COMMON_CLASSES = [
  { name: 'String', snippet: 'String ${1:str} = "${2:value}"', detail: '字符串' },
  { name: 'Integer', snippet: 'Integer ${1:num} = ${2:value}', detail: '整数包装类' },
  { name: 'Double', snippet: 'Double ${1:num} = ${2:value}', detail: '双精度包装类' },
  { name: 'Boolean', snippet: 'Boolean ${1:bool} = ${2:true}', detail: '布尔包装类' },
  { name: 'ArrayList', snippet: 'ArrayList<${1:Integer}> ${2:list} = new ArrayList<>()', detail: '动态数组' },
  { name: 'LinkedList', snippet: 'LinkedList<${1:Integer}> ${2:list} = new LinkedList<>()', detail: '链表' },
  { name: 'HashMap', snippet: 'HashMap<${1:String}, ${2:Integer}> ${3:map} = new HashMap<>()', detail: '哈希映射' },
  { name: 'HashSet', snippet: 'HashSet<${1:Integer}> ${2:set} = new HashSet<>()', detail: '哈希集合' },
  { name: 'TreeMap', snippet: 'TreeMap<${1:String}, ${2:Integer}> ${3:map} = new TreeMap<>()', detail: '有序映射' },
  { name: 'TreeSet', snippet: 'TreeSet<${1:Integer}> ${2:set} = new TreeSet<>()', detail: '有序集合' },
  { name: 'PriorityQueue', snippet: 'PriorityQueue<${1:Integer}> ${2:pq} = new PriorityQueue<>()', detail: '优先队列（小根堆）' },
  { name: 'PriorityQueue max', snippet: 'PriorityQueue<${1:Integer}> ${2:pq} = new PriorityQueue<>(Collections.reverseOrder())', detail: '大根堆' },
  { name: 'ArrayDeque', snippet: 'ArrayDeque<${1:Integer}> ${2:dq} = new ArrayDeque<>()', detail: '双端队列' },
  { name: 'Stack', snippet: 'Stack<${1:Integer}> ${2:stack} = new Stack<>()', detail: '栈' },
  { name: 'Scanner', snippet: 'Scanner ${1:sc} = new Scanner(System.in)', detail: '输入扫描器' },
  { name: 'BufferedReader', snippet: 'BufferedReader ${1:br} = new BufferedReader(new InputStreamReader(System.in))', detail: '缓冲读取器' },
  { name: 'StringTokenizer', snippet: 'StringTokenizer ${1:st} = new StringTokenizer(${2:br}.readLine())', detail: '字符串分割' },
  { name: 'StringBuilder', snippet: 'StringBuilder ${1:sb} = new StringBuilder()', detail: '可变字符串' },
]

const JAVA_MATH_METHODS = [
  { name: 'Math.max', snippet: 'Math.max(${1:a}, ${2:b})', detail: '最大值' },
  { name: 'Math.min', snippet: 'Math.min(${1:a}, ${2:b})', detail: '最小值' },
  { name: 'Math.abs', snippet: 'Math.abs(${1:n})', detail: '绝对值' },
  { name: 'Math.pow', snippet: 'Math.pow(${1:x}, ${2:n})', detail: '幂运算' },
  { name: 'Math.sqrt', snippet: 'Math.sqrt(${1:x})', detail: '平方根' },
  { name: 'Math.floor', snippet: 'Math.floor(${1:x})', detail: '向下取整' },
  { name: 'Math.ceil', snippet: 'Math.ceil(${1:x})', detail: '向上取整' },
  { name: 'Math.round', snippet: 'Math.round(${1:x})', detail: '四舍五入' },
  { name: 'Math.random', snippet: 'Math.random()', detail: '随机数 [0,1)' },
]

const JAVA_ARRAYS_METHODS = [
  { name: 'Arrays.sort', snippet: 'Arrays.sort(${1:arr})', detail: '数组排序' },
  { name: 'Arrays.sort range', snippet: 'Arrays.sort(${1:arr}, ${2:from}, ${3:to})', detail: '范围排序' },
  { name: 'Arrays.fill', snippet: 'Arrays.fill(${1:arr}, ${2:value})', detail: '填充数组' },
  { name: 'Arrays.copyOf', snippet: 'Arrays.copyOf(${1:arr}, ${2:newLength})', detail: '复制数组' },
  { name: 'Arrays.toString', snippet: 'Arrays.toString(${1:arr})', detail: '数组转字符串' },
  { name: 'Arrays.binarySearch', snippet: 'Arrays.binarySearch(${1:arr}, ${2:key})', detail: '二分查找' },
  { name: 'Arrays.equals', snippet: 'Arrays.equals(${1:arr1}, ${2:arr2})', detail: '数组比较' },
]

const JAVA_COLLECTIONS_METHODS = [
  { name: 'Collections.sort', snippet: 'Collections.sort(${1:list})', detail: '列表排序' },
  { name: 'Collections.sort desc', snippet: 'Collections.sort(${1:list}, Collections.reverseOrder())', detail: '降序排序' },
  { name: 'Collections.reverse', snippet: 'Collections.reverse(${1:list})', detail: '反转列表' },
  { name: 'Collections.shuffle', snippet: 'Collections.shuffle(${1:list})', detail: '随机打乱' },
  { name: 'Collections.max', snippet: 'Collections.max(${1:list})', detail: '最大元素' },
  { name: 'Collections.min', snippet: 'Collections.min(${1:list})', detail: '最小元素' },
  { name: 'Collections.binarySearch', snippet: 'Collections.binarySearch(${1:list}, ${2:key})', detail: '二分查找' },
  { name: 'Collections.frequency', snippet: 'Collections.frequency(${1:list}, ${2:obj})', detail: '统计出现次数' },
]

// Java 常用代码模板
const JAVA_SNIPPETS = [
  { name: 'main', snippet: 'public static void main(String[] args) {\n\t${1:// code}\n}', detail: '主方法', sortText: '0_main' },
  { name: 'class', snippet: 'public class ${1:Main} {\n\t${2:// code}\n}', detail: '类定义', sortText: '0_class' },
  { name: 'class with main', snippet: 'import java.util.*;\n\npublic class ${1:Main} {\n\tpublic static void main(String[] args) {\n\t\tScanner sc = new Scanner(System.in);\n\t\t${2:// code}\n\t}\n}', detail: '完整类模板', sortText: '0_class' },
  { name: 'for', snippet: 'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t${3:// code}\n}', detail: 'for 循环', sortText: '1_for' },
  { name: 'for-each', snippet: 'for (${1:Type} ${2:item} : ${3:collection}) {\n\t${4:// code}\n}', detail: '增强 for 循环', sortText: '1_for' },
  { name: 'while', snippet: 'while (${1:condition}) {\n\t${2:// code}\n}', detail: 'while 循环', sortText: '1_while' },
  { name: 'if', snippet: 'if (${1:condition}) {\n\t${2:// code}\n}', detail: 'if 语句', sortText: '1_if' },
  { name: 'if-else', snippet: 'if (${1:condition}) {\n\t${2:// code}\n} else {\n\t${3:// code}\n}', detail: 'if-else 语句', sortText: '1_if' },
  { name: 'switch', snippet: 'switch (${1:var}) {\n\tcase ${2:value}:\n\t\t${3:// code}\n\t\tbreak;\n\tdefault:\n\t\t${4:// code}\n}', detail: 'switch 语句', sortText: '1_switch' },
  { name: 'try-catch', snippet: 'try {\n\t${1:// code}\n} catch (${2:Exception} e) {\n\t${3:// handle}\n}', detail: '异常处理', sortText: '3_try' },
  { name: 'method', snippet: 'public ${1:void} ${2:methodName}(${3:params}) {\n\t${4:// code}\n}', detail: '方法定义', sortText: '2_method' },
  { name: 'private method', snippet: 'private ${1:void} ${2:methodName}(${3:params}) {\n\t${4:// code}\n}', detail: '私有方法', sortText: '2_method' },
  { name: 'static method', snippet: 'public static ${1:void} ${2:methodName}(${3:params}) {\n\t${4:// code}\n}', detail: '静态方法', sortText: '2_method' },
  { name: 'println', snippet: 'System.out.println(${1:value})', detail: '打印输出', sortText: '0_io' },
  { name: 'printf', snippet: 'System.out.printf("${1:%d}\\n", ${2:value})', detail: '格式化输出', sortText: '0_io' },
  { name: 'next', snippet: 'sc.next()', detail: '读取字符串', sortText: '0_io' },
  { name: 'nextInt', snippet: 'sc.nextInt()', detail: '读取整数', sortText: '0_io' },
  { name: 'nextLine', snippet: 'sc.nextLine()', detail: '读取一行', sortText: '0_io' },
]

// ========== Rust 语言 ==========
const RUST_KEYWORDS = [
  'as', 'async', 'await', 'break', 'const', 'continue', 'crate', 'dyn', 'else',
  'enum', 'extern', 'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop',
  'match', 'mod', 'move', 'mut', 'pub', 'ref', 'return', 'self', 'Self', 'static',
  'struct', 'super', 'trait', 'true', 'type', 'unsafe', 'use', 'where', 'while'
]

const RUST_COMMON_FUNCTIONS = [
  { name: 'println!', snippet: 'println!("${1:{}"}", ${2:value})', detail: '打印输出并换行' },
  { name: 'print!', snippet: 'print!("${1:{}"}", ${2:value})', detail: '打印输出（无换行）' },
  { name: 'format!', snippet: 'format!("${1:{}"}", ${2:value})', detail: '格式化字符串' },
  { name: 'eprintln!', snippet: 'eprintln!("${1:{}"}", ${2:value})', detail: '标准错误输出' },
  { name: 'vec!', snippet: 'vec![${1:elements}]', detail: '创建向量' },
  { name: 'vec![n]', snippet: 'vec![${1:0}; ${2:n}]', detail: '创建n个相同元素的向量' },
  { name: 'String::from', snippet: 'String::from("${1:value}")', detail: '创建String' },
  { name: 'String::new', snippet: 'String::new()', detail: '创建空String' },
  { name: 'Vec::new', snippet: 'Vec::<${1:T}>::new()', detail: '创建空向量' },
  { name: 'Vec::with_capacity', snippet: 'Vec::<${1:T}>::with_capacity(${2:n})', detail: '预分配容量' },
  { name: 'HashMap::new', snippet: 'HashMap::<${1:K}, ${2:V}>::new()', detail: '创建空HashMap' },
  { name: 'HashSet::new', snippet: 'HashSet::<${1:T}>::new()', detail: '创建空HashSet' },
  { name: 'push', snippet: '${1:vec}.push(${2:value})', detail: '添加元素' },
  { name: 'pop', snippet: '${1:vec}.pop()', detail: '移除并返回末尾元素' },
  { name: 'len', snippet: '${1:collection}.len()', detail: '获取长度' },
  { name: 'is_empty', snippet: '${1:collection}.is_empty()', detail: '检查是否为空' },
  { name: 'iter', snippet: '${1:collection}.iter()', detail: '获取不可变迭代器' },
  { name: 'iter_mut', snippet: '${1:collection}.iter_mut()', detail: '获取可变迭代器' },
  { name: 'into_iter', snippet: '${1:collection}.into_iter()', detail: '获取消费迭代器' },
  { name: 'collect', snippet: '.collect::<${1:Vec<_>}>()', detail: '收集为集合' },
  { name: 'map', snippet: '.map(|${1:x}| ${2:x})', detail: '映射变换' },
  { name: 'filter', snippet: '.filter(|${1:x}| ${2:true})', detail: '过滤' },
  { name: 'fold', snippet: '.fold(${1:init}, |${2:acc}, ${3:x}| ${4:acc})', detail: '折叠' },
  { name: 'take', snippet: '.take(${1:n})', detail: '取前n个元素' },
  { name: 'skip', snippet: '.skip(${1:n})', detail: '跳过前n个元素' },
  { name: 'enumerate', snippet: '.enumerate()', detail: '带索引枚举' },
  { name: 'zip', snippet: '.zip(${1:other})', detail: '并行迭代' },
  { name: 'sort', snippet: '${1:vec}.sort()', detail: '原地排序' },
  { name: 'sort_by', snippet: '${1:vec}.sort_by(|a, b| ${2:a.cmp(b)})', detail: '自定义排序' },
  { name: 'reverse', snippet: '${1:vec}.reverse()', detail: '原地反转' },
  { name: 'clone', snippet: '${1:value}.clone()', detail: '克隆' },
  { name: 'copy', snippet: '${1:value}.copy()', detail: '复制' },
]

const RUST_SNIPPETS = [
  { name: 'fn main', snippet: 'fn main() {\n\t${1:// code}\n}', detail: '主函数', sortText: '0_main' },
  { name: 'fn', snippet: 'fn ${1:name}(${2:params}) -> ${3:ReturnType} {\n\t${4:// code}\n}', detail: '函数定义', sortText: '2_func' },
  { name: 'fn generic', snippet: 'fn ${1:name}<${2:T}>(${3:params}) -> ${4:T} {\n\t${5:// code}\n}', detail: '泛型函数', sortText: '2_func' },
  { name: 'pub fn', snippet: 'pub fn ${1:name}(${2:params}) -> ${3:ReturnType} {\n\t${4:// code}\n}', detail: '公开函数', sortText: '2_func' },
  { name: 'struct', snippet: 'struct ${1:Name} {\n\t${2:field}: ${3:Type},\n}', detail: '结构体定义', sortText: '2_struct' },
  { name: 'struct tuple', snippet: 'struct ${1:Name}(${2:Type}, ${3:Type});', detail: '元组结构体', sortText: '2_struct' },
  { name: 'struct unit', snippet: 'struct ${1:Name};', detail: '单元结构体', sortText: '2_struct' },
  { name: 'enum', snippet: 'enum ${1:Name} {\n\t${2:Variant1},\n\t${3:Variant2},\n}', detail: '枚举定义', sortText: '2_enum' },
  { name: 'impl', snippet: 'impl ${1:Type} {\n\t${2:// methods}\n}', detail: '实现块', sortText: '2_impl' },
  { name: 'impl trait', snippet: 'impl ${1:Trait} for ${2:Type} {\n\t${3:// methods}\n}', detail: '实现trait', sortText: '2_impl' },
  { name: 'trait', snippet: 'trait ${1:Name} {\n\t${2:// methods}\n}', detail: 'trait定义', sortText: '2_trait' },
  { name: 'match', snippet: 'match ${1:value} {\n\t${2:pattern} => ${3:expression},\n\t_ => ${4:default},\n}', detail: '模式匹配', sortText: '1_match' },
  { name: 'match Option', snippet: 'match ${1:option} {\n\tSome(x) => ${2:// handle Some},\n\tNone => ${3:// handle None},\n}', detail: 'Option匹配', sortText: '1_match' },
  { name: 'match Result', snippet: 'match ${1:result} {\n\tOk(x) => ${2:// handle Ok},\n\tErr(e) => ${3:// handle Err},\n}', detail: 'Result匹配', sortText: '1_match' },
  { name: 'if let', snippet: 'if let ${1:Some(x)} = ${2:option} {\n\t${3:// code}\n}', detail: 'if let模式', sortText: '1_match' },
  { name: 'while let', snippet: 'while let ${1:Some(x)} = ${2:iterator.next()} {\n\t${3:// code}\n}', detail: 'while let模式', sortText: '1_match' },
  { name: 'for', snippet: 'for ${1:i} in 0..${2:n} {\n\t${3:// code}\n}', detail: 'for 循环', sortText: '1_for' },
  { name: 'for in', snippet: 'for ${1:item} in ${2:iterable} {\n\t${3:// code}\n}', detail: '迭代循环', sortText: '1_for' },
  { name: 'loop', snippet: 'loop {\n\t${1:// code}\n\tif ${2:condition} {\n\t\tbreak;\n\t}\n}', detail: '无限循环', sortText: '1_loop' },
  { name: 'while', snippet: 'while ${1:condition} {\n\t${2:// code}\n}', detail: 'while 循环', sortText: '1_while' },
  { name: 'if', snippet: 'if ${1:condition} {\n\t${2:// code}\n}', detail: 'if 语句', sortText: '1_if' },
  { name: 'if-else', snippet: 'if ${1:condition} {\n\t${2:// code}\n} else {\n\t${3:// code}\n}', detail: 'if-else 语句', sortText: '1_if' },
  { name: 'use std', snippet: 'use std::${1:collection}::${2:HashMap};', detail: '导入标准库', sortText: '0_use' },
  { name: 'use crate', snippet: 'use crate::${1:module}::${2:item};', detail: '导入crate模块', sortText: '0_use' },
  { name: 'Option Some', snippet: 'Some(${1:value})', detail: 'Option::Some', sortText: '3_option' },
  { name: 'Option None', snippet: 'None', detail: 'Option::None', sortText: '3_option' },
  { name: 'Result Ok', snippet: 'Ok(${1:value})', detail: 'Result::Ok', sortText: '3_result' },
  { name: 'Result Err', snippet: 'Err(${1:error})', detail: 'Result::Err', sortText: '3_result' },
  { name: 'unwrap', snippet: '${1:option}.unwrap()', detail: '解包Option/Result' },
  { name: 'unwrap_or', snippet: '${1:option}.unwrap_or(${2:default})', detail: '解包或默认值' },
  { name: 'expect', snippet: '${1:option}.expect("${2:message}")', detail: '解包并panic' },
  { name: '? operator', snippet: '${1:result}?', detail: '错误传播操作符', sortText: '3_result' },
]

// ========================================
// Phase 2: 变量名补全 - 分析当前文件
// ========================================

interface VariableInfo {
  name: string
  type: 'variable' | 'function' | 'class' | 'constant'
  line: number
}

/**
 * 从代码中提取变量、函数、类名
 */
function extractSymbolsFromCode(code: string, language: string): VariableInfo[] {
  const symbols: VariableInfo[] = []
  const lines = code.split('\n')

  switch (language) {
    case 'c':
    case 'cpp':
      // 匹配变量声明: int x, float y, string name
      lines.forEach((line, idx) => {
        // 匹配函数定义: type name(...) {
        const funcMatch = line.match(/^\s*(?:inline\s+)?(?:static\s+)?(?:const\s+)?(\w+(?:\s*[*&])?)\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{?/)
        if (funcMatch) {
          symbols.push({ name: funcMatch[2], type: 'function', line: idx + 1 })
        }
        // 匹配变量: int x = 或 type x;
        const varMatch = line.match(/^\s*(?:const\s+)?(\w+(?:\s*[*&])?)\s+(\w+)\s*(?:=|;)/)
        if (varMatch && !['if', 'for', 'while', 'switch', 'return', 'break', 'continue', 'else'].includes(varMatch[2])) {
          symbols.push({ name: varMatch[2], type: 'variable', line: idx + 1 })
        }
        // 匹配 #define 常量
        const defineMatch = line.match(/^\s*#define\s+(\w+)/)
        if (defineMatch) {
          symbols.push({ name: defineMatch[1], type: 'constant', line: idx + 1 })
        }
      })
      break

    case 'python':
      lines.forEach((line, idx) => {
        // 匹配函数定义: def name(...
        const funcMatch = line.match(/^\s*def\s+(\w+)\s*\(/)
        if (funcMatch) {
          symbols.push({ name: funcMatch[1], type: 'function', line: idx + 1 })
        }
        // 匹配类定义: class Name:
        const classMatch = line.match(/^\s*class\s+(\w+)/)
        if (classMatch) {
          symbols.push({ name: classMatch[1], type: 'class', line: idx + 1 })
        }
        // 匹配变量: name = 或 name:
        const varMatch = line.match(/^\s*(\w+)\s*[=:]/)
        if (varMatch && !['def', 'class', 'if', 'for', 'while', 'with', 'try', 'except', 'elif', 'else'].includes(varMatch[1])) {
          symbols.push({ name: varMatch[1], type: 'variable', line: idx + 1 })
        }
        // 匹配常量: NAME =
        const constMatch = line.match(/^\s*([A-Z][A-Z0-9_]*)\s*=/)
        if (constMatch) {
          symbols.push({ name: constMatch[1], type: 'constant', line: idx + 1 })
        }
      })
      break

    case 'java':
      lines.forEach((line, idx) => {
        // 匹配方法定义: public/private/protected type name(
        const methodMatch = line.match(/^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(\w+)\s+(\w+)\s*\(/)
        if (methodMatch && !['if', 'for', 'while', 'switch', 'catch', 'class', 'interface'].includes(methodMatch[2])) {
          symbols.push({ name: methodMatch[2], type: 'function', line: idx + 1 })
        }
        // 匹配类定义: class Name
        const classMatch = line.match(/^\s*(?:public\s+)?class\s+(\w+)/)
        if (classMatch) {
          symbols.push({ name: classMatch[1], type: 'class', line: idx + 1 })
        }
        // 匹配变量: type name = 或 type name;
        const varMatch = line.match(/^\s*(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*[=;]/)
        if (varMatch && !['if', 'for', 'while', 'switch', 'catch', 'class', 'interface', 'return', 'new'].includes(varMatch[2])) {
          symbols.push({ name: varMatch[2], type: 'variable', line: idx + 1 })
        }
        // 匹配常量: static final TYPE NAME
        const constMatch = line.match(/^\s*(?:public\s+)?static\s+final\s+\w+\s+([A-Z][A-Z0-9_]*)/)
        if (constMatch) {
          symbols.push({ name: constMatch[1], type: 'constant', line: idx + 1 })
        }
      })
      break

    case 'rust':
      lines.forEach((line, idx) => {
        // 匹配函数定义: fn name(
        const funcMatch = line.match(/^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)/)
        if (funcMatch) {
          symbols.push({ name: funcMatch[1], type: 'function', line: idx + 1 })
        }
        // 匹配结构体: struct Name
        const structMatch = line.match(/^\s*(?:pub\s+)?struct\s+(\w+)/)
        if (structMatch) {
          symbols.push({ name: structMatch[1], type: 'class', line: idx + 1 })
        }
        // 匹配枚举: enum Name
        const enumMatch = line.match(/^\s*(?:pub\s+)?enum\s+(\w+)/)
        if (enumMatch) {
          symbols.push({ name: enumMatch[1], type: 'class', line: idx + 1 })
        }
        // 匹配变量: let name = 或 let mut name =
        const varMatch = line.match(/^\s*let\s+(?:mut\s+)?(\w+)/)
        if (varMatch) {
          symbols.push({ name: varMatch[1], type: 'variable', line: idx + 1 })
        }
        // 匹配常量: const NAME
        const constMatch = line.match(/^\s*(?:pub\s+)?const\s+([A-Z][A-Z0-9_]*)/)
        if (constMatch) {
          symbols.push({ name: constMatch[1], type: 'constant', line: idx + 1 })
        }
        // 匹配静态变量: static NAME
        const staticMatch = line.match(/^\s*(?:pub\s+)?static\s+(\w+)/)
        if (staticMatch) {
          symbols.push({ name: staticMatch[1], type: 'constant', line: idx + 1 })
        }
      })
      break
  }

  // 去重
  const seen = new Set<string>()
  return symbols.filter(s => {
    if (seen.has(s.name)) return false
    seen.add(s.name)
    return true
  })
}

// ========================================
// 补全提供者注册
// ========================================

const registeredLanguages = new Set<string>()

function getCompletionKind(monaco: typeof import('monaco-editor'), type: string) {
  switch (type) {
    case 'function': return monaco.languages.CompletionItemKind.Function
    case 'class': return monaco.languages.CompletionItemKind.Class
    case 'constant': return monaco.languages.CompletionItemKind.Constant
    default: return monaco.languages.CompletionItemKind.Variable
  }
}

function registerCompletionProviders(monaco: typeof import('monaco-editor')) {
  // ========== C 语言 ==========
  if (!registeredLanguages.has('c')) {
    monaco.languages.registerCompletionItemProvider('c', {
      triggerCharacters: ['.', '>', ' ', '(', '#'],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        }

        // Phase 2: 提取当前文件中的符号
        const code = model.getValue()
        const symbols = extractSymbolsFromCode(code, 'c')

        const suggestions = [
          // Phase 2: 当前文件的变量和函数
          ...symbols.map(s => ({
            label: s.name,
            kind: getCompletionKind(monaco, s.type),
            insertText: s.name,
            range,
            detail: `${s.type} (line ${s.line})`,
            sortText: `0_${s.name}`, // 本地符号优先级最高
          })),
          // 代码模板
          ...C_SNIPPETS.map(s => ({
            label: s.name,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: s.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: s.detail,
            sortText: s.sortText,
          })),
          // 关键字
          ...C_KEYWORDS.map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
            detail: '关键字',
            sortText: `5_${kw}`,
          })),
          // 标准库函数
          ...[...C_STDIO_FUNCTIONS, ...C_STDLIB_FUNCTIONS, ...C_STRING_FUNCTIONS, ...C_MATH_FUNCTIONS].map(fn => ({
            label: fn.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: fn.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: fn.detail,
            documentation: fn.detail,
            sortText: `3_${fn.name}`,
          })),
        ]

        return { suggestions }
      }
    })
    registeredLanguages.add('c')
  }

  // ========== C++ ==========
  if (!registeredLanguages.has('cpp')) {
    monaco.languages.registerCompletionItemProvider('cpp', {
      triggerCharacters: ['.', '>', ' ', '(', '<', ':', '#'],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        }

        const code = model.getValue()
        const symbols = extractSymbolsFromCode(code, 'cpp')

        const suggestions = [
          // 当前文件的符号
          ...symbols.map(s => ({
            label: s.name,
            kind: getCompletionKind(monaco, s.type),
            insertText: s.name,
            range,
            detail: `${s.type} (line ${s.line})`,
            sortText: `0_${s.name}`,
          })),
          // C++ 代码模板
          ...CPP_SNIPPETS.map(s => ({
            label: s.name,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: s.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: s.detail,
            sortText: s.sortText,
          })),
          // STL 容器
          ...CPP_STL_CONTAINERS.map(c => ({
            label: c.name,
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: c.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: c.detail,
            sortText: `2_${c.name}`,
          })),
          // STL 算法
          ...CPP_ALGORITHMS.map(a => ({
            label: a.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: a.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: a.detail,
            sortText: `2_${a.name}`,
          })),
          // IO 函数
          ...CPP_IO_FUNCTIONS.map(fn => ({
            label: fn.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: fn.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: fn.detail,
            sortText: `3_${fn.name}`,
          })),
          // 关键字
          ...CPP_KEYWORDS.map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
            detail: '关键字',
            sortText: `5_${kw}`,
          })),
          // C 标准库函数
          ...[...C_STDIO_FUNCTIONS, ...C_STDLIB_FUNCTIONS, ...C_STRING_FUNCTIONS, ...C_MATH_FUNCTIONS].map(fn => ({
            label: fn.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: fn.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: fn.detail,
            sortText: `4_${fn.name}`,
          })),
        ]

        return { suggestions }
      }
    })
    registeredLanguages.add('cpp')
  }

  // ========== Python ==========
  if (!registeredLanguages.has('python')) {
    monaco.languages.registerCompletionItemProvider('python', {
      triggerCharacters: ['.', ' ', '(', '[', ':', '"', "'"],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        }

        const code = model.getValue()
        const symbols = extractSymbolsFromCode(code, 'python')

        const suggestions = [
          // 当前文件的符号
          ...symbols.map(s => ({
            label: s.name,
            kind: getCompletionKind(monaco, s.type),
            insertText: s.name,
            range,
            detail: `${s.type} (line ${s.line})`,
            sortText: `0_${s.name}`,
          })),
          // Python 代码模板
          ...PYTHON_SNIPPETS.map(s => ({
            label: s.name,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: s.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: s.detail,
            sortText: s.sortText,
          })),
          // 内置函数
          ...PYTHON_BUILTINS.map(fn => ({
            label: fn.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: fn.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: fn.detail,
            sortText: `2_${fn.name}`,
          })),
          // 字符串方法
          ...PYTHON_STRING_METHODS.map(m => ({
            label: m.name,
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: m.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: m.detail,
            sortText: `3_${m.name}`,
          })),
          // 列表方法
          ...PYTHON_LIST_METHODS.map(m => ({
            label: m.name,
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: m.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: m.detail,
            sortText: `3_${m.name}`,
          })),
          // 关键字
          ...PYTHON_KEYWORDS.map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
            detail: '关键字',
            sortText: `5_${kw}`,
          })),
        ]

        return { suggestions }
      }
    })
    registeredLanguages.add('python')
  }

  // ========== Java ==========
  if (!registeredLanguages.has('java')) {
    monaco.languages.registerCompletionItemProvider('java', {
      triggerCharacters: ['.', ' ', '(', '<', '"'],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        }

        const code = model.getValue()
        const symbols = extractSymbolsFromCode(code, 'java')

        const suggestions = [
          // 当前文件的符号
          ...symbols.map(s => ({
            label: s.name,
            kind: getCompletionKind(monaco, s.type),
            insertText: s.name,
            range,
            detail: `${s.type} (line ${s.line})`,
            sortText: `0_${s.name}`,
          })),
          // Java 代码模板
          ...JAVA_SNIPPETS.map(s => ({
            label: s.name,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: s.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: s.detail,
            sortText: s.sortText,
          })),
          // 常用类
          ...JAVA_COMMON_CLASSES.map(c => ({
            label: c.name,
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: c.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: c.detail,
            sortText: `2_${c.name}`,
          })),
          // Math 方法
          ...JAVA_MATH_METHODS.map(m => ({
            label: m.name,
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: m.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: m.detail,
            sortText: `3_${m.name}`,
          })),
          // Arrays 方法
          ...JAVA_ARRAYS_METHODS.map(m => ({
            label: m.name,
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: m.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: m.detail,
            sortText: `3_${m.name}`,
          })),
          // Collections 方法
          ...JAVA_COLLECTIONS_METHODS.map(m => ({
            label: m.name,
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: m.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: m.detail,
            sortText: `3_${m.name}`,
          })),
          // 关键字
          ...JAVA_KEYWORDS.map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
            detail: '关键字',
            sortText: `5_${kw}`,
          })),
        ]

        return { suggestions }
      }
    })
    registeredLanguages.add('java')
  }

  // ========== Rust ==========
  if (!registeredLanguages.has('rust')) {
    monaco.languages.registerCompletionItemProvider('rust', {
      triggerCharacters: ['.', ' ', '(', ':', '!', '<', '#'],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        }

        const code = model.getValue()
        const symbols = extractSymbolsFromCode(code, 'rust')

        const suggestions = [
          // 当前文件的符号
          ...symbols.map(s => ({
            label: s.name,
            kind: getCompletionKind(monaco, s.type),
            insertText: s.name,
            range,
            detail: `${s.type} (line ${s.line})`,
            sortText: `0_${s.name}`,
          })),
          // Rust 代码模板
          ...RUST_SNIPPETS.map(s => ({
            label: s.name,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: s.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: s.detail,
            sortText: s.sortText,
          })),
          // 常用函数和宏
          ...RUST_COMMON_FUNCTIONS.map(fn => ({
            label: fn.name,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: fn.snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
            detail: fn.detail,
            sortText: `2_${fn.name}`,
          })),
          // 关键字
          ...RUST_KEYWORDS.map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
            detail: '关键字',
            sortText: `5_${kw}`,
          })),
        ]

        return { suggestions }
      }
    })
    registeredLanguages.add('rust')
  }
}

// ========================================
// 主组件
// ========================================

export function CodeEditorPanel({
  value,
  onChange,
  language = 'c',
  readOnly = false,
  height = '100%',
}: CodeEditorPanelProps) {
  const editorRef = useRef<import('monaco-editor').editor.IStandaloneCodeEditor | null>(null)
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null)

  const handleEditorChange = useCallback((val: string | undefined) => {
    onChange(val || '')
  }, [onChange])

  const handleEditorMount = (editor: import('monaco-editor').editor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor')) => {
    editorRef.current = editor
    monacoRef.current = monaco

    // 注册所有语言的补全提供者
    registerCompletionProviders(monaco)

    // 浅色主题
    monaco.editor.defineTheme('light-custom', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955' },
        { token: 'keyword', foreground: 'AF00DB' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: '098658' },
        { token: 'type', foreground: '008080' },
        { token: 'function', foreground: '795E26' },
        { token: 'variable', foreground: '001080' },
      ],
      colors: {
        'editor.background': '#FFFFFF',
        'editor.foreground': '#303133',
        'editor.lineHighlightBackground': '#F5F7FA',
        'editorCursor.foreground': '#3498DB',
        'editor.selectionBackground': '#3498DB30',
        'editorLineNumber.foreground': '#C0C4CC',
        'editorLineNumber.activeForeground': '#909399',
        'editorIndentGuide.background': '#EBEEF5',
        'editorIndentGuide.activeBackground': '#DCDFE6',
        'editorSuggestWidget.background': '#FFFFFF',
        'editorSuggestWidget.border': '#E4E7ED',
        'editorSuggestWidget.selectedBackground': '#F5F7FA',
        'editorSuggestWidget.highlightForeground': '#3498DB',
      },
    })
    monaco.editor.setTheme('light-custom')

    editor.updateOptions({ automaticLayout: true })
    editor.focus()
  }

  useEffect(() => {
    editorRef.current?.focus()
  }, [])

  return (
    <div className="h-full bg-white">
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorMount}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'JetBrains Mono, Monaco, Consolas, monospace',
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 16, bottom: 16 },
          tabSize: 4,
          insertSpaces: true,
          wordWrap: 'on',
          scrollbar: {
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
          },
          // ========== 补全增强 ==========
          quickSuggestions: {
            other: 'inline',
            comments: false,
            strings: true,
          },
          suggest: {
            showKeywords: true,
            showSnippets: true,
            showClasses: true,
            showFunctions: true,
            showVariables: true,
            showModules: true,
            showProperties: true,
            showMethods: true,
            showConstructors: true,
            showEnums: true,
            showEnumMembers: true,
            showConstants: true,
            preview: true,
            snippetsPreventQuickSuggestions: false,
            localityBonus: true,
            shareSuggestSelections: true,
          },
          parameterHints: {
            enabled: true,
            cycle: true,
          },
          autoClosingBrackets: 'always',
          autoClosingQuotes: 'always',
          autoClosingDelete: 'always',
          autoClosingOvertype: 'always',
          autoSurround: 'languageDefined',
          tabCompletion: 'on',
          wordBasedSuggestions: 'allDocuments',
          snippetSuggestions: 'top',
          acceptSuggestionOnEnter: 'on',
          acceptSuggestionOnCommitCharacter: true,
          formatOnPaste: true,
          formatOnType: true,
          bracketPairColorization: {
            enabled: true,
          },
          folding: true,
          foldingHighlight: true,
          foldingStrategy: 'auto',
          showFoldingControls: 'mouseover',
          hover: {
            enabled: true,
            delay: 300,
            sticky: true,
          },
          definitionLinkOpensInPeek: false,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          renderWhitespace: 'selection',
          guides: {
            bracketPairs: true,
            indentation: true,
            highlightActiveIndentation: true,
          },
          links: true,
          colorDecorators: true,
          renderLineHighlight: 'all',
          suggestOnTriggerCharacters: true,
          quickSuggestionsDelay: 50, // 更快的建议延迟
          inlineSuggest: {
            enabled: true,
          },
        }}
        theme="vs"
        loading={
          <div className="flex items-center justify-center h-full text-[#909399]">
            <div className="animate-pulse">{/* Loading state */}</div>
          </div>
        }
      />
    </div>
  )
}
