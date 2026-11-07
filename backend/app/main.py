from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import connect_db, close_db
from app.routers import projects, files, jobs

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="VidCode API",
    description="AI-powered video generation platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow all origins in dev; restrict in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "env": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": settings.app_name}

