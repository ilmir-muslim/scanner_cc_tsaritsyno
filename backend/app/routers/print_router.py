from fastapi import APIRouter, HTTPException
from ..services.print_service import PrintService
from ..schemas import PrintRequest

router = APIRouter(prefix="/api/print", tags=["print"])


@router.post("/")
async def print_qr(print_request: PrintRequest):
    """Готовим данные для печати через браузер"""
    try:
        print_service = PrintService()

        print_data = await print_service.prepare_browser_print_data(
            print_request.qr_content, print_request.label_size
        )

        return {
            "success": True,
            "message": "Данные для печати готовы",
            "data": print_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка подготовки печати: {str(e)}"
        )


@router.post("/test/")
async def test_print():
    """Тестовая печать"""
    try:
        print_service = PrintService()

        test_data = await print_service.prepare_browser_print_data(
            "TEST_" + "1234567890", "50x30"
        )

        return {
            "success": True,
            "message": "Тестовые данные для печати готовы",
            "data": test_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестовой печати: {str(e)}")


@router.get("/capabilities/")
async def get_print_capabilities():
    """Получить возможности печати"""
    return {
        "browser_print": True,
        "print_dialog": True,
        "paper_sizes": ["A4", "Letter", "50x30", "70x50", "100x70"],
        "supported_formats": ["HTML", "PDF"],
        "default_printer": "Браузер по умолчанию",
        "instructions": "Используйте стандартный диалог печати вашего браузера",
    }
