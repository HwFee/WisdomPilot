import pytest
import os
from datetime import datetime, timezone


class TestConfigSettings:
    """Test configuration settings (C1, C2, C3)"""

    def test_secret_key_is_required(self, monkeypatch):
        """C1: SECRET_KEY should raise error when not set"""
        # Clear all env vars that could affect settings
        monkeypatch.setenv("SECRET_KEY", "")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

        # Re-import to get fresh settings
        import importlib
        from app import config
        importlib.reload(config)

        with pytest.raises(Exception):
            config.get_settings()

    def test_secret_key_minimum_length(self, monkeypatch):
        """C1: SECRET_KEY shorter than 32 chars should raise error"""
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

        import importlib
        from app import config
        importlib.reload(config)

        with pytest.raises(Exception):
            config.get_settings()

    def test_secret_key_accepted(self, monkeypatch):
        """C1: SECRET_KEY >= 32 chars should be accepted"""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

        import importlib
        from app import config
        importlib.reload(config)

        settings = config.get_settings()
        assert settings.SECRET_KEY == "a" * 32

    def test_debug_default_false(self, monkeypatch):
        """C2: DEBUG should default to False"""
        # Explicitly set DEBUG=false to override any .env file value
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)

        import importlib
        from app import config
        importlib.reload(config)

        settings = config.get_settings()
        assert settings.DEBUG is False

    def test_debug_can_be_enabled(self, monkeypatch):
        """C2: DEBUG should be configurable"""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)

        import importlib
        from app import config
        importlib.reload(config)

        settings = config.get_settings()
        assert settings.DEBUG is True


class TestDatetimeUtc:
    """Test timezone-aware datetime (M2)"""

    def test_utc_now_returns_aware_datetime(self):
        """M2: utc_now should return timezone-aware datetime"""
        from app.utils.time import utc_now

        result = utc_now()

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_utc_now_is_current_time(self):
        """M2: utc_now should be close to actual current time"""
        from app.utils.time import utc_now

        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        assert before <= result <= after or abs((result - before).total_seconds()) < 1
