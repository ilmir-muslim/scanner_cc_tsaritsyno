from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
def create_printer(printer: schemas.PrinterCreate, db: Session = Depends(get_db)):
    """Register new printer"""
    # If setting as default, unset other defaults
    if printer.is_default:
        db.query(models.Printer).update({models.Printer.is_default: False})

    db_printer = models.Printer(**printer.dict())
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer


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
        # Return a dummy printer for browser printing
        return {
            "name": "Browser Printer",
            "connection_type": "browser",
            "is_default": True,
        }

    return printer


@router.post("/test/{printer_id}")
async def test_printer(printer_id: int, db: Session = Depends(get_db)):
    """Test printer connection"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    # Test connection logic here
    return {"status": "test_sent", "printer": printer.name}
