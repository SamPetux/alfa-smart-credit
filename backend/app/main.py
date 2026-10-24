"""FastAPI entrypoint. Каркас: health + заглушки роутов появятся в B04+."""

from fastapi import FastAPI

app = FastAPI(
    title="Alfa Smart Credit API",
    version="api-v1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/v1/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def health_ready() -> dict[str, str]:
    # TODO(B09): проверка БД и миграций
    return {"status": "not_wired", "detail": "DB readiness not implemented yet"}
