# LibreOJ 题库下载指南

本指南说明如何从 LibreOJ (LOJ) 下载题目（包含测试数据）到本系统。

## 为什么选择 LibreOJ？

| 特性 | LibreOJ | Codeforces | TK题库 |
|------|---------|------------|--------|
| 官方API | ✅ 有 | ✅ 有 | ❌ 无 |
| 测试数据 | ✅ 完整下载 | ❌ API不提供 | ✅ 有 |
| 题目数量 | 3000+ | 11000+ | ~1000 |
| 题目质量 | 高（中文为主） | 极高（英文为主） | 中等 |
| 难度分级 | ✅ 有 | ✅ 有rating | 部分有 |
| 法律风险 | 无（官方API） | 无 | 爬虫风险 |

## 1. 快速开始

### 下载单个题目

```bash
cd backend

# 下载题目 #1（包含测试数据）
python -m app.scripts.loj_downloader --problem 1

# 指定保存目录
python -m app.scripts.loj_downloader --problem 1 --output my_problems
```

### 下载多个题目

```bash
# 下载指定编号的题目
python -m app.scripts.loj_downloader --problems 1 2 3 4 5

# 下载一个范围的题目
python -m app.scripts.loj_downloader --range 1 100

# 限制下载数量
python -m app.scripts.loj_downloader --range 1 100 --limit 10
```

### 导入到数据库

```bash
# 下载并导入到数据库
python -m app.scripts.loj_downloader --problems 1 2 3 --import

# 指定课程
python -m app.scripts.loj_downloader --range 1 50 --import --course DSA
```

## 2. 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--problem` | `-p` | 下载单个题目 |
| `--problems` | | 下载多个指定题目 |
| `--range` | | 下载一个范围（起始 结束） |
| `--import` | | 导入到数据库 |
| `--course` | | 指定课程（C/CPP/Python/Java/Rust/DSA/ADA/DiscreteMath） |
| `--output` | `-o` | 保存目录 |
| `--limit` | `-l` | 限制下载数量 |

## 3. 下载的内容

每个题目会下载以下内容：

```
downloads/loj/{pid}/
├── problem.json      # 完整题目信息（API返回）
└── testdata/         # 测试数据目录
    ├── 1.in          # 测试输入 1
    ├── 1.out         # 测试输出 1
    ├── 2.in
    ├── 2.out
    └── ...           # 更多测试用例
```

### problem.json 包含

- 题目标题（中英文）
- 题目描述
- 输入/输出格式
- 样例
- 时间/内存限制
- 标签
- 提交/通过数量

## 4. 测试用例解析

系统会自动解析测试用例：

1. 识别 `.in` 和 `.out`/`.ans` 文件
2. 按编号配对（如 `1.in` ↔ `1.out`）
3. 转换为标准格式存入数据库

```json
{
  "input": "1 2\n",
  "output": "3\n",
  "name": "test_1"
}
```

## 5. 难度估算

由于 LOJ 不提供 rating，系统根据通过率估算难度：

| 通过率 | 难度等级 |
|--------|----------|
| >= 60% | 1 (入门) |
| 40-60% | 2 (初级) |
| 20-40% | 3 (中等) |
| 10-20% | 4 (困难) |
| < 10% | 5 (专家) |

## 6. 推荐用法

### 场景一：导入入门题目

```bash
# 下载前 50 题作为入门题
python -m app.scripts.loj_downloader --range 1 50 --import --course C
```

### 场景二：导入算法练习题

```bash
# 根据题目标签选择
# 需要先在 LOJ 网站上查找相关题目编号
python -m app.scripts.loj_downloader --problems 100 101 102 103 --import --course DSA
```

### 场景三：批量下载后筛选

```bash
# 下载 1-100 题
python -m app.scripts.loj_downloader --range 1 100 --output my_problems

# 人工筛选后再导入
python -m app.scripts.loj_downloader --problems [筛选后的编号] --import
```

## 7. 代码中使用

```python
import asyncio
from app.scripts.loj_downloader import download_problem, import_problems

async def main():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # 下载单个题目
        result = await download_problem(session, 1)
        
        if result:
            print(f"Got {len(result['test_cases'])} test cases")
            
            # 导入到数据库
            stats = await import_problems([result], course_code="DSA")
            print(f"Imported: {stats['imported']}")

asyncio.run(main())
```

## 8. 注意事项

### API 限制
- 每次请求间隔 0.5 秒
- 请勿大量并发请求

### 测试数据
- 部分题目可能有图片附件
- 图片会保存到 testdata 目录
- 系统会自动过滤非测试文件

### 字符编码
- LOJ 题目以中文为主
- 测试数据使用 UTF-8 编码
- 系统自动处理编码转换

## 9. 常见问题

**Q: 为什么有些题目下载失败？**

A: 可能原因：
- 题目不存在或已删除
- 网络连接问题
- API 临时不可用

**Q: 测试用例数量为 0 怎么办？**

A: 部分题目可能：
- 没有上传测试数据
- 测试数据格式特殊
- 需要手动从题目页面获取

**Q: 如何获取题目的标签信息？**

A: 系统会自动获取 LOJ 的标签并存入 `knowledge_points` 字段。

---

**LOJ 官网**: https://loj.ac

**API 参考**: https://github.com/hydro-dev/loj-download
