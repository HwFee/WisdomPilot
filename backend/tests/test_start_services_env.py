"""Startup script environment file tests."""

import sys

import start_services

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


def test_start_frontend_uses_the_local_next_executable(tmp_path, monkeypatch):
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    captured: dict[str, list[str]] = {}

    def capture_popen(command, **_kwargs):
        captured["command"] = command
        return object()

    monkeypatch.setattr(start_services.subprocess, "Popen", capture_popen)

    start_services.start_frontend(frontend_dir, tmp_path, "pnpm")

    assert captured["command"] == [
        str(frontend_dir / "node_modules" / ".bin" / "next.cmd"),
        "dev",
        "--port",
        "3000",
    ]


def test_database_migration_runs_as_a_backend_module(tmp_path, monkeypatch):
    captured: dict[str, object] = {}

    def capture_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        return object()

    monkeypatch.setattr(start_services.subprocess, "run", capture_run)

    start_services.run_database_migration(tmp_path)

    assert captured["command"] == [
        sys.executable,
        "-m",
        "scripts.migrate_missing_columns",
    ]
    assert captured["cwd"] == tmp_path
