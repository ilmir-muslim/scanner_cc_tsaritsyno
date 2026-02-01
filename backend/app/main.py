from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from .database import engine, Base
from .config import settings
from .routers import scans, printers, print_router
from .routers import remote_scanner


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting QR Replication System...")
    Base.metadata.create_all(bind=engine)
    yield
    print("Shutting down...")


app = FastAPI(
    title="QR Replication System",
    description="Система репликации и логирования QR-кодов",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(print_router.router)
app.include_router(remote_scanner.router)


@app.get("/")
async def root():
    return {"message": "QR Replication System API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qr-system"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
