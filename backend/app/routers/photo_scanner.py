from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import os
from ..services.qr_service import QRService
from ..database import get_db
from sqlalchemy.orm import Session
from .. import models

router = APIRouter(prefix="/api/photo-scanner", tags=["photo-scanner"])


@router.post("/scan-qr/")
async def scan_qr_from_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Scan QR code from uploaded photo"""
    try:
        # Проверяем файл
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Читаем байты
        image_bytes = await file.read()
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400, detail="Файл слишком большой (макс. 10MB)"
            )

        # Сохраняем во временный файл
        temp_file_path = QRService.save_temp_image(image_bytes)
        if not temp_file_path:
            raise HTTPException(status_code=500, detail="Ошибка сохранения файла")

        # Распознаем QR-код
        qr_content = QRService.decode_qr_from_bytes(image_bytes)

        # Сохраняем запись о сканировании
        photo_scan = models.PhotoScan(
            filename=file.filename,
            file_path=temp_file_path,
            qr_content=qr_content,
            session_id=session_id,
            is_processed=bool(qr_content),
            processed_at=datetime.now() if qr_content else None,
        )

        db.add(photo_scan)
        db.commit()
        db.refresh(photo_scan)

        # Планируем удаление файла через 5 минут
        background_tasks.add_task(delete_file_later, temp_file_path)

        # Если найден QR-код и это сессия, проверяем ее
        if qr_content and qr_content.isdigit() and len(qr_content) == 6:
            session = (
                db.query(models.RemoteSession)
                .filter(
                    models.RemoteSession.session_id == qr_content,
                    models.RemoteSession.is_active == True,
                )
                .first()
            )

            if session:
                return {
                    "success": True,
                    "type": "session_connect",
                    "session_id": qr_content,
                    "session_exists": True,
                    "session_active": session.is_active,
                    "host_connected": session.host_connected,
                    "message": "QR-код сессии найден. Подключайтесь!",
                }

        return {
            "success": bool(qr_content),
            "qr_content": qr_content,
            "message": "QR-код найден" if qr_content else "QR-код не найден на фото",
            "scan_id": photo_scan.id,
            "filename": file.filename,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки фото: {str(e)}")


@router.post("/connect/{session_id}")
async def connect_to_session_from_qr(session_id: str, db: Session = Depends(get_db)):
    """Connect to session using QR code data"""
    try:
        session = (
            db.query(models.RemoteSession)
            .filter(
                models.RemoteSession.session_id == session_id,
                models.RemoteSession.is_active == True,
            )
            .first()
        )

        if not session:
            # Создаем новую сессию
            session = models.RemoteSession(
                session_id=session_id,
                is_active=True,
                expires_at=datetime.now() + timedelta(hours=1),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            message = "Новая сессия создана"
        else:
            message = "Сессия найдена"

        return {
            "success": True,
            "session_id": session_id,
            "session_exists": True,
            "host_connected": session.host_connected,
            "message": message,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка подключения к сессии: {str(e)}"
        )


async def delete_file_later(file_path: str):
    """Delete file after delay"""
    import asyncio

    await asyncio.sleep(300)  # 5 минут
    QRService.delete_file(file_path)


@router.get("/scans/")
async def get_photo_scans(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    """Get photo scan history"""
    scans = (
        db.query(models.PhotoScan)
        .order_by(models.PhotoScan.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": scan.id,
            "filename": scan.filename,
            "qr_content": scan.qr_content,
            "session_id": scan.session_id,
            "created_at": scan.created_at.isoformat(),
            "processed_at": (
                scan.processed_at.isoformat() if scan.processed_at else None
            ),
            "is_processed": scan.is_processed,
        }
        for scan in scans
    ]


@router.post("/process-photo/")
async def process_photo_and_connect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Обработка фото с QR-кодом и подключение к сессии"""
    try:
        # Проверяем файл
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Читаем байты
        image_bytes = await file.read()

        # Сохраняем временный файл
        temp_file_path = QRService.save_temp_image(image_bytes)

        # Распознаем QR-код
        qr_content = QRService.decode_qr_from_bytes(image_bytes)

        if not qr_content:
            # Пробуем улучшить изображение
            enhanced_image = QRService.enhance_image(image_bytes)
            qr_content = QRService.decode_qr_from_bytes(enhanced_image)

        if not qr_content:
            raise HTTPException(status_code=400, detail="QR-код не найден на фото")

        # Парсим URL если это ссылка
        import urllib.parse

        parsed_url = urllib.parse.urlparse(qr_content)

        # Извлекаем session_id из URL параметров
        query_params = urllib.parse.parse_qs(parsed_url.query)
        extracted_session_id = query_params.get("session", [None])[0]

        # Используем извлеченный session_id или переданный
        target_session_id = extracted_session_id or session_id

        if not target_session_id:
            raise HTTPException(
                status_code=400, detail="Session ID не найден в QR-коде"
            )

        # Проверяем существование сессии
        session = (
            db.query(models.RemoteSession)
            .filter(
                models.RemoteSession.session_id == target_session_id,
                models.RemoteSession.is_active == True,
            )
            .first()
        )

        if not session:
            # Создаем сессию если её нет
            session = models.RemoteSession(
                session_id=target_session_id,
                client_connected=True,
                is_active=True,
                expires_at=datetime.now() + timedelta(hours=1),
            )
            db.add(session)
            db.commit()
            message = "Новая сессия создана"
        else:
            # Обновляем сессию
            session.client_connected = True
            session.expires_at = datetime.now() + timedelta(hours=1)
            db.commit()
            message = "Подключено к существующей сессии"

        # Сохраняем запись о сканировании
        photo_scan = models.PhotoScan(
            filename=file.filename,
            file_path=temp_file_path,
            qr_content=qr_content,
            session_id=target_session_id,
            is_processed=True,
            processed_at=datetime.now(),
        )

        db.add(photo_scan)
        db.commit()

        # Планируем удаление файла
        background_tasks.add_task(QRService.delete_file, temp_file_path)

        return {
            "success": True,
            "message": message,
            "session_id": target_session_id,
            "qr_content": qr_content,
            "session_exists": True,
            "connected": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки фото: {str(e)}")
