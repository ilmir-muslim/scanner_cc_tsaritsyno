import qrcode
import io
import base64
from typing import Optional
import cv2
import numpy as np
from pyzbar.pyzbar import decode


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
        """Decode QR code from image bytes"""
        try:
            # Конвертируем bytes в numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

            if img is None:
                return None

            # Декодируем QR коды
            decoded_objects = decode(img)

            if decoded_objects:
                # Возвращаем первый найденный QR код
                return decoded_objects[0].data.decode("utf-8")

            return None

        except Exception as e:
            print(f"QR decoding error: {e}")
            return None

    @staticmethod
    def validate_qr_content(content: str) -> bool:
        """Validate QR code content"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 1000:  # Reasonable limit
            return False
        return True
