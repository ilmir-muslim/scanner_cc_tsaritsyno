import socket
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict
import os

from ..database import SessionLocal
from .. import models
from .qr_service import QRService


class PrintService:
    def __init__(self):
        self.connected_printers = {}

    async def print_to_network_printer(
        self, qr_content: str, printer_ip: str, port: int = 9100
    ) -> bool:
        """Send print job to network printer (ZPL or similar)"""
        try:
            # Генерируем ZPL код для QR
            zpl_code = self._generate_zpl_for_qr(qr_content)

            # Отправляем на принтер
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((printer_ip, port))
                sock.sendall(zpl_code.encode())
                sock.close()

            return True
        except Exception as e:
            print(f"Print error: {e}")
            return False

    def _generate_zpl_for_qr(self, content: str) -> str:
        """Generate ZPL code for QR printing"""
        zpl = f"""
^XA
^FO20,20
^BQN,2,10
^FDMA,{content}
^FS
^FO20,150
^A0N,30,30
^FD{content[:30]}
^FS
^XZ
"""
        return zpl

    async def print_via_browser(
        self, qr_content: str, label_size: str = "50x30"
    ) -> Dict:
        """Prepare data for browser printing"""
        qr_image = QRService.generate_qr_code(qr_content, 150)

        return {
            "qr_image": qr_image,
            "content": qr_content,
            "label_size": label_size,
            "timestamp": datetime.now().isoformat(),
            "print_command": "window.print()",
        }

    async def test_printer_connection(self, printer_ip: str, port: int = 9100) -> bool:
        """Test if printer is reachable"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                result = sock.connect_ex((printer_ip, port))
                return result == 0
        except:
            return False


async def print_qr_background(scan_id: int, printer_id: Optional[int] = None):
    """Background task to print QR code"""
    db = SessionLocal()
    try:
        scan = (
            db.query(models.ScanRecord).filter(models.ScanRecord.id == scan_id).first()
        )
        if not scan:
            return

        print_service = PrintService()

        # Получаем принтер из базы если указан printer_id
        printer = None
        if printer_id:
            printer = (
                db.query(models.Printer)
                .filter(
                    models.Printer.id == printer_id, models.Printer.is_active == True
                )
                .first()
            )

        # Если принтер не указан, используем принтер по умолчанию
        if not printer:
            printer = (
                db.query(models.Printer)
                .filter(
                    models.Printer.is_default == True, models.Printer.is_active == True
                )
                .first()
            )

        print_status = "failed"

        if printer and printer.connection_type == "network" and printer.ip_address:
            # Печать на сетевой принтер
            success = await print_service.print_to_network_printer(
                scan.qr_content, printer.ip_address, printer.port or 9100
            )
            print_status = "success" if success else "failed"
        else:
            # Для других типов принтеров или браузерной печати
            # Просто отмечаем как успех, т.к. браузер сам печатает
            print_status = "success"

        # Обновляем статус в базе
        scan.print_status = print_status
        scan.printed_at = datetime.utcnow()
        db.commit()

        print(f"Background print completed for scan {scan_id}: {print_status}")

    except Exception as e:
        print(f"Background print failed: {e}")
        # Обновляем статус на failed при ошибке
        try:
            scan.print_status = "failed"
            db.commit()
        except:
            pass
    finally:
        db.close()
