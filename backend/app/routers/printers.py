from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
def create_printer(printer: schemas.PrinterCreate, db: Session = Depends(get_db)):
    """Register new printer"""
    try:
        if not printer.name:
            raise HTTPException(status_code=400, detail="Имя принтера обязательно")

        existing_printer = (
            db.query(models.Printer).filter(models.Printer.name == printer.name).first()
        )
        if existing_printer:
            raise HTTPException(
                status_code=400, detail="Принтер с таким именем уже существует"
            )

        # Если устанавливаем принтер по умолчанию, снимаем флаг с других
        if printer.is_default:
            db.query(models.Printer).update({models.Printer.is_default: False})

        db_printer = models.Printer(
            name=printer.name,
            connection_type=printer.connection_type,
            ip_address=printer.ip_address,
            port=printer.port,
            is_default=printer.is_default,
            is_active=True,
        )

        db.add(db_printer)
        db.commit()
        db.refresh(db_printer)

        return db_printer

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания принтера: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания принтера: {str(e)}"
        )


@router.get("/", response_model=List[schemas.PrinterResponse])
def get_printers(db: Session = Depends(get_db)):
    """Get all printers"""
    return db.query(models.Printer).filter(models.Printer.is_active == True).all()


@router.get("/default")
def get_default_printer(db: Session = Depends(get_db)):
    """Get default printer"""
    printer = (
        db.query(models.Printer)
        .filter(models.Printer.is_default == True)
        .filter(models.Printer.is_active == True)
        .first()
    )

    if not printer:
        # Создаем браузерный принтер по умолчанию, если нет других
        browser_printer = models.Printer(
            name="Браузерная печать",
            connection_type="browser",
            is_default=True,
            is_active=True,
        )
        db.add(browser_printer)
        db.commit()
        db.refresh(browser_printer)
        printer = browser_printer

    return printer


@router.post("/test/{printer_id}")
async def test_printer(printer_id: int, db: Session = Depends(get_db)):
    """Test printer connection - для браузерной печати просто возвращаем успех"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    return {
        "status": "success",
        "message": f"Браузерный принтер '{printer.name}' готов к работе",
        "printer": printer.name,
    }


@router.put("/{printer_id}", response_model=schemas.PrinterResponse)
def update_printer(
    printer_id: int,
    printer_update: schemas.PrinterCreate,
    db: Session = Depends(get_db),
):
    """Update printer settings"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    if printer_update.is_default:
        db.query(models.Printer).update({models.Printer.is_default: False})

    for key, value in printer_update.dict().items():
        setattr(printer, key, value)

    db.commit()
    db.refresh(printer)
    return printer


@router.delete("/{printer_id}")
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    """Delete printer"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    if printer.is_default:
        other_printer = (
            db.query(models.Printer)
            .filter(models.Printer.id != printer_id, models.Printer.is_active == True)
            .first()
        )

        if other_printer:
            other_printer.is_default = True

    db.delete(printer)
    db.commit()

    return {"status": "success", "message": "Printer deleted"}


@router.post("/scan/")
async def scan_network():
    """Упрощенное сканирование - возвращает только браузерный принтер"""
    return {
        "status": "success",
        "message": "Используется браузерная печать по умолчанию",
        "discovered": [
            {
                "name": "Браузерная печать",
                "type": "browser",
                "status": "available",
                "description": "Печать через диалог браузера",
            }
        ],
    }


@router.post("/auto-configure")
async def auto_configure_printers(db: Session = Depends(get_db)):
    """Автоматическая настройка - только браузерный принтер"""
    try:
        # Проверяем, есть ли уже браузерный принтер
        existing_browser_printer = (
            db.query(models.Printer)
            .filter(
                models.Printer.connection_type == "browser",
                models.Printer.is_active == True,
            )
            .first()
        )

        if existing_browser_printer:
            if not existing_browser_printer.is_default:
                existing_browser_printer.is_default = True
                db.commit()

            return {
                "status": "success",
                "message": "Браузерная печать уже настроена",
                "default_printer": {
                    "id": existing_browser_printer.id,
                    "name": existing_browser_printer.name,
                    "ip": None,
                    "port": None,
                    "connection_type": "browser",
                },
            }

        # Создаем новый браузерный принтер
        browser_printer = models.Printer(
            name="Браузерная печать",
            connection_type="browser",
            is_default=True,
            is_active=True,
        )
        db.add(browser_printer)
        db.commit()
        db.refresh(browser_printer)

        return {
            "status": "success",
            "message": "Браузерная печать настроена по умолчанию",
            "default_printer": {
                "id": browser_printer.id,
                "name": browser_printer.name,
                "ip": None,
                "port": None,
                "connection_type": "browser",
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка настройки: {str(e)}",
            "default_printer": None,
        }
