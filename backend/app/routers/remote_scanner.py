from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import Dict
import asyncio

router = APIRouter(prefix="/ws", tags=["remote-scanner"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_pairs: Dict[str, Dict[str, str]] = (
            {}
        )  # session_id -> {host: conn_id, client: conn_id}

    async def connect(self, websocket: WebSocket, session_id: str, device_type: str):
        """Подключаем устройство"""
        await websocket.accept()
        connection_id = f"{session_id}_{device_type}"
        self.active_connections[connection_id] = websocket

        # Инициализируем сессию если нужно
        if session_id not in self.session_pairs:
            self.session_pairs[session_id] = {}

        # Сохраняем подключение
        self.session_pairs[session_id][device_type] = connection_id

        print(f"✅ {device_type} подключен к сессии {session_id}")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Отключаем устройство"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].close()
            except:
                pass
            del self.active_connections[connection_id]

        # Находим и удаляем из сессии
        for session_id, devices in self.session_pairs.items():
            for device_type, conn_id in list(devices.items()):
                if conn_id == connection_id:
                    if device_type in devices:
                        del devices[device_type]
                    print(f"❌ {device_type} отключен от сессии {session_id}")

                    # Уведомляем другую сторону если она подключена
                    other_type = "client" if device_type == "host" else "host"
                    if other_type in self.session_pairs[session_id]:
                        other_conn_id = self.session_pairs[session_id][other_type]
                        if other_conn_id in self.active_connections:
                            try:
                                await self.active_connections[other_conn_id].send_json(
                                    {
                                        "type": "status",
                                        "message": f"{device_type}_disconnected",
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                            except:
                                pass

    async def send_to_other(self, session_id: str, from_device: str, message: dict):
        """Отправляем сообщение другой стороне"""
        other_type = "client" if from_device == "host" else "host"

        if (
            session_id in self.session_pairs
            and other_type in self.session_pairs[session_id]
        ):
            other_conn_id = self.session_pairs[session_id][other_type]
            if other_conn_id in self.active_connections:
                try:
                    await self.active_connections[other_conn_id].send_json(message)
                    return True
                except:
                    return False
        return False


manager = ConnectionManager()


@router.websocket("/remote-scanner/{session_id}/{device_type}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, device_type: str):
    if device_type not in ["host", "client"]:
        await websocket.close(code=1008, reason="Invalid device type")
        return

    try:
        # Подключаемся
        connection_id = await manager.connect(websocket, session_id, device_type)

        # Отправляем подтверждение подключения
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Уведомляем другую сторону если она уже подключена
        other_type = "client" if device_type == "host" else "host"
        if (
            session_id in manager.session_pairs
            and other_type in manager.session_pairs[session_id]
        ):
            other_conn_id = manager.session_pairs[session_id][other_type]
            if other_conn_id in manager.active_connections:
                # Уведомляем новую сторону о существующей
                await websocket.send_json(
                    {
                        "type": "status",
                        "message": f"{other_type}_already_connected",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Уведомляем существующую о новой
                await manager.active_connections[other_conn_id].send_json(
                    {
                        "type": "status",
                        "message": f"{device_type}_connected",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Обрабатываем сообщения
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "scan" and data.get("qr_content"):
                    # Пересылаем сканирование другой стороне
                    await manager.send_to_other(
                        session_id,
                        device_type,
                        {
                            "type": "scan",
                            "qr_content": data["qr_content"],
                            "from_device": device_type,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                elif data.get("type") == "ping":
                    # Отвечаем на пинг
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "disconnect":
                    break

            except Exception as e:
                print(f"Ошибка обработки сообщения: {e}")
                break

    except WebSocketDisconnect:
        print(f"Соединение разорвано: {session_id} - {device_type}")
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        await manager.disconnect(connection_id)


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Проверка статуса сессии"""
    if session_id in manager.session_pairs:
        devices = list(manager.session_pairs[session_id].keys())
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
    for session_id, devices in manager.session_pairs.items():
        sessions.append({"session_id": session_id, "devices": list(devices.keys())})

    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
        "timestamp": datetime.now().isoformat(),
    }
