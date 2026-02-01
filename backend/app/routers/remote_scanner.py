from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict
import asyncio
from ..database import get_db
from .. import models

router = APIRouter(prefix="/ws", tags=["remote-scanner"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(
        self, websocket: WebSocket, session_id: str, device_type: str, db: Session
    ):
        """Подключаем устройство и сохраняем в БД"""
        await websocket.accept()

        # Находим или создаем сессию
        session = (
            db.query(models.RemoteSession)
            .filter(models.RemoteSession.session_id == session_id)
            .first()
        )

        if not session:
            session = models.RemoteSession(session_id=session_id, is_active=True)
            db.add(session)

        # Обновляем статус подключения
        if device_type == "host":
            session.host_connected = True
            session.host_websocket_id = f"{session_id}_host"
        else:
            session.client_connected = True
            session.client_websocket_id = f"{session_id}_client"

        db.commit()

        # Сохраняем соединение
        connection_id = f"{session_id}_{device_type}"
        self.active_connections[connection_id] = websocket

        print(f"✅ {device_type} подключен к сессии {session_id}")
        return connection_id

    async def disconnect(self, connection_id: str, db: Session):
        """Отключаем устройство и обновляем БД"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].close()
            except:
                pass
            del self.active_connections[connection_id]

        # Обновляем статус в БД
        parts = connection_id.split("_")
        if len(parts) >= 2:
            session_id = parts[0]
            device_type = parts[-1]  # 'host' или 'client'

            session = (
                db.query(models.RemoteSession)
                .filter(models.RemoteSession.session_id == session_id)
                .first()
            )

            if session:
                if device_type == "host":
                    session.host_connected = False
                    session.host_websocket_id = None
                else:
                    session.client_connected = False
                    session.client_websocket_id = None
                db.commit()

                print(f"❌ {device_type} отключен от сессии {session_id}")


manager = ConnectionManager()


@router.websocket("/remote-scanner/{session_id}/{device_type}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    device_type: str,
    db: Session = Depends(get_db),
):
    if device_type not in ["host", "client"]:
        await websocket.close(code=1008, reason="Неверный тип устройства")
        return

    try:
        connection_id = await manager.connect(websocket, session_id, device_type, db)

        # Отправляем подтверждение
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "device_type": device_type,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Уведомляем другую сторону, если она подключена
        other_type = "client" if device_type == "host" else "host"
        other_connection_id = f"{session_id}_{other_type}"

        if other_connection_id in manager.active_connections:
            try:
                await manager.active_connections[other_connection_id].send_json(
                    {
                        "type": "status",
                        "message": f"{device_type}_connected",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except:
                pass

        # Главный цикл обработки сообщений
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=300
                )  # 5 минут таймаут

                if data.get("type") == "scan":
                    # Пересылаем сканирование другой стороне
                    if other_connection_id in manager.active_connections:
                        try:
                            await manager.active_connections[
                                other_connection_id
                            ].send_json(
                                {
                                    "type": "scan",
                                    "qr_content": data.get("qr_content"),
                                    "from_device": device_type,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        except:
                            pass

                elif data.get("type") == "ping":
                    # Ответ на пинг
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )

                elif data.get("type") == "disconnect":
                    break

            except asyncio.TimeoutError:
                # Таймаут - отправляем пинг
                try:
                    await websocket.send_json(
                        {"type": "ping", "timestamp": datetime.now().isoformat()}
                    )
                except:
                    break
            except Exception as e:
                print(f"Ошибка обработки сообщения: {e}")
                break

    except WebSocketDisconnect:
        print(f"Соединение разорвано: {session_id} - {device_type}")
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
    finally:
        await manager.disconnect(connection_id, db)
