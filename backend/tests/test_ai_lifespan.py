from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.config import Settings
from app.core.lifespan import create_lifespan


def lifespan_settings() -> Settings:
    return Settings(
        SECRET_KEY="test-secret-key-that-is-long-enough-123",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        AI_PROVIDER="deepseek",
        AI_API_KEY="",
        AI_MODEL="deepseek-test",
    )


@pytest.mark.asyncio
async def test_lifespan_closes_ai_service_after_normal_exit() -> None:
    with patch("app.core.lifespan.init_db", new=AsyncMock()) as init_db:
        with patch("app.core.lifespan.seed_deck", new=AsyncMock()):
            with patch("app.core.lifespan.configure_ai_service", new=Mock()) as configure:
                with patch(
                    "app.core.lifespan.ai_service.aclose", new=AsyncMock()
                ) as close:
                    async with create_lifespan(lifespan_settings())(Mock()):
                        pass

    init_db.assert_awaited_once()
    configure.assert_called_once()
    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_closes_ai_service_when_application_body_fails() -> None:
    with patch("app.core.lifespan.init_db", new=AsyncMock()):
        with patch("app.core.lifespan.seed_deck", new=AsyncMock()):
            with patch("app.core.lifespan.configure_ai_service", new=Mock()):
                with patch(
                    "app.core.lifespan.ai_service.aclose", new=AsyncMock()
                ) as close:
                    with pytest.raises(RuntimeError, match="application failed"):
                        async with create_lifespan(lifespan_settings())(Mock()):
                            raise RuntimeError("application failed")

    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_configures_and_closes_judge0_service() -> None:
    """Judge0 与 lifespan 联动：启动配置（base_url 为空则不启用）、关闭释放连接。"""
    with patch("app.core.lifespan.init_db", new=AsyncMock()):
        with patch("app.core.lifespan.seed_deck", new=AsyncMock()):
            with patch("app.core.lifespan.configure_ai_service", new=Mock()):
                with patch("app.core.lifespan.ai_service.aclose", new=AsyncMock()):
                    with patch(
                        "app.core.lifespan.training_service.configure_judge0", new=Mock()
                    ) as configure_judge0:
                        with patch(
                            "app.core.lifespan.training_service.aclose_judge0", new=AsyncMock()
                        ) as close_judge0:
                            async with create_lifespan(lifespan_settings())(Mock()):
                                pass

    # 默认 JUDGE0_BASE_URL 为空 → 启动时以空串配置（判题走降级），关闭时释放
    configure_judge0.assert_called_once_with("")
    close_judge0.assert_awaited_once()
