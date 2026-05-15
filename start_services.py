"""
智码领航 服务启动器

特性：
- 前台统一托管前后端进程
- Ctrl+C 时递归关闭整棵进程树
- 自动清理 3000 / 8000 端口残留进程
- 前后端日志分别落盘

用法：
    python start_services.py
    python start_services.py --reload-backend
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import json


BACKEND_PORT = 8000
FRONTEND_PORT = 3000
STATE_FILE_NAME = "service_state.json"


def is_windows() -> bool:
    return os.name == "nt"


def run_quiet(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def get_pids_by_port(port: int) -> list[int]:
    if not is_windows():
        return []

    result = run_quiet(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                "Select-Object -ExpandProperty OwningProcess -Unique"
            ),
        ]
    )
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def kill_process_tree(pid: int) -> None:
    if pid <= 0:
        return

    if is_windows():
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def cleanup_ports(ports: list[int]) -> None:
    killed: set[int] = set()
    for port in ports:
        for pid in get_pids_by_port(port):
            if pid not in killed:
                print(f"[清理] 结束占用端口 {port} 的进程树 PID={pid}")
                kill_process_tree(pid)
                killed.add(pid)
    if killed:
        time.sleep(2)


def write_state_file(
    state_file: Path,
    launcher_pid: int | None,
    backend_pid: int | None,
    frontend_pid: int | None,
    backend_port: int,
    frontend_port: int,
) -> None:
    state = {
        "launcher_pid": launcher_pid,
        "backend_pid": backend_pid,
        "frontend_pid": frontend_pid,
        "backend_port": backend_port,
        "frontend_port": frontend_port,
    }
    state_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def remove_state_file(state_file: Path) -> None:
    try:
        state_file.unlink(missing_ok=True)
    except Exception:
        pass


def stop_previous_run(state_file: Path, current_pid: int) -> None:
    if not state_file.exists():
        return

    print("[清理] 检测到上一次运行状态，先停止旧窗口和旧服务...")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[警告] 状态文件读取失败，将直接删除: {exc}")
        remove_state_file(state_file)
        return

    for key, label in (
        ("frontend_pid", "前端"),
        ("backend_pid", "后端"),
        ("launcher_pid", "启动窗口"),
    ):
        pid = state.get(key)
        if isinstance(pid, int) and pid > 0 and pid != current_pid:
            print(f"[清理] 关闭旧{label}进程树 PID={pid}")
            kill_process_tree(pid)

    time.sleep(2)
    remove_state_file(state_file)


def wait_for_url(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status in (200, 404):
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def resolve_pnpm() -> str:
    candidates = [
        r"C:\Program Files\nodejs\pnpm.cmd",
        "pnpm.cmd",
        "pnpm",
    ]
    for candidate in candidates:
        result = subprocess.run(
            [candidate, "--version"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if result.returncode == 0:
            return candidate
    raise RuntimeError("未找到 pnpm，请先安装 pnpm。")


def ensure_frontend_dependencies(frontend_dir: Path, pnpm_cmd: str) -> None:
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        return

    print("[检查] 前端依赖缺失，正在安装...")
    result = subprocess.run(
        [pnpm_cmd, "install"],
        cwd=frontend_dir,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("前端依赖安装失败。")


def ensure_backend_env(backend_dir: Path) -> None:
    env_file = backend_dir / ".env"
    example_file = backend_dir.parent / ".env.example"

    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("SECRET_KEY=") and len(line.split("=", 1)[1]) >= 32:
                return
        print("[检查] .env 中 SECRET_KEY 为空，正在重新生成...")

    import secrets

    secret_key = secrets.token_hex(32)

    if example_file.exists():
        print("[检查] 从 .env.example 创建 .env 并生成 SECRET_KEY...")
        content = example_file.read_text(encoding="utf-8")
        lines = []
        for line in content.splitlines():
            if line.startswith("SECRET_KEY="):
                lines.append(f"SECRET_KEY={secret_key}")
            else:
                lines.append(line)
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        print("[检查] 创建 .env 文件并生成 SECRET_KEY...")
        env_file.write_text(f"SECRET_KEY={secret_key}\n", encoding="utf-8")


def start_backend(backend_dir: Path, log_dir: Path, reload_backend: bool) -> subprocess.Popen:
    stdout_file = open(log_dir / "backend.log", "w", encoding="utf-8")
    stderr_file = open(log_dir / "backend.err.log", "w", encoding="utf-8")

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(BACKEND_PORT),
    ]
    if reload_backend:
        command.append("--reload")

    print(f"[启动] 后端 FastAPI: {' '.join(command)}")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0
    return subprocess.Popen(
        command,
        cwd=backend_dir,
        stdout=stdout_file,
        stderr=stderr_file,
        creationflags=creationflags,
    )


def start_frontend(frontend_dir: Path, log_dir: Path, pnpm_cmd: str) -> subprocess.Popen:
    stdout_file = open(log_dir / "frontend.log", "w", encoding="utf-8")
    stderr_file = open(log_dir / "frontend.err.log", "w", encoding="utf-8")

    command = [pnpm_cmd, "exec", "next", "dev", "--port", str(FRONTEND_PORT)]
    print(f"[启动] 前端 Next.js: {' '.join(command)}")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0
    return subprocess.Popen(
        command,
        cwd=frontend_dir,
        stdout=stdout_file,
        stderr=stderr_file,
        creationflags=creationflags,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="智码领航 服务启动器")
    parser.add_argument(
        "--reload-backend",
        action="store_true",
        help="以 uvicorn --reload 模式启动后端",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root_dir = Path(__file__).resolve().parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    log_dir = root_dir / ".run_logs"
    log_dir.mkdir(exist_ok=True)
    state_file = log_dir / STATE_FILE_NAME

    print("=" * 56)
    print(" 智码领航 启动脚本")
    print("=" * 56)
    print(f"[目录] 项目根目录: {root_dir}")
    print(f"[日志] 日志目录: {log_dir}")

    stop_previous_run(state_file, current_pid=os.getpid())
    cleanup_ports([BACKEND_PORT, FRONTEND_PORT])

    ensure_backend_env(backend_dir)

    pnpm_cmd = resolve_pnpm()
    ensure_frontend_dependencies(frontend_dir, pnpm_cmd)

    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None
    shutting_down = False

    def shutdown(*_: object) -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True

        print("\n[停止] 收到 Ctrl+C，正在关闭所有服务...")
        for proc, name in ((frontend_proc, "前端"), (backend_proc, "后端")):
            if proc is not None:
                print(f"[停止] 关闭{name}进程树 PID={proc.pid}")
                kill_process_tree(proc.pid)
        cleanup_ports([BACKEND_PORT, FRONTEND_PORT])
        remove_state_file(state_file)
        print("[完成] 所有服务已停止")

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    try:
        backend_proc = start_backend(backend_dir, log_dir, args.reload_backend)
        print(f"[信息] 后端 PID: {backend_proc.pid}")
        print("[等待] 后端启动中...")
        if not wait_for_url(f"http://127.0.0.1:{BACKEND_PORT}/", timeout=30):
            raise RuntimeError("后端启动超时，请查看 .run_logs/backend.err.log")

        frontend_proc = start_frontend(frontend_dir, log_dir, pnpm_cmd)
        print(f"[信息] 前端 PID: {frontend_proc.pid}")
        print("[等待] 前端启动中...")
        if not wait_for_url(f"http://127.0.0.1:{FRONTEND_PORT}", timeout=60):
            raise RuntimeError("前端启动超时，请查看 .run_logs/frontend.err.log")

        write_state_file(
            state_file,
            launcher_pid=os.getpid(),
            backend_pid=backend_proc.pid,
            frontend_pid=frontend_proc.pid,
            backend_port=BACKEND_PORT,
            frontend_port=FRONTEND_PORT,
        )

        print("")
        print("=" * 56)
        print(" 服务已启动")
        print("=" * 56)
        print(f" 后端: http://localhost:{BACKEND_PORT}")
        print(f" 前端: http://localhost:{FRONTEND_PORT}")
        print(" 按 Ctrl+C 停止所有进程")
        print(f" 后端日志: {log_dir / 'backend.log'}")
        print(f" 后端错误: {log_dir / 'backend.err.log'}")
        print(f" 前端日志: {log_dir / 'frontend.log'}")
        print(f" 前端错误: {log_dir / 'frontend.err.log'}")
        print(f" 手动停止: python {root_dir / 'stop_services.py'}")
        print("")

        while True:
            if backend_proc.poll() is not None:
                raise RuntimeError("后端进程已退出，请查看日志。")
            if frontend_proc.poll() is not None:
                raise RuntimeError("前端进程已退出，请查看日志。")
            time.sleep(1)

    except KeyboardInterrupt:
        shutdown()
        return 0
    except Exception as exc:
        print(f"[错误] {exc}")
        shutdown()
        return 1
    finally:
        shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
