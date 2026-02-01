import qrcode
import io
import base64
from typing import Optional
from PIL import Image
import json
import os
import tempfile
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode
import numpy as np


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

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"QR generation error: {e}")
            return ""

    @staticmethod
    def decode_qr_from_bytes(image_bytes: bytes) -> Optional[str]:
        """Decode QR code from image bytes using OpenCV and pyzbar"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

            if img is None:
                print("Failed to decode image")
                return None

            # Enhance contrast
            img = cv2.equalizeHist(img)

            # Decode QR codes
            decoded_objects = decode(img)

            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    print(f"Found QR code: {qr_data}")
                    return qr_data

            print("No QR code found in image")
            return None

        except Exception as e:
            print(f"QR decoding error: {e}")
            return None

    @staticmethod
    def decode_qr_from_file(file_path: str) -> Optional[str]:
        """Decode QR code from file path"""
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            return QRService.decode_qr_from_bytes(image_bytes)
        except Exception as e:
            print(f"File decoding error: {e}")
            return None

    @staticmethod
    def validate_qr_content(content: str) -> bool:
        """Validate QR code content"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 1000:
            return False
        return True

    @staticmethod
    def save_temp_image(image_bytes: bytes) -> str:
        """Save image to temp file and return path"""
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"qr_scan_{timestamp}.jpg"
            file_path = os.path.join(temp_dir, filename)

            with open(file_path, "wb") as f:
                f.write(image_bytes)

            return file_path

        except Exception as e:
            print(f"Error saving temp image: {e}")
            return ""

    @staticmethod
    def delete_file(file_path: str):
        """Delete file if exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file: {e}")
