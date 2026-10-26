"""FastAPI entrypoint: health, meta, API; request_id middleware (B09)."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.api.v1.router import api_router
from backend.app.applications.errors import ApiError
from backend.app.core.config import DEMO_PRIVACY_NOTICE, get_settings
from backend.app.core.logging_utils import log_event
from backend.app.core.request_context import clear_request_context, set_request_id
from backend.app.db.session import get_engine

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

app = FastAPI(
    title="Alfa Smart Credit API",
    version="api-v1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(api_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    incoming = request.headers.get("X-Request-Id", "").strip()
    request_id = incoming if incoming and len(incoming) <= 64 else f"req-{uuid4().hex[:12]}"
    set_request_id(request_id)
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-Id"] = request_id
        return response
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        # Не логируем query/body/cookies — только путь и коды
        path = request.url.path
        if not path.startswith("/api/v1/health/"):
            log_event(
                "HTTP_REQUEST",
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
        clear_request_context()


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    log_event(
        "API_ERROR",
        level=logging.WARNING,
        error_code=exc.envelope.error.code,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.envelope.model_dump(mode="json"),
        headers={"X-Request-Id": exc.envelope.error.request_id},
    )


@app.get("/api/v1/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def health_ready() -> JSONResponse:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception as exc:  # noqa: BLE001 — readiness envelope
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": type(exc).__name__},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "migration": str(version or "unknown")},
    )


@app.get("/api/v1/meta")
def meta() -> dict[str, object]:
    cfg = get_settings()
    payload: dict[str, object] = {
        "app_env": cfg.app_env,
        "demo_mode": cfg.demo_mode,
        "api_version": "api-v1",
        "is_simulation": True,
    }
    if cfg.demo_mode:
        payload["privacy_notice"] = DEMO_PRIVACY_NOTICE
    return payload
