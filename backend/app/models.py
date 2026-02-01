from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )


class ScanRecord(Base):
    __tablename__ = "scan_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    qr_content: Mapped[str] = mapped_column(Text, nullable=False)
    scan_source: Mapped[str] = mapped_column(String(50)) 
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    printed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    print_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  

    user: Mapped["User"] = relationship("User")


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    connection_type: Mapped[str] = mapped_column(String(50))  
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
