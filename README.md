# 智码领航 - 基于GAI的程序设计类课程实践教学系统

## 项目概述

基于生成式AI(GAI)的编程教学平台，支持 C/C++/Python/Java/Rust 等多门课程的在线学习与练习。

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HwFee/zhima-linghang-demo.git
cd zhima-linghang-demo
```

### 2. 一键启动(Windows 推荐)

双击 `start.ps1`(或在 PowerShell 执行 `.\start.ps1`),启动器会:
- 自动检测端口,清理残留进程
- 检查并初始化 `backend/.env`(从根目录 `.env.example` 生成,自动填入随机 SECRET_KEY)
- 自动 `pnpm install`(如缺依赖)
- 同时拉起后端 `http://localhost:8000` 与前端 `http://localhost:3000`

按 Ctrl+C 关闭所有进程,或双击 `stop.ps1` 停止。

### 3. 开始使用

1. 打开浏览器访问 http://localhost:3000
2. 点击"注册"创建账号
3. 登录后选择课程开始学习

## 环境要求

- Python 3.10+
- Node.js 18+
- pnpm (推荐) 或 npm

## 环境变量配置

环境变量模板在项目根目录 `.env.example`,双击 `start.ps1` 启动时,启动器会自动:
1. 如果 `backend/.env` 不存在,从根目录 `.env.example` 复制生成,并填入随机的 `SECRET_KEY`
2. 如果 `backend/.env` 已存在且 `SECRET_KEY` 合法,直接使用

需要修改 AI 配置时,编辑 `backend/.env` 文件(填入 `AI_API_KEY`、`EMBEDDING_API_KEY` 等)。

前端默认连 `http://localhost:8000`,如需自定义,建 `frontend/.env.local` 并写:

```
NEXT_PUBLIC_API_URL=http://your-backend-host:port
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
