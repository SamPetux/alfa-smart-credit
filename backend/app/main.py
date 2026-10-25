"""FastAPI entrypoint: health + auth/demo + applications (B03–B04)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.api.v1.router import api_router
from backend.app.applications.errors import ApiError
from backend.app.core.config import get_settings
from backend.app.db.session import get_engine

app = FastAPI(
    title="Alfa Smart Credit API",
    version="api-v1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(api_router)


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.envelope.model_dump(mode="json"),
    )


@app.get("/api/v1/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def health_ready() -> dict[str, str]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception as exc:  # noqa: BLE001 — readiness envelope
        return {"status": "not_ready", "detail": type(exc).__name__}
    return {"status": "ok", "migration": str(version or "unknown")}


@app.get("/api/v1/meta")
def meta() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "api_version": "api-v1",
    }
