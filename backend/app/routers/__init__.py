from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.admin import router as admin_router
from app.routers.stats import router as stats_router
from app.routers.code import router as code_router
from app.routers.solutions import router as solutions_router

__all__ = ["auth_router", "users_router", "admin_router", "stats_router", "code_router", "solutions_router"]
