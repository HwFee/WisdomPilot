"""Tests for favorites API"""

import pytest
from datetime import datetime


@pytest.mark.asyncio
class TestFavoritesAPI:
    """Test favorites endpoints"""

    async def test_add_favorite(self, client, auth_headers):
        """Should add an exercise to favorites"""
        response = await client.post(
            "/api/favorites",
            json={
                "exercise_id": 1,
                "chapter_id": 1,
                "subsection_index": 0,
                "note": "Important concept",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exercise_id"] == 1
        assert data["chapter_id"] == 1
        assert data["note"] == "Important concept"

    async def test_get_favorites(self, client, auth_headers):
        """Should get user's favorites list"""
        # Add a favorite first
        await client.post(
            "/api/favorites",
            json={
                "exercise_id": 1,
                "chapter_id": 1,
                "subsection_index": 0,
            },
            headers=auth_headers,
        )

        response = await client.get("/api/favorites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "favorites" in data
        assert len(data["favorites"]) >= 1

    async def test_remove_favorite(self, client, auth_headers):
        """Should remove an exercise from favorites"""
        # Add a favorite first
        add_response = await client.post(
            "/api/favorites",
            json={
                "exercise_id": 2,
                "chapter_id": 1,
                "subsection_index": 0,
            },
            headers=auth_headers,
        )
        favorite_id = add_response.json()["id"]

        # Remove it
        response = await client.delete(f"/api/favorites/{favorite_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's removed
        get_response = await client.get("/api/favorites", headers=auth_headers)
        favorites = get_response.json()["favorites"]
        assert not any(f["id"] == favorite_id for f in favorites)

    async def test_get_favorites_count(self, client, auth_headers):
        """Should get favorites count"""
        # Add some favorites
        for i in range(3):
            await client.post(
                "/api/favorites",
                json={
                    "exercise_id": i + 10,
                    "chapter_id": 1,
                    "subsection_index": 0,
                },
                headers=auth_headers,
            )

        response = await client.get("/api/favorites/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3

    async def test_duplicate_favorite(self, client, auth_headers):
        """Should handle duplicate favorite gracefully"""
        # Add a favorite
        await client.post(
            "/api/favorites",
            json={
                "exercise_id": 100,
                "chapter_id": 1,
                "subsection_index": 0,
            },
            headers=auth_headers,
        )

        # Try to add the same favorite again
        response = await client.post(
            "/api/favorites",
            json={
                "exercise_id": 100,
                "chapter_id": 1,
                "subsection_index": 0,
            },
            headers=auth_headers,
        )
        # Should return the existing favorite
        assert response.status_code == 200

    async def test_favorites_require_auth(self, client):
        """Should require authentication for favorites endpoints"""
        endpoints = [
            ("GET", "/api/favorites"),
            ("GET", "/api/favorites/count"),
            ("POST", "/api/favorites"),
            ("DELETE", "/api/favorites/some-id"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            else:
                response = await client.delete(endpoint)
            assert response.status_code == 401, f"{method} {endpoint} should require auth"
