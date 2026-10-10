from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Offline-first pilgrim-trail safety system for Himachal Pradesh",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.PUBLIC_ORIGIN],
    expose_headers=["Date"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RFC 7807 Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("yatra").error("Request failed: %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred."
        }
    )

from app.routers import yatras, groups, checkins, auth, dashboard, safety

app.include_router(yatras.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(checkins.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(safety.router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint required by sprint acceptance checks."""
    from app.db import AsyncSessionLocal
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/v1", tags=["System"])
async def api_root():
    return {
        "message": "Welcome to Yatra Kavach API v1",
        "docs_url": "/docs",
        "health": "/health"
    }

from app.services.security import security_middleware
app.middleware("http")(security_middleware)

from app.routers.operations import router as ops_router, public as config_router
app.include_router(ops_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")

from app.routers.advisories import router as advisories_router
app.include_router(advisories_router, prefix="/api/v1")
