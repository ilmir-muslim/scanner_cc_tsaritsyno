from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import socket
import asyncio

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
def create_printer(printer: schemas.PrinterCreate, db: Session = Depends(get_db)):
    """Register new printer"""
    try:
        # Валидация данных
        if not printer.name:
            raise HTTPException(status_code=400, detail="Имя принтера обязательно")

        # Проверяем, не существует ли уже принтер с таким именем
        existing_printer = (
            db.query(models.Printer).filter(models.Printer.name == printer.name).first()
        )
        if existing_printer:
            raise HTTPException(
                status_code=400, detail="Принтер с таким именем уже существует"
            )

        # Проверяем для сетевых принтеров
        if printer.connection_type == "network":
            if not printer.ip_address:
                raise HTTPException(
                    status_code=400, detail="IP адрес обязателен для сетевого принтера"
                )

            # Проверяем, не существует ли уже принтер с таким IP
            existing_ip = (
                db.query(models.Printer)
                .filter(
                    models.Printer.ip_address == printer.ip_address,
                    models.Printer.connection_type == "network",
                )
                .first()
            )
            if existing_ip:
                raise HTTPException(
                    status_code=400, detail="Принтер с таким IP уже существует"
                )

        # Если устанавливаем как принтер по умолчанию, снимаем флаг с других
        if printer.is_default:
            db.query(models.Printer).update({models.Printer.is_default: False})

        # Создаем новый принтер
        db_printer = models.Printer(
            name=printer.name,
            connection_type=printer.connection_type,
            ip_address=printer.ip_address,
            port=printer.port,
            is_default=printer.is_default,
            is_active=True,
        )

        db.add(db_printer)
        db.commit()
        db.refresh(db_printer)

        return db_printer

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания принтера: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания принтера: {str(e)}"
        )


@router.get("/", response_model=List[schemas.PrinterResponse])
def get_printers(db: Session = Depends(get_db)):
    """Get all printers"""
    return db.query(models.Printer).filter(models.Printer.is_active == True).all()


@router.get("/default")
def get_default_printer(db: Session = Depends(get_db)):
    """Get default printer - только для сканирования"""
    printer = (
        db.query(models.Printer)
        .filter(models.Printer.is_default == True)
        .filter(models.Printer.is_active == True)
        .first()
    )

    if not printer:
        return None

    return printer


@router.post("/test/{printer_id}")
async def test_printer(printer_id: int, db: Session = Depends(get_db)):
    """Test printer connection"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    # For network printers, test connection
    if printer.connection_type == "network" and printer.ip_address:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((printer.ip_address, printer.port or 9100))
            sock.close()

            if result == 0:
                return {
                    "status": "success",
                    "message": f"Принтер {printer.name} доступен",
                    "printer": printer.name,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Не удалось подключиться к принтеру {printer.name}",
                    "printer": printer.name,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}",
                "printer": printer.name,
            }

    # For other printer types
    return {
        "status": "test_sent",
        "message": "Тестовое задание отправлено",
        "printer": printer.name,
    }


@router.put("/{printer_id}", response_model=schemas.PrinterResponse)
def update_printer(
    printer_id: int,
    printer_update: schemas.PrinterCreate,
    db: Session = Depends(get_db),
):
    """Update printer settings"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    # If setting as default, unset other defaults
    if printer_update.is_default:
        db.query(models.Printer).update({models.Printer.is_default: False})

    # Update printer fields
    for key, value in printer_update.dict().items():
        setattr(printer, key, value)

    db.commit()
    db.refresh(printer)
    return printer


@router.delete("/{printer_id}")
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    """Delete printer"""
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    # If deleting default printer, set another as default
    if printer.is_default:
        other_printer = (
            db.query(models.Printer)
            .filter(models.Printer.id != printer_id, models.Printer.is_active == True)
            .first()
        )

        if other_printer:
            other_printer.is_default = True

    db.delete(printer)
    db.commit()

    return {"status": "success", "message": "Printer deleted"}


@router.post("/scan/")
async def scan_network():
    """Scan network for printers using HTTP"""
    import socket
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    discovered = []
    
    # Определяем популярные подсети для сканирования
    subnets = ["192.168.1", "192.168.0", "10.0.0"]
    ports = [9100, 631, 515]  # Стандартные порты принтеров
    
    def check_ip_port(ip, port):
        """Проверяет доступность IP и порта"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Таймаут 0.5 секунды
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    # Используем ThreadPoolExecutor для параллельной проверки
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        for subnet in subnets:
            # Сканируем только первые 20 адресов в каждой подсети для скорости
            for i in range(1, 21):
                ip = f"{subnet}.{i}"
                for port in ports:
                    futures.append(executor.submit(check_ip_port, ip, port, (ip, port)))
        
        # Обрабатываем результаты
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                if result:
                    ip, port = result[1]  # Извлекаем IP и порт
                    discovered.append({
                        "ip": ip,
                        "port": port,
                        "name": f"Сетевой принтер {ip}:{port}",
                        "status": "online"
                    })
            except Exception as e:
                continue
    
    return {
        "status": "success",
        "message": f"Сканирование завершено. Найдено {len(discovered)} устройств.",
        "discovered": discovered
    }


@router.post("/scan-simple/")
async def scan_simple():
    """Упрощенное сканирование для быстрого теста"""
    import socket
    
    discovered = []
    
    # Только самые популярные адреса
    test_configs = [
        {"ip": "192.168.1.100", "port": 9100},
        {"ip": "192.168.0.100", "port": 9100},
        {"ip": "10.0.0.100", "port": 9100},
        {"ip": "192.168.1.101", "port": 9100},
        {"ip": "192.168.0.101", "port": 9100},
    ]
    
    for config in test_configs:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((config["ip"], config["port"]))
            sock.close()
            
            if result == 0:
                discovered.append({
                    "ip": config["ip"],
                    "port": config["port"],
                    "name": f"Принтер {config['ip']}",
                    "status": "online"
                })
        except:
            continue
    
    return {
        "status": "success",
        "message": f"Быстрое сканирование завершено. Найдено {len(discovered)} устройств.",
        "discovered": discovered
    }


@router.post("/auto-configure")
async def auto_configure_printers(db: Session = Depends(get_db)):
    """Автоматическая настройка принтеров"""
    try:
        # Проверяем, есть ли уже принтеры
        existing_printers = (
            db.query(models.Printer).filter(models.Printer.is_active == True).all()
        )

        if existing_printers:
            # Используем существующий принтер
            default_printer = next(
                (p for p in existing_printers if p.is_default), existing_printers[0]
            )

            return {
                "status": "info",
                "message": f"Используется существующий принтер '{default_printer.name}'.",
                "default_printer": {
                    "id": default_printer.id,
                    "name": default_printer.name,
                    "ip": default_printer.ip_address,
                    "port": default_printer.port,
                    "connection_type": default_printer.connection_type,
                },
            }

        # Если ничего нет, создаем браузерный принтер
        browser_printer = models.Printer(
            name="Браузерная печать",
            connection_type="browser",
            is_default=True,
            is_active=True,
        )
        db.add(browser_printer)
        db.commit()

        return {
            "status": "success",
            "message": "Установлена браузерная печать по умолчанию.",
            "default_printer": {
                "id": browser_printer.id,
                "name": browser_printer.name,
                "ip": None,
                "port": None,
                "connection_type": "browser",
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка автоматической настройки: {str(e)}",
            "default_printer": None,
        }
