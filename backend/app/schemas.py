from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ScanBase(BaseModel):
    qr_content: str
    scan_source: Optional[str] = "scanner"


class ScanCreate(ScanBase):
    printer_id: Optional[int] = None


class ScanResponse(ScanBase):
    id: int
    user_id: Optional[int]
    scanned_at: datetime
    printed_at: Optional[datetime]
    print_status: str
    qr_image: Optional[str] = None 

    class Config:
        from_attributes = True


class PrinterBase(BaseModel):
    name: str
    connection_type: str
    ip_address: Optional[str] = None
    port: Optional[int] = None


class PrinterCreate(PrinterBase):
    is_default: bool = False


class PrinterResponse(PrinterBase):
    id: int
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PrintRequest(BaseModel):
    qr_content: str
    printer_id: Optional[int] = None
    label_size: Optional[str] = "50x30"  
    copies: int = 1


class ExportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None


