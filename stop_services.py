"""
智码领航 手动停止脚本

用途：
- 读取 .run_logs/service_state.json 中的 PID
- 递归关闭前后端进程树
- 兜底清理 3000 / 8000 端口残留进程

用法：
    python stop_services.py
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path


BACKEND_PORT = 8000
FRONTEND_PORT = 3000
STATE_FILE = Path(__file__).resolve().parent / ".run_logs" / "service_state.json"


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
    seen: set[int] = set()
    for port in ports:
        for pid in get_pids_by_port(port):
            if pid not in seen:
                print(f"[清理] 关闭占用端口 {port} 的进程树 PID={pid}")
                kill_process_tree(pid)
                seen.add(pid)
    if seen:
        time.sleep(2)


def main() -> int:
    print("=" * 56)
    print(" 智码领航 停止脚本")
    print("=" * 56)

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[警告] 状态文件读取失败: {exc}")
            state = {}

        for key, label in (
            ("frontend_pid", "前端"),
            ("backend_pid", "后端"),
            ("launcher_pid", "启动窗口"),
        ):
            pid = state.get(key)
            if isinstance(pid, int) and pid > 0:
                print(f"[停止] 关闭{label}进程树 PID={pid}")
                kill_process_tree(pid)
    else:
        print("[提示] 未找到状态文件，将直接按端口清理。")

    cleanup_ports([BACKEND_PORT, FRONTEND_PORT])

    try:
        STATE_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    backend_alive = port_in_use(BACKEND_PORT)
    frontend_alive = port_in_use(FRONTEND_PORT)

    if backend_alive or frontend_alive:
        print("[警告] 仍检测到端口占用：")
        if backend_alive:
            print(f"  - {BACKEND_PORT}")
        if frontend_alive:
            print(f"  - {FRONTEND_PORT}")
        return 1

    print("[完成] 前后端服务已停止")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
