from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .config import settings
from .routers import scans, printers, remote_scanner, photo_scanner, sessions

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QR Replication System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans.router)
app.include_router(printers.router)
app.include_router(remote_scanner.router)
app.include_router(photo_scanner.router)
app.include_router(sessions.router)


@app.get("/")
async def root():
    return {"message": "QR Replication System API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
