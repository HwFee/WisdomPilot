"""
核心应用模块包（路由注册、中间件、生命周期管理、异常处理）。

本包包含 FastAPI 应用启动所需的基础设施组件：
    - ``routes``:         统一注册所有 API 路由器和健康检查端点
    - ``middleware``:     限流中间件和 CORS 跨域配置
    - ``lifespan``:       应用启动/关闭生命周期管理（数据库初始化、AI 服务配置等）
    - ``exceptions``:     全局异常处理器，将错误转换为前端友好的 JSON 响应
"""

"""Core application modules (routing, middleware, lifespan, exceptions)."""
