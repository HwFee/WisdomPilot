"""
WisdomPilot 后端应用包初始化模块。

本模块是整个后端 Python 应用的根包（``app``），所有后端代码都组织在 ``app``
子包下。FastAPI 应用实例在此包的 ``main`` 模块中创建。

包结构概览：
    app/
    ├── main.py          # FastAPI 应用入口，创建并配置 app 实例
    ├── config.py         # 全局配置（从 .env 读取）
    ├── database.py       # 异步数据库引擎与会话管理
    ├── core/             # 核心基础设施：路由注册、中间件、生命周期、异常处理
    ├── auth/             # 认证模块：用户模型、JWT 令牌、登录注册
    ├── training/         # 训练舱域：掌握度模型、徽章系统、题目评测
    └── ai/               # AI 基础设施：大模型调用封装

整个后端只注册两组路由：``/api/auth``（认证）和 ``/api``（训练舱 deck 域）。
"""

# 智码领航 Backend
