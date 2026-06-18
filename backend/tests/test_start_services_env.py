"""Startup script environment file tests."""

from start_services import ensure_backend_env


def test_backend_env_generation_omits_frontend_public_variables(tmp_path):
    project_root = tmp_path
    backend_dir = project_root / "backend"
    backend_dir.mkdir()
    (project_root / ".env.example").write_text(
        "\n".join([
            "DATABASE_URL=sqlite+aiosqlite:///./data.db",
            "SECRET_KEY=",
            "NEXT_PUBLIC_API_URL=http://localhost:8000",
        ]),
        encoding="utf-8",
    )

    ensure_backend_env(backend_dir)

    backend_env = (backend_dir / ".env").read_text(encoding="utf-8")
    assert "DATABASE_URL=sqlite+aiosqlite:///./data.db" in backend_env
    assert "SECRET_KEY=" in backend_env
    assert "NEXT_PUBLIC_API_URL" not in backend_env
