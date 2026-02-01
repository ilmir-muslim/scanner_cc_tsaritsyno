from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import uuid
from typing import Dict
from ..schemas import WebSocketMessage

router = APIRouter(prefix="/ws", tags=["remote-scanner"])


class ConnectionManager:
    def __init__(self):
        # session_id -> {"host": WebSocket, "client": WebSocket}
        self.active_sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, device_type: str):
        await websocket.accept()

        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}

        self.active_sessions[session_id][device_type] = websocket

        # Уведомляем другую сторону о подключении
        other_type = "client" if device_type == "host" else "host"
        if other_type in self.active_sessions[session_id]:
            await self.send_message(
                self.active_sessions[session_id][other_type],
                WebSocketMessage(
                    type="status",
                    session_id=session_id,
                    status=f"{device_type}_connected",
                ),
            )

        return session_id

    async def disconnect(self, session_id: str, device_type: str):
        if (
            session_id in self.active_sessions
            and device_type in self.active_sessions[session_id]
        ):
            del self.active_sessions[session_id][device_type]

            # Если обе стороны отключились, удаляем сессию
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]
            else:
                # Уведомляем оставшуюся сторону об отключении
                remaining_type = "client" if device_type == "host" else "host"
                if remaining_type in self.active_sessions[session_id]:
                    await self.send_message(
                        self.active_sessions[session_id][remaining_type],
                        WebSocketMessage(
                            type="status",
                            session_id=session_id,
                            status=f"{device_type}_disconnected",
                        ),
                    )

    async def send_message(self, websocket: WebSocket, message: WebSocketMessage):
        await websocket.send_json(message.dict())

    async def forward_scan(self, session_id: str, qr_content: str, from_device: str):
        """Пересылает отсканированный код с телефона на компьютер"""
        if session_id in self.active_sessions:
            other_type = "host" if from_device == "client" else "client"
            if other_type in self.active_sessions[session_id]:
                message = WebSocketMessage(
                    type="scan",
                    session_id=session_id,
                    qr_content=qr_content,
                    device_type=from_device,
                )
                await self.send_message(
                    self.active_sessions[session_id][other_type], message
                )
                return True
        return False


manager = ConnectionManager()


@router.websocket("/remote-scanner/{session_id}/{device_type}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, device_type: str):
    try:
        await websocket.accept()
        print(f"✅ WebSocket connection accepted: {session_id} - {device_type}")

        await manager.connect(websocket, session_id, device_type)

        # Отправляем подтверждение подключения
        await websocket.send_json(
            {
                "type": "connect",
                "session_id": session_id,
                "device_type": device_type,
                "status": "connected",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Ожидаем сообщения
        while True:
            try:
                data = await websocket.receive_json()
                print(f"Received message: {data}")

                if data.get("type") == "scan" and data.get("qr_content"):
                    # Пересылаем сканирование
                    await manager.forward_scan(
                        session_id, data["qr_content"], device_type
                    )

                elif data.get("type") == "ping":
                    # Отправляем pong для поддержания соединения
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )

            except Exception as e:
                print(f"Error processing message: {e}")
                break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id} - {device_type}")
        await manager.disconnect(session_id, device_type)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(session_id, device_type)


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Проверка статуса сессии"""
    if session_id in manager.active_sessions:
        devices = list(manager.active_sessions[session_id].keys())
        return {
            "active": True,
            "devices": devices,
            "host_connected": "host" in devices,
            "client_connected": "client" in devices,
        }
    return {"active": False, "devices": []}
