from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import io

from ..database import get_db
from .. import models, schemas
from ..services.qr_service import QRService
from ..services.print_service import PrintService, print_qr_background
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/api/scans", tags=["scans"])

@router.post("/", response_model=schemas.ScanResponse)
async def create_scan(
    scan: schemas.ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register new scan and trigger print"""
    if not QRService.validate_qr_content(scan.qr_content):
        raise HTTPException(status_code=400, detail="Invalid QR content")
    
    # Create scan record
    db_scan = models.ScanRecord(
        qr_content=scan.qr_content,
        scan_source=scan.scan_source or "scanner"
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    # Генерируем QR изображение для ответа
    qr_image = QRService.generate_qr_code(scan.qr_content)
    
    # Trigger print in background
    background_tasks.add_task(print_qr_background, db_scan.id, scan.printer_id)
    
    # Возвращаем ответ с изображением QR
    return {
        "id": db_scan.id,
        "qr_content": db_scan.qr_content,
        "scan_source": db_scan.scan_source,
        "scanned_at": db_scan.scanned_at,
        "printed_at": db_scan.printed_at,
        "print_status": db_scan.print_status,
        "qr_image": qr_image
    }

@router.post("/scan-image/", response_model=schemas.ScanResponse)
async def scan_from_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Scan QR code from uploaded image (camera photo)"""
    # Читаем изображение
    image_bytes = await image.read()
    
    # Декодируем QR
    qr_content = QRService.decode_qr_from_image(image_bytes)
    
    if not qr_content:
        raise HTTPException(status_code=400, detail="No QR code found in image")
    
    # Создаем запись в базе
    db_scan = models.ScanRecord(
        qr_content=qr_content,
        scan_source="camera"
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    # Генерируем QR изображение для ответа
    qr_image = QRService.generate_qr_code(qr_content)
    
    # Trigger print in background
    background_tasks.add_task(print_qr_background, db_scan.id)
    
    return {
        "id": db_scan.id,
        "qr_content": db_scan.qr_content,
        "scan_source": db_scan.scan_source,
        "scanned_at": db_scan.scanned_at,
        "printed_at": db_scan.printed_at,
        "print_status": db_scan.print_status,
        "qr_image": qr_image
    }

@router.get("/", response_model=List[schemas.ScanResponse])
def get_scans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get scan history"""
    scans = db.query(models.ScanRecord)\
        .order_by(models.ScanRecord.scanned_at.desc())\
        .offset(skip).limit(limit).all()
    
    # Добавляем QR изображения к каждому скану
    result = []
    for scan in scans:
        scan_dict = {
            "id": scan.id,
            "qr_content": scan.qr_content,
            "scan_source": scan.scan_source,
            "scanned_at": scan.scanned_at,
            "printed_at": scan.printed_at,
            "print_status": scan.print_status,
            "qr_image": QRService.generate_qr_code(scan.qr_content)
        }
        result.append(scan_dict)
    
    return result

@router.post("/export/")
async def export_scans(
    export_request: schemas.ExportRequest,
    db: Session = Depends(get_db)
):
    """Export scans to Excel"""
    excel_service = ExcelService()
    excel_data = excel_service.create_scan_report(
        db,
        export_request.start_date,
        export_request.end_date
    )
    
    filename = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(excel_data.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/qr-image/{qr_content:path}")
async def get_qr_image(qr_content: str):
    """Generate QR code image"""
    image_data = QRService.generate_qr_code(qr_content)
    if not image_data:
        raise HTTPException(status_code=500, detail="Failed to generate QR code")
    return JSONResponse({"qr_image": image_data})