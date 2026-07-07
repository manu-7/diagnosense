from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import ai, auth, bookings, centers, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # place any cleanup (e.g. closing redis pool) here on shutdown


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade AI-powered diagnostic center booking & report analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(centers.router)
app.include_router(bookings.router)
app.include_router(reports.router)
app.include_router(ai.router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
