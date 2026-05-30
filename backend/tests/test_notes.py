"""Tests for notes API"""

import pytest


@pytest.mark.asyncio
class TestNotesAPI:
    """Test notes endpoints"""

    async def test_create_note(self, client, auth_headers):
        """Should create a note"""
        response = await client.post(
            "/api/notes",
            json={
                "title": "My first note",
                "content": "This is an important concept to remember.",
                "chapter_id": 1,
                "subsection_index": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My first note"
        assert data["content"] == "This is an important concept to remember."
        assert data["chapter_id"] == 1

    async def test_get_notes(self, client, auth_headers):
        """Should get user's notes list"""
        # Create a note first
        await client.post(
            "/api/notes",
            json={
                "title": "Test note",
                "content": "Test content",
            },
            headers=auth_headers,
        )

        response = await client.get("/api/notes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notes" in data
        assert len(data["notes"]) >= 1

    async def test_update_note(self, client, auth_headers):
        """Should update a note"""
        # Create a note first
        create_response = await client.post(
            "/api/notes",
            json={
                "title": "Original title",
                "content": "Original content",
            },
            headers=auth_headers,
        )
        note_id = create_response.json()["id"]

        # Update it
        response = await client.put(
            f"/api/notes/{note_id}",
            json={
                "title": "Updated title",
                "content": "Updated content",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["content"] == "Updated content"

    async def test_delete_note(self, client, auth_headers):
        """Should delete a note"""
        # Create a note first
        create_response = await client.post(
            "/api/notes",
            json={
                "title": "To be deleted",
                "content": "This will be deleted",
            },
            headers=auth_headers,
        )
        note_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/notes/{note_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get("/api/notes", headers=auth_headers)
        notes = get_response.json()["notes"]
        assert not any(n["id"] == note_id for n in notes)

    async def test_get_notes_count(self, client, auth_headers):
        """Should get notes count"""
        # Create some notes
        for i in range(3):
            await client.post(
                "/api/notes",
                json={
                    "title": f"Note {i}",
                    "content": f"Content {i}",
                },
                headers=auth_headers,
            )

        response = await client.get("/api/notes/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3

    async def test_get_notes_by_chapter(self, client, auth_headers):
        """Should get notes filtered by chapter"""
        # Create notes for different chapters
        await client.post(
            "/api/notes",
            json={
                "title": "Chapter 1 note",
                "content": "Content for chapter 1",
                "chapter_id": 1,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/notes",
            json={
                "title": "Chapter 2 note",
                "content": "Content for chapter 2",
                "chapter_id": 2,
            },
            headers=auth_headers,
        )

        response = await client.get("/api/notes?chapter_id=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for note in data["notes"]:
            assert note["chapter_id"] == 1

    async def test_notes_require_auth(self, client):
        """Should require authentication for notes endpoints"""
        endpoints = [
            ("GET", "/api/notes"),
            ("GET", "/api/notes/count"),
            ("POST", "/api/notes"),
            ("PUT", "/api/notes/some-id"),
            ("DELETE", "/api/notes/some-id"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            elif method == "PUT":
                response = await client.put(endpoint, json={})
            else:
                response = await client.delete(endpoint)
            assert response.status_code == 401, f"{method} {endpoint} should require auth"
