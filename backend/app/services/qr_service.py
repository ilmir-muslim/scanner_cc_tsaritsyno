import qrcode
import io
import base64
from typing import Optional
from PIL import Image
import json


class QRService:
    @staticmethod
    def generate_qr_code(content: str, size: int = 200) -> str:
        """Generate QR code and return base64 encoded image"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Конвертируем PIL Image в base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"QR generation error: {e}")
            # Возвращаем пустую картинку при ошибке
            return ""

    @staticmethod
    def decode_qr_from_image(image_bytes: bytes) -> Optional[str]:
        """Decode QR code from image bytes - placeholder for future implementation"""
        # В текущей реализации декодирование делается на фронтенде
        # Это заглушка для будущей реализации на бэкенде
        print("QR decoding is handled by frontend")
        return None

    @staticmethod
    def validate_qr_content(content: str) -> bool:
        """Validate QR code content"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 1000:  # Reasonable limit
            return False
        return True

    @staticmethod
    def create_print_json(qr_content: str) -> str:
        """Create JSON data for printing"""
        qr_image = QRService.generate_qr_code(qr_content)

        print_data = {
            "qr_content": qr_content,
            "qr_image": qr_image,
            "timestamp": json.dumps({"scanned_at": "now"}, default=str),
            "print_command": "window.print()",
        }

        return json.dumps(print_data)
