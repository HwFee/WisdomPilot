# 智码领航 - 基于GAI的程序设计类课程实践教学系统

## 项目概述

基于生成式AI(GAI)的编程教学平台，支持 C/C++/Python/Java/Rust 等多门课程的在线学习与练习。

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HwFee/zhima-linghang-demo.git
cd zhima-linghang-demo
```

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制示例文件并修改）
copy .env.example .env
# 编辑 .env 文件，配置 AI_API_KEY 等

# 初始化数据库
python init_db.py

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动成功后访问: http://localhost:8000/docs 查看 API 文档

### 3. 前端启动

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖（使用 pnpm）
npm install -g pnpm  # 如果没有安装 pnpm
pnpm install

# 配置环境变量
# 创建 .env.local 文件，内容如下：
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 启动前端服务
pnpm dev
```

前端启动成功后访问: http://localhost:3000

### 4. 开始使用

1. 打开浏览器访问 http://localhost:3000
2. 点击"注册"创建账号
3. 登录后选择课程开始学习

## 环境要求

- Python 3.10+
- Node.js 18+
- pnpm (推荐) 或 npm

## 环境变量配置

### 后端 (.env)

```env
# AI 配置
AI_PROVIDER=openai
AI_API_KEY=your-api-key
AI_MODEL=gpt-4
AI_BASE_URL=https://api.openai.com/v1

# JWT 密钥
SECRET_KEY=your-secret-key

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data.db
```

### 前端 (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 项目结构

```
智码领航/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── models/        # 数据模型
│   │   ├── routers/       # API 路由
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 应用入口
│   ├── tests/             # 测试文件
│   ├── init_db.py         # 数据库初始化脚本
│   └── requirements.txt
│
├── frontend/               # Next.js 前端
│   ├── app/               # 页面路由
│   ├── components/        # React 组件
│   ├── lib/               # 工具库
│   └── package.json
│
└── README.md
```

## 支持的课程

1. C语言程序设计
2. C++程序设计
3. Python程序设计
4. Java程序设计
5. Rust程序设计
6. 数据结构与算法
7. 算法设计与分析
8. 离散数学

## 常用命令

### 后端

```bash
# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 运行测试
pytest

# 测试覆盖率
pytest --cov=app --cov-report=term-missing
```

### 前端

```bash
# 开发模式
pnpm dev

# 构建生产版本
pnpm build

# 启动生产服务
pnpm start

# 运行测试
pnpm test
```
