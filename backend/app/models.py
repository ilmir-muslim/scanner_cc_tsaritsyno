from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
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


class RemoteSession(Base):
    __tablename__ = "remote_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(6), unique=True, index=True
    )  # 6-значный ID
    host_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    client_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now() + timedelta(hours=1)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Для восстановления подключений
    host_websocket_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_websocket_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class PhotoScan(Base):
    __tablename__ = "photo_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    qr_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
