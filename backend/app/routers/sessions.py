from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
import json

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Хранилище активных сессий
active_sessions: Dict[str, Dict] = {}


@router.post("/create")
async def create_session(session_data: dict, db: Session = Depends(get_db)):
    """Создание новой сессии"""
    try:
        session_id = session_data.get("session_id")

        # Проверяем, существует ли уже сессия
        existing_session = (
            db.query(models.RemoteSession)
            .filter(models.RemoteSession.session_id == session_id)
            .first()
        )

        if existing_session and existing_session.is_active:
            # Обновляем время жизни существующей сессии
            existing_session.expires_at = datetime.now() + timedelta(hours=1)
            db.commit()

            return {
                "success": True,
                "message": "Сессия уже существует",
                "session_id": session_id,
                "existing": True,
            }

        # Создаем новую сессию
        new_session = models.RemoteSession(
            session_id=session_id,
            host_connected=True,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            is_active=True,
        )

        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        # Сохраняем в активных сессиях
        active_sessions[session_id] = {
            "host_connected": True,
            "client_connected": False,
            "created_at": datetime.now(),
            "scans": [],
        }

        return {
            "success": True,
            "message": "Сессия создана",
            "session_id": session_id,
            "created": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания сессии: {str(e)}")


@router.get("/{session_id}/status")
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Получить статус сессии"""
    session = (
        db.query(models.RemoteSession)
        .filter(models.RemoteSession.session_id == session_id)
        .first()
    )

    if not session:
        return {"exists": False, "active": False, "message": "Сессия не найдена"}

    return {
        "exists": True,
        "active": session.is_active,
        "host_connected": session.host_connected,
        "client_connected": session.client_connected,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
    }


@router.post("/{session_id}/connect-client")
async def connect_client_to_session(session_id: str, db: Session = Depends(get_db)):
    """Подключение клиента (телефона) к сессии"""
    session = (
        db.query(models.RemoteSession)
        .filter(
            models.RemoteSession.session_id == session_id,
            models.RemoteSession.is_active == True,
        )
        .first()
    )

    if not session:
        return {"success": False, "message": "Сессия не найдена или не активна"}

    # Обновляем статус подключения клиента
    session.client_connected = True
    session.expires_at = datetime.now() + timedelta(hours=1)  # Обновляем время жизни
    db.commit()

    # Обновляем активную сессию
    if session_id in active_sessions:
        active_sessions[session_id]["client_connected"] = True

    return {
        "success": True,
        "message": "Клиент подключен",
        "host_connected": session.host_connected,
    }


@router.post("/{session_id}/disconnect")
async def disconnect_session(session_id: str, db: Session = Depends(get_db)):
    """Отключение сессии"""
    session = (
        db.query(models.RemoteSession)
        .filter(models.RemoteSession.session_id == session_id)
        .first()
    )

    if session:
        session.is_active = False
        session.host_connected = False
        session.client_connected = False
        db.commit()

    # Удаляем из активных сессий
    if session_id in active_sessions:
        del active_sessions[session_id]

    return {"success": True, "message": "Сессия отключена"}


@router.get("/active/list")
async def list_active_sessions(db: Session = Depends(get_db)):
    """Список активных сессий"""
    active = (
        db.query(models.RemoteSession)
        .filter(
            models.RemoteSession.is_active == True,
            models.RemoteSession.expires_at > datetime.now(),
        )
        .all()
    )

    return [
        {
            "session_id": session.session_id,
            "host_connected": session.host_connected,
            "client_connected": session.client_connected,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
        }
        for session in active
    ]
