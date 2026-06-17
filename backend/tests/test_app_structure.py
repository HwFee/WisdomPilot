"""Application assembly structure tests."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app, create_app


def test_global_app_is_created_by_factory():
    """The exported ASGI app should come from the shared factory."""
    fresh_app = create_app()

    assert isinstance(fresh_app, FastAPI)
    assert app.title == fresh_app.title
    assert app.version == fresh_app.version


@pytest.mark.asyncio
async def test_health_endpoint_remains_registered():
    """Health checks stay available after application assembly refactors."""
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
