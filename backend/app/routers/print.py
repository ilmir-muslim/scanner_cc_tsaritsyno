from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Optional
from ..services.print_service import PrintService
from ..schemas import PrintRequest

router = APIRouter(prefix="/api/print", tags=["print"])


@router.post("/")
async def print_qr(print_request: PrintRequest):
    """Print QR code"""
    try:
        print_service = PrintService()

        # Подготавливаем данные для печати
        print_data = await print_service.print_via_browser(
            print_request.qr_content, print_request.label_size
        )

        return {"success": True, "message": "Print job prepared", "data": print_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Print error: {str(e)}")


@router.post("/test/")
async def test_print():
    """Test printer connection"""
    try:
        print_service = PrintService()

        # Тестовая печать
        test_data = await print_service.print_via_browser(
            "TEST_QR_" + datetime.now().strftime("%Y%m%d%H%M%S"), "50x30"
        )

        return {
            "success": True,
            "message": "Test print job prepared",
            "data": test_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test print error: {str(e)}")
