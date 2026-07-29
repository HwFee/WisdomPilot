"""
FastAPI 应用入口模块。

本文件是整个后端服务的启动入口。它使用工厂函数模式（``create_app``）来
创建和配置 FastAPI 应用实例。工厂模式的好处是：
    1. 便于测试时创建独立的应用实例
    2. 配置可以在创建时注入，避免全局状态
    3. 所有中间件、路由、异常处理器的注册集中在一处，结构清晰

启动流程：
    加载配置 → 创建 FastAPI 实例 → 注册中间件 → 注册路由 → 注册健康检查 → 注册异常处理器

运行方式：
    uvicorn app.main:app --reload  （开发环境）
    gunicorn -k uvicorn.workers.UvicornWorker app.main:app  （生产环境）
"""

from fastapi import FastAPI

# 导入配置获取函数（从环境变量/.env 文件加载配置）
from app.config import get_settings
# 导入异常处理器注册函数
from app.core.exceptions import register_exception_handlers
# 导入生命周期管理工厂函数
from app.core.lifespan import create_lifespan
# 导入中间件配置函数
from app.core.middleware import configure_middleware
# 导入路由注册函数和健康检查路由注册函数
from app.core.routes import include_routers, register_health_routes

# ---------------------------------------------------------------------------
# 应用元信息常量，会展示在 Swagger 文档页面（/docs）上
# ---------------------------------------------------------------------------
APP_TITLE = "WisdomPilot API"                          # API 标题
APP_DESCRIPTION = "AI-powered DebugTeaching Platform API"  # API 描述
APP_VERSION = "1.0.1"                                  # API 版本号


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例（工厂模式）。

    本函数执行以下步骤来组装一个完整可用的应用：
        1. 加载应用配置（从 .env 文件或环境变量）
        2. 创建 FastAPI 实例，绑定生命周期管理器
        3. 注册中间件（CORS 跨域、限流）
        4. 注册 API 路由（认证路由 + 训练舱路由）
        5. 注册健康检查端点（/ 和 /health）
        6. 注册全局异常处理器

    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例，可直接被 uvicorn/gunicorn 使用
    """
    # 获取应用配置（通过 lru_cache 缓存，整个生命周期只读取一次环境变量）
    settings = get_settings()
    application = FastAPI(
        title=APP_TITLE,                # 显示在 Swagger 文档标题
        description=APP_DESCRIPTION,    # 显示在 Swagger 文档描述
        version=APP_VERSION,            # 显示在 Swagger 文档版本
        lifespan=create_lifespan(settings),  # 绑定启动/关闭生命周期管理
    )

    # 注册中间件（注意：Starlette 中间件按注册的逆序执行，先注册的在后执行）
    configure_middleware(application)
    # 注册所有 API 路由（auth + training）
    include_routers(application, settings)
    # 注册健康检查端点
    register_health_routes(application)
    # 注册全局异常处理器（统一错误响应格式）
    register_exception_handlers(application)

    return application


# 模块级变量：创建全局应用实例，供 uvicorn 导入使用
# uvicorn 启动命令会引用 app.main:app，即此变量
app = create_app()
