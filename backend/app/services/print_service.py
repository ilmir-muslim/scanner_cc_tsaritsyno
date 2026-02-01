import json
from datetime import datetime
from typing import Optional, Dict
import base64
import io

from ..database import SessionLocal
from .. import models
from .qr_service import QRService


class PrintService:
    def __init__(self):
        pass

    async def prepare_browser_print_data(
        self, qr_content: str, label_size: str = "50x30"
    ) -> Dict:
        """Prepare data for browser printing"""
        qr_image = QRService.generate_qr_code(qr_content, 200)

        # Создаем HTML для печати
        html_content = self._create_print_html(qr_content, qr_image)

        return {
            "qr_image": qr_image,
            "qr_content": qr_content,
            "label_size": label_size,
            "timestamp": datetime.now().isoformat(),
            "html_content": html_content,
            "print_command": "window.print()",
        }

    def _create_print_html(self, qr_content: str, qr_image: str) -> str:
        """Create HTML content for printing"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Печать QR-кода</title>
            <style>
                @media print {{
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                    .no-print {{
                        display: none !important;
                    }}
                }}
                
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    text-align: center;
                }}
                
                .qr-container {{
                    margin: 20px auto;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    max-width: 400px;
                }}
                
                .qr-image {{
                    width: 300px;
                    height: 300px;
                    margin: 20px auto;
                    display: block;
                }}
                
                .qr-content {{
                    margin-top: 20px;
                    padding: 10px;
                    background: #f5f5f5;
                    border-radius: 4px;
                    word-break: break-all;
                    font-family: monospace;
                }}
                
                .print-info {{
                    margin-top: 10px;
                    color: #666;
                    font-size: 12px;
                }}
                
                .print-button {{
                    margin: 20px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div class="qr-container">
                <h2>QR-код для печати</h2>
                <img src="{qr_image}" alt="QR Code" class="qr-image" />
                <div class="qr-content">
                    <strong>Содержимое:</strong><br>
                    {qr_content}
                </div>
                <div class="print-info">
                    Отсканировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
                </div>
            </div>
            
            <button class="print-button no-print" onclick="window.print()">
                🖨️ Печатать
            </button>
            <button class="print-button no-print" onclick="window.close()">
                ✖️ Закрыть
            </button>
            
            <script>
                // Автоматически открываем диалог печати без подтверждения
                window.onload = function() {{
                    setTimeout(function() {{
                        window.print();
                    }}, 500);
                }};
                
                // Закрываем окно после печати
                window.onafterprint = function() {{
                    setTimeout(function() {{
                        window.close();
                    }}, 1000);
                }};
            </script>
        </body>
        </html>
        """

    def generate_print_job(self, qr_content: str) -> Dict:
        """Generate print job data"""
        return {
            "type": "browser_print",
            "qr_content": qr_content,
            "timestamp": datetime.now().isoformat(),
            "instructions": "Используйте стандартный диалог печати браузера",
        }


async def print_qr_background(scan_id: int, printer_id: Optional[int] = None):
    """Background task to print QR code - теперь только логирование"""
    db = SessionLocal()
    try:
        scan = (
            db.query(models.ScanRecord).filter(models.ScanRecord.id == scan_id).first()
        )
        if not scan:
            return

        # Для браузерной печати просто помечаем как готовый к печати
        scan.print_status = "pending"
        db.commit()

        print(f"Scan {scan_id} готов к печати через браузер. QR: {scan.qr_content}")

    except Exception as e:
        print(f"Ошибка подготовки к печати: {e}")
        try:
            scan.print_status = "failed"
            db.commit()
        except:
            pass
    finally:
        db.close()
