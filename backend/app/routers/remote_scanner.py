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
        """Подключаем устройство, НЕ вызываем websocket.accept() здесь!"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}

        self.active_sessions[session_id][device_type] = websocket

        # Уведомляем другую сторону о подключении
        other_type = "client" if device_type == "host" else "host"
        if other_type in self.active_sessions[session_id]:
            try:
                await self.active_sessions[session_id][other_type].send_json(
                    {
                        "type": "status",
                        "session_id": session_id,
                        "status": f"{device_type}_connected",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                print(f"Error sending status to {other_type}: {e}")

        print(f"✅ Device {device_type} connected to session {session_id}")
        return session_id

    async def disconnect(self, websocket: WebSocket, session_id: str, device_type: str):
        """Отключаем устройство"""
        if (
            session_id in self.active_sessions
            and device_type in self.active_sessions[session_id]
        ):
            del self.active_sessions[session_id][device_type]

            # Если обе стороны отключились, удаляем сессию
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]
                print(f"❌ Session {session_id} deleted (no devices)")
            else:
                # Уведомляем оставшуюся сторону об отключении
                remaining_type = "client" if device_type == "host" else "host"
                if remaining_type in self.active_sessions[session_id]:
                    try:
                        await self.active_sessions[session_id][
                            remaining_type
                        ].send_json(
                            {
                                "type": "status",
                                "session_id": session_id,
                                "status": f"{device_type}_disconnected",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        print(
                            f"⚠️ Notified {remaining_type} about {device_type} disconnect"
                        )
                    except Exception as e:
                        print(f"Error sending disconnect notification: {e}")

    async def forward_scan(self, session_id: str, qr_content: str, from_device: str):
        """Пересылает отсканированный код с телефона на компьютер"""
        if session_id in self.active_sessions:
            other_type = "host" if from_device == "client" else "client"
            if other_type in self.active_sessions[session_id]:
                try:
                    message = {
                        "type": "scan",
                        "session_id": session_id,
                        "qr_content": qr_content,
                        "device_type": from_device,
                        "timestamp": datetime.now().isoformat(),
                    }
                    await self.active_sessions[session_id][other_type].send_json(
                        message
                    )
                    print(
                        f"📱 Scan forwarded from {from_device} to {other_type}: {qr_content[:50]}..."
                    )
                    return True
                except Exception as e:
                    print(f"Error forwarding scan: {e}")
        return False


manager = ConnectionManager()


@router.websocket("/remote-scanner/{session_id}/{device_type}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, device_type: str):
    # Проверяем корректность device_type
    if device_type not in ["host", "client"]:
        print(f"❌ Invalid device_type: {device_type}")
        await websocket.close(code=1008, reason="Invalid device type")
        return

    try:
        # Принимаем соединение (только один раз!)
        await websocket.accept()
        print(f"✅ WebSocket connection accepted: {session_id} - {device_type}")

        # Подключаем устройство к менеджеру
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

        print(f"📡 WebSocket connected for {device_type} in session {session_id}")

        # Отправляем пинг каждые 30 секунд для поддержания соединения
        import asyncio

        try:
            while True:
                try:
                    # Ждем сообщение от клиента
                    data = await asyncio.wait_for(
                        websocket.receive_json(), timeout=60.0
                    )

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

                    elif data.get("type") == "disconnect":
                        print(f"Disconnect requested by {device_type}")
                        break

                except asyncio.TimeoutError:
                    # Таймаут - отправляем пинг для поддержания соединения
                    try:
                        await websocket.send_json(
                            {"type": "ping", "timestamp": datetime.now().isoformat()}
                        )
                    except:
                        break
                except Exception as e:
                    print(f"Error processing message: {e}")
                    break

        except Exception as e:
            print(f"WebSocket loop error: {e}")

    except WebSocketDisconnect:
        print(f"📡 WebSocket disconnected normally: {session_id} - {device_type}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        # Всегда отключаем устройство при выходе
        await manager.disconnect(websocket, session_id, device_type)


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Проверка статуса сессии"""
    if session_id in manager.active_sessions:
        devices = list(manager.active_sessions[session_id].keys())
        return {
            "active": True,
            "session_id": session_id,
            "devices": devices,
            "host_connected": "host" in devices,
            "client_connected": "client" in devices,
            "timestamp": datetime.now().isoformat(),
        }
    return {
        "active": False,
        "session_id": session_id,
        "devices": [],
        "host_connected": False,
        "client_connected": False,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/sessions")
async def get_all_sessions():
    """Получить все активные сессии"""
    sessions = []
    for session_id, devices in manager.active_sessions.items():
        sessions.append(
            {
                "session_id": session_id,
                "devices": list(devices.keys()),
                "host_connected": "host" in devices,
                "client_connected": "client" in devices,
            }
        )

    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
        "timestamp": datetime.now().isoformat(),
    }
