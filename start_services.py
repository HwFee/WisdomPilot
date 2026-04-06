"""
AIcodiingTeach 服务启动器
用法: python start_services.py
"""
import subprocess
import time
import sys
import os
import signal
import socket

def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_port(port):
    """Kill processes using a specific port on Windows"""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | '
             f'Select-Object -ExpandProperty OwningProcess | '
             f'ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}'],
            capture_output=True, text=True
        )
    except:
        pass

def wait_for_url(url, timeout=20, interval=0.5):
    """Wait for a URL to return 200 or 404"""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = urllib.request.urlopen(url, timeout=1)
            if r.status in (200, 404):
                return True
        except:
            pass
        time.sleep(interval)
    return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, 'backend')
    frontend_dir = os.path.join(script_dir, 'frontend')
    backend_port = 8000
    frontend_port = 3000

    print("=" * 50)
    print(" AIcodiingTeach 启动脚本")
    print("=" * 50)

    # Kill old processes on ports
    for port in [backend_port, frontend_port]:
        if port_in_use(port):
            print(f"[清理] 端口 {port} 被占用，正在清理...")
            kill_port(port)
            time.sleep(1)

    # Start backend
    print(f"[启动] 后端 FastAPI (端口 {backend_port})...")
    backend_proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app',
         '--host', '0.0.0.0', '--port', str(backend_port)],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    print(f"      PID: {backend_proc.pid}")

    print(f"[等待] 后端启动中...")
    if wait_for_url(f'http://localhost:{backend_port}/'):
        print(f"      后端启动成功 (http://localhost:{backend_port})")
    else:
        print(f"      后端启动超时！")
        sys.exit(1)

    # Start frontend
    print(f"[启动] 前端 Next.js (端口 {frontend_port})...")
    npm_cmd = r'C:\Program Files\nodejs\npm.cmd'
    frontend_proc = subprocess.Popen(
        [npm_cmd, 'run', 'dev', '--', '--port', str(frontend_port)],
        cwd=frontend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    print(f"      PID: {frontend_proc.pid}")

    print(f"[等待] 前端启动中...")
    if wait_for_url(f'http://localhost:{frontend_port}', timeout=40):
        print(f"      前端启动成功 (http://localhost:{frontend_port})")
    else:
        print(f"      前端启动超时，请手动检查")

    print("")
    print("=" * 50)
    print(" 服务已启动")
    print("=" * 50)
    print(f"  后端: http://localhost:{backend_port}")
    print(f"  前端: http://localhost:{frontend_port}")
    print("")
    print(" 按 Ctrl+C 停止所有服务")
    print("")

    shutdown_requested = False

    def shutdown(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        print("\n[停止] 正在关闭服务...")
        for proc in [backend_proc, frontend_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except:
                    proc.kill()
        for port in [backend_port, frontend_port]:
            kill_port(port)
        print("[完成] 所有服务已停止")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Keep running (non-blocking check)
    while not shutdown_requested:
        try:
            time.sleep(0.5)
            # Poll to check if backend exited unexpectedly
            if backend_proc.poll() is not None:
                print("[错误] 后端进程意外退出")
                break
        except KeyboardInterrupt:
            shutdown(None, None)
            break

if __name__ == '__main__':
    main()
