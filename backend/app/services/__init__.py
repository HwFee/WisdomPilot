"""
外部服务集成包（Judge0 代码执行引擎）。

本包负责与 WisdomPilot 平台外部的第三方服务进行交互。当前主要集成了
Judge0——一个在线代码评测引擎，用于在沙箱中安全地编译、运行用户提交的代码。

设计说明：
- 领域特定的业务服务不在本包中，而是各自独立成包：
  - 认证服务：app.auth.service
  - AI 服务：app.ai.service
- 本包仅放置「与外部系统通信」的基础设施层代码，保持职责单一。

模块结构：
- judge0.py       —— Judge0Service：面向业务的代码执行服务，负责判定逻辑
- judge0_client.py —— Judge0Client：面向 HTTP 协议的底层客户端，负责网络通信
"""

import logging

# 使用标准 logging 模块，日志会归入 "app.services" 命名空间
logger = logging.getLogger(__name__)
