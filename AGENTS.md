# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

# AIcodiingTeach - 基于GAI的程序设计类课程实践教学系统

## 项目概述

本项目是一个基于生成式AI(GAI)的编程教学平台，旨在解决：
- 实践教学个性化不足
- 理论和实践不协同
- 实时交互性不足
- 打榜激励不足

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **数据库**: SQLite + SQLAlchemy (async) with aiosqlite
- **AI**: 支持多 Provider (OpenAI, 本地模型等) - 通过 `app/services/ai.py` 配置
- **认证**: JWT Token (python-jose)
- **验证**: Pydantic v2
- **测试**: pytest + pytest-asyncio + httpx

### 前端
- **框架**: Next.js 16 (App Router) + React 19
- **语言**: TypeScript
- **样式**: Tailwind CSS 4
- **代码编辑器**: Monaco Editor (@monaco-editor/react)
- **测试**: Jest + @testing-library/react
- **包管理**: pnpm (推荐)

## 支持的课程

1. C语言程序设计
2. C++程序设计
3. Python程序设计
4. Java程序设计
5. Rust程序设计
6. 数据结构与算法
7. 算法设计与分析
8. 离散数学

## 核心功能

### 1. 用户认证
- 注册/登录/登出
- JWT Token 认证
- 用户画像管理

### 2. 课程学习
- 课程选择与进度追踪
- 关卡式学习路径
- AI个性化内容生成

### 3. 在线实践
- Monaco 代码编辑器
- 实时代码运行反馈（Judge0）
- 练习题两种来源：TK题库 / AI生成

### 4. 闯关验证
- 每关完成后的验证题目
- AI生成验证题，按练习题难度加权
- 学习目标达成评估

### 5. AI配额控制
- 配额限制防止过度依赖
- 配额使用记录追踪
- 配额获取途径

### 6. 统计分析
- 学习进度统计
- 正确率分析
- 排行榜系统
- 成就系统

## 架构说明

### 后端架构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口，路由注册，中间件配置
│   ├── config.py            # Pydantic Settings 配置管理
│   ├── database.py          # SQLAlchemy async 引擎和会话
│   ├── middleware.py        # 速率限制中间件
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── user.py          # 用户模型
│   │   ├── course.py        # 课程模型
│   │   ├── chapter.py       # 章节模型
│   │   ├── exercise.py      # 练习题模型
│   │   ├── stage.py         # 关卡模型
│   │   ├── challenge.py     # 挑战模式
│   │   └── ...              # 其他模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── routers/             # API 路由端点
│   ├── services/            # 业务逻辑层
│   ├── utils/               # 工具函数（安全、依赖注入）
│   └── providers/           # AI Provider 抽象
├── tests/
│   ├── conftest.py          # pytest 配置，共享 fixtures
│   └── test_*.py            # 测试文件
└── init_db.py               # 数据库初始化脚本
```

**关键依赖注入**: `app/utils/deps.py` 提供了 `get_db` 和 `get_current_user` 依赖

**模型关系**:
- Course → Chapter → Exercise（课程层级）
- Stage → UserStageProgress（关卡进度）
- Challenge → UserChallenge（挑战记录）
- UserWeakPoint + SpacedRepetition（错题本与间隔复习）

### 前端架构

```
frontend/
├── app/                     # Next.js App Router 页面
│   ├── login/page.tsx       # 登录页
│   ├── register/page.tsx    # 注册页
│   ├── dashboard/page.tsx   # 仪表盘
│   ├── courses/[id]/        # 课程详情
│   ├── chapter/[id]/        # 章节学习
│   ├── stage/[id]/          # 关卡页面
│   ├── challenge/[id]/      # 挑战页面
│   └── ...
├── components/
│   ├── ui/                  # 通用 UI 组件
│   ├── layout/              # 布局组件
│   ├── course/              # 课程相关组件
│   ├── exercise/            # 练习相关组件
│   └── dashboard/           # 仪表盘组件
├── lib/
│   ├── api/                 # API 客户端模块
│   │   ├── client.ts        # 基础 fetch 封装
│   │   ├── auth.ts          # 认证 API
│   │   ├── courses.ts       # 课程 API
│   │   └── ...
│   └── utils/               # 工具函数
├── types/                   # TypeScript 类型定义
└── __tests__/               # Jest 测试
```

**API 调用模式**: 所有 API 调用通过 `lib/api/` 模块，使用 `fetchWithAuth` 统一处理认证和错误

## 开发规范

### 后端规范
- 使用 Pydantic 进行数据验证
- 所有 API 需要 TypeScript 类型对齐
- 测试覆盖率 >= 80%
- 使用 `logging` 模块，不用 `print()`
- Schema 放 `schemas/`，Model 放 `models/`，业务逻辑放 `services/`

### 前端规范
- 使用函数组件 + Hooks
- 类型定义放在 `types/` 目录
- API 调用使用 `lib/api/` 模块
- 组件放在 `components/` 目录

### Git 提交规范
```
<type>: <description>

类型: feat, fix, refactor, docs, test, chore, perf
```

## 常用命令

### 后端
```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 设置 SECRET_KEY 和 AI_API_KEY

# 初始化数据库
python init_db.py

# 启动开发服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_auth.py

# 运行单个测试函数
pytest tests/test_auth.py::test_register -v

# 测试覆盖率
pytest --cov=app --cov-report=term-missing

# 查看 API 文档
# 访问 http://localhost:8000/docs
```

### 前端
```bash
cd frontend

# 安装依赖（推荐 pnpm）
pnpm install

# 配置环境变量
# 创建 .env.local 文件：
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 启动生产服务
pnpm start

# 运行测试
pnpm test

# 代码检查
pnpm lint
```

## 环境变量

### 后端 (.env)
```env
# 必需
SECRET_KEY=your-secret-key-at-least-32-characters
AI_API_KEY=your-openai-api-key

# 可选
AI_PROVIDER=openai           # openai | local | ollama
AI_MODEL=gpt-4o-mini         # 模型名称
AI_BASE_URL=                 # API 基础 URL
AI_LOCAL_FIRST=false         # 优先使用本地模型
DATABASE_URL=sqlite+aiosqlite:///./data.db
DEBUG=false
```

### 前端 (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 测试说明

### 后端测试
- 使用 `test.db` 作为测试数据库（自动创建/销毁）
- `conftest.py` 提供常用 fixtures：`client`, `auth_user`, `auth_headers`, `admin_user`
- 所有测试前会重置速率限制器

### 前端测试
- 使用 Jest + Testing Library
- 配置在 `jest.config.js`
- 测试文件放在 `__tests__/` 或 `*.test.tsx`

## 注意事项

1. **AI配额管理**: 防止用户过度依赖AI，需要合理设置配额
2. **题目质量**: AI生成题目需要质量验证机制
3. **数据安全**: 用户代码和答案需要安全存储
4. **性能优化**: 大量练习题需要合理的缓存策略
5. **速率限制**: 后端有速率限制中间件，测试时需要重置
6. **外键约束**: SQLite 默认不启用外键，已在 `database.py` 中配置 `PRAGMA foreign_keys=ON`
7. **时区设置**: 本项目面向中国用户，所有时间显示和处理使用**北京时区 (Asia/Shanghai, UTC+8)**
   - 前端时间显示使用 `Intl.DateTimeFormat` 并指定 `timeZone: 'Asia/Shanghai'`
   - 后端数据库存储使用 UTC 时间，前端展示时转换为北京时间
   - "今日"统计基于北京时区的日期判断
