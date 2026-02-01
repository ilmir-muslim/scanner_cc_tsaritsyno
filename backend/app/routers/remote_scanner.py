from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict
import asyncio
from ..database import get_db
from .. import models

router = APIRouter(prefix="/ws", tags=["remote-scanner"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, Dict] = {}  # Данные сессий

    async def connect(
        self, websocket: WebSocket, session_id: str, device_type: str, db: Session
    ):
        """Подключаем устройство и сохраняем в БД"""
        await websocket.accept()

        # Находим сессию в БД
        session = (
            db.query(models.RemoteSession)
            .filter(
                models.RemoteSession.session_id == session_id,
                models.RemoteSession.is_active == True,
            )
            .first()
        )

        if not session:
            # Создаем новую сессию если её нет
            session = models.RemoteSession(
                session_id=session_id,
                is_active=True,
                expires_at=datetime.now() + timedelta(hours=1),
            )
            db.add(session)

        # Обновляем статус подключения
        if device_type == "host":
            session.host_connected = True
            session.host_websocket_id = f"{session_id}_host"
        else:
            session.client_connected = True
            session.client_websocket_id = f"{session_id}_client"

        # Обновляем время жизни сессии
        session.expires_at = datetime.now() + timedelta(hours=1)

        db.commit()

        # Сохраняем соединение
        connection_id = f"{session_id}_{device_type}"
        self.active_connections[connection_id] = websocket

        # Сохраняем данные сессии
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "host_connected": device_type == "host",
                "client_connected": device_type == "client",
                "last_activity": datetime.now(),
                "scans": [],
            }
        else:
            self.session_data[session_id][f"{device_type}_connected"] = True
            self.session_data[session_id]["last_activity"] = datetime.now()

        print(f"✅ {device_type} подключен к сессии {session_id}")
        return connection_id

    def get_session_status(self, session_id: str):
        """Получить статус сессии"""
        if session_id in self.session_data:
            return self.session_data[session_id]
        return None

    async def send_to_other_device(
        self, session_id: str, from_device: str, message: dict
    ):
        """Отправить сообщение другому устройству в сессии"""
        other_type = "client" if from_device == "host" else "host"
        other_connection_id = f"{session_id}_{other_type}"

        if other_connection_id in self.active_connections:
            try:
                await self.active_connections[other_connection_id].send_json(message)
                return True
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")
                return False
        return False


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
