from app.routers.auth import router as auth_router
import logging

__all__ = ["auth_router"]


logger = logging.getLogger(__name__)
