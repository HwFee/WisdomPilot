# 智码领航 · AI 时代的编程实战训练舱

## 项目概述

智码领航（WisdomPilot）是一个面向编程实战能力训练的 Web 平台。系统围绕「训练舱」理念构建，
通过四个核心模块 + 复盘 + 能力图谱，形成「练—评—导—证」的闭环：

- **代码审查室**（`/review-gym`）：审查注入缺陷的代码，训练读码与缺陷识别能力
- **调试竞技场**（`/arena`）：ELO 评分、每日轮换的调试挑战
- **苏格拉底导师**（`/tutor`）：对话式引导，含「考考我」费曼检验模式
- **基本功认证**（`/certification`）：定级测试 + 主题认证
- **复盘**（`/review`）：错题与失败项聚合
- **能力图谱**（`/abilities`）：review / debug / implement 三轴能力成长

掌握度采用事件源 HLR 记忆模型 + 四级状态机（初识 / 熟悉 / 熟练 / 精通）。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+、FastAPI、SQLAlchemy 2.0（异步）、Pydantic v2、JWT 认证、SQLite（WAL） |
| 代码执行 | Judge0 |
| AI | 多 provider 抽象（DeepSeek / OpenAI / SiliconFlow 等） |
| 前端 | Next.js 15、React 19、TypeScript、Tailwind CSS v4、lucide-react、Monaco Editor |
| 测试 | 后端 pytest；前端 Jest + React Testing Library |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HwFee/zhima-linghang-demo.git
cd zhima-linghang-demo
```

### 2. 一键启动（Windows 推荐）

双击 `start.ps1`（或在 PowerShell 执行 `.\start.ps1`），启动器会：
- 自动检测端口、清理残留进程
- 检查并初始化 `backend/.env`（从根目录 `.env.example` 生成，自动填入随机 SECRET_KEY）
- 自动安装依赖（如缺）
- 同时拉起后端 `http://localhost:8000` 与前端 `http://localhost:3000`

按 Ctrl+C 关闭所有进程，或双击 `stop.ps1` 停止。

### 3. 开始使用

1. 打开浏览器访问 http://localhost:3000
2. 注册账号并登录，进入 `/dashboard` 首页
3. 从首页四模块入口开始训练

## 环境要求

- Python 3.10+
- Node.js 18+
- pnpm（推荐）或 npm

## 环境变量配置

环境变量模板在项目根目录 `.env.example`。双击 `start.ps1` 启动时，启动器会自动：
1. 如果 `backend/.env` 不存在，从根目录 `.env.example` 复制生成，并填入随机的 `SECRET_KEY`
2. 如果 `backend/.env` 已存在且 `SECRET_KEY` 合法，直接使用

需要修改 AI 配置时，编辑 `backend/.env` 文件（填入 `AI_API_KEY`、`AI_PROVIDER`、`AI_MODEL`、`AI_BASE_URL` 等）。

前端默认连 `http://localhost:8000`；如需自定义，建 `frontend/.env.local` 并写：

```
NEXT_PUBLIC_API_URL=http://your-backend-host:port
```

前端默认走 mock 数据（`NEXT_PUBLIC_DECK_MOCK` 未设置时为 `1`）；需要联调真实后端时，设 `NEXT_PUBLIC_DECK_MOCK=0`。

## 项目结构

```
WisdomPilot/
├── backend/
│   ├── app/
│   │   ├── auth/          # 认证（注册/登录/JWT）
│   │   ├── training/      # 训练舱业务域（路由/模型/掌握度/徽章/种子）
│   │   ├── ai/            # AI provider 抽象
│   │   ├── core/          # lifespan / middleware / 限流 / 路由注册
│   │   ├── services/      # Judge0 等外部服务封装
│   │   ├── utils/
│   │   └── main.py        # 应用入口
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── app/               # Next.js App Router 页面
│   ├── components/        # React 组件（各模块 + deck 共享 kit）
│   ├── lib/api/deck/      # 训练舱契约层（唯一数据源，含 mock）
│   ├── __tests__/         # Jest 测试
│   └── package.json
│
├── docs/                  # 设计文档与接口规格
├── start.ps1 / start_services.py
├── stop.ps1 / stop_services.py
└── AGENTS.md              # Agent 协作规则（权威架构说明）
```

> 注：后端业务模块目录为 `app/training/`，但数据表前缀（`deck_*`）、前端契约目录（`lib/api/deck/`）与组件目录（`components/deck/`）仍沿用 `deck` 命名——这是重构遗留，两者指向同一业务域。

## 相关文档

- `AGENTS.md`：项目架构与 Agent 协作规则（最权威的现状说明）
- `docs/backend-api/01-target-design.md`：后端接口规格
- `docs/superpowers/specs/`：各子系统设计 spec
