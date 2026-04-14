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
- **数据库**: SQLite + SQLAlchemy (async)
- **AI**: 支持多 Provider (OpenAI, 本地模型等)
- **认证**: JWT Token

### 前端
- **框架**: Next.js 16 + React 19
- **语言**: TypeScript
- **样式**: Tailwind CSS 4
- **代码编辑器**: Monaco Editor

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
- 实时代码运行反馈
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

## 项目结构

```
AIcodiingTeach/
├── backend/
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑
│   │   ├── utils/           # 工具函数
│   │   └── main.py          # 应用入口
│   ├── tests/               # 测试文件
│   └── data.db              # SQLite 数据库
│
├── frontend/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React 组件
│   ├── lib/                 # 工具库
│   │   └── api/             # API 客户端
│   ├── types/               # TypeScript 类型
│   └── __tests__/           # 测试文件
│
└── CLAUDE.md                # 本文件
```

## 开发规范

### 后端规范
- 使用 Pydantic 进行数据验证
- 所有 API 需要 TypeScript 类型对齐
- 测试覆盖率 >= 80%
- 使用 `logging` 模块，不用 `print()`

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pytest                                    # 运行测试
pytest --cov=app --cov-report=term-missing  # 测试覆盖率
```

### 前端
```bash
cd frontend
npm run build && npm start    # 生产模式启动
npm test                       # 运行测试
```

## AI 配置

环境变量配置 (`.env`):
```
AI_PROVIDER=openai|local|ollama
AI_API_KEY=your-api-key
AI_MODEL=gpt-4|gpt-3.5-turbo|local-model
AI_BASE_URL=https://api.openai.com/v1
AI_LOCAL_FIRST=true|false
```

## 注意事项

1. **AI配额管理**: 防止用户过度依赖AI，需要合理设置配额
2. **题目质量**: AI生成题目需要质量验证机制
3. **数据安全**: 用户代码和答案需要安全存储
4. **性能优化**: 大量练习题需要合理的缓存策略
