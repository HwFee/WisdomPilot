"""Exercise WebSocket - 题目生成实时推送

基于 FastAPI WebSocket 实现，用于：
1. 推送新生成的题目
2. 通知生成完成/失败
3. 支持连接管理和心跳

简化实现，优先稳定性。"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.services.auth import verify_token

logger = logging.getLogger(__name__)


class ExerciseWebSocketManager:
    """管理题目生成WebSocket连接

    每个用户可以有多个连接（多个标签页）。
    按session_id组织连接，只推送用户关心的会话。
    """

    def __init__(self):
        # user_id -> set of WebSockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # session_id -> user_id
        self.session_users: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """建立WebSocket连接，返回是否成功"""
        try:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            logger.info(f"WebSocket连接建立: user={user_id[:8]}..., 当前连接数={len(self.user_connections[user_id])}")
            return True
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """断开WebSocket连接"""
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            logger.info(f"WebSocket连接断开: user={user_id[:8]}...")

    def register_session(self, session_id: str, user_id: str) -> None:
        """注册会话，建立session到user的映射"""
        self.session_users[session_id] = user_id

    def unregister_session(self, session_id: str) -> None:
        """注销会话"""
        if session_id in self.session_users:
            del self.session_users[session_id]

    async def send_exercise(self, session_id: str, index: int, exercise: dict) -> None:
        """推送新题目到用户"""
        user_id = self.session_users.get(session_id)
        if not user_id:
            return

        connections = self.user_connections.get(user_id, set())
        if not connections:
            return

        message = {
            "type": "exercise_generated",
            "session_id": session_id,
            "index": index,
            "exercise": exercise,
            "progress": index + 1,
        }

        # 向所有连接发送（多标签页场景）
        dead_connections = set()
        for conn in connections:
            try:
                if conn.client_state == WebSocketState.CONNECTED:
                    await conn.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket发送失败: {e}")
                dead_connections.add(conn)

        # 清理失效连接
        for dead in dead_connections:
            self.disconnect(dead, user_id)

    async def send_completion(self, session_id: str, total_count: int) -> None:
        """推送生成完成消息"""
        user_id = self.session_users.get(session_id)
        if not user_id:
            return

        connections = self.user_connections.get(user_id, set())
        if not connections:
            return

        message = {
            "type": "generation_completed",
            "session_id": session_id,
            "total_count": total_count,
        }

        dead_connections = set()
        for conn in connections:
            try:
                if conn.client_state == WebSocketState.CONNECTED:
                    await conn.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket发送失败: {e}")
                dead_connections.add(conn)

        for dead in dead_connections:
            self.disconnect(dead, user_id)

    async def send_error(self, session_id: str, error: str) -> None:
        """推送生成错误"""
        user_id = self.session_users.get(session_id)
        if not user_id:
            return

        connections = self.user_connections.get(user_id, set())
        if not connections:
            return

        message = {
            "type": "generation_failed",
            "session_id": session_id,
            "error": error,
        }

        dead_connections = set()
        for conn in connections:
            try:
                if conn.client_state == WebSocketState.CONNECTED:
                    await conn.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket发送失败: {e}")
                dead_connections.add(conn)

        for dead in dead_connections:
            self.disconnect(dead, user_id)


# 全局管理器实例
websocket_manager = ExerciseWebSocketManager()


async def exercise_websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket端点处理器

    URL: /ws/exercises?token=<jwt_token>

    客户端连接后：
    1. 验证token获取user_id
    2. 保持连接，监听消息
    3. 自动处理断开
    """
    # 验证token
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    if not await websocket_manager.connect(websocket, user.id):
        await websocket.close(code=4002, reason="Connection failed")
        return

    try:
        # 保持连接，处理心跳
        while True:
            try:
                # 等待消息（心跳或控制命令）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30秒心跳超时
                )

                # 处理心跳 pong
                if data == "ping":
                    await websocket.send_text("pong")
                    continue

                # 处理其他命令（如订阅特定session）
                # 预留扩展接口
                try:
                    msg = json.loads(data)
                    if msg.get("action") == "subscribe":
                        session_id = msg.get("session_id")
                        if session_id:
                            websocket_manager.register_session(session_id, user.id)
                            await websocket.send_json({"type": "subscribed", "session_id": session_id})
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # 发送心跳检测
                try:
                    await websocket.send_text("ping")
                    # 等待pong
                    response = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                    if response != "pong":
                        break
                except (asyncio.TimeoutError, WebSocketDisconnect):
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket断开: user={user.id[:8]}...")
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
    finally:
        websocket_manager.disconnect(websocket, user.id)
