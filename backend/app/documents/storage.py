"""Локальное хранилище документов (volume). Не публичный static."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from backend.app.applications.errors import ApiError
from backend.app.core.config import get_settings

ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}
MAX_BYTES = 10 * 1024 * 1024


def store_upload(*, data: bytes, mime: str, application_id: str) -> tuple[str, str, int]:
    if mime not in ALLOWED_MIME:
        raise ApiError(422, "VALIDATION_ERROR", f"Недопустимый MIME: {mime}")
    if len(data) == 0:
        raise ApiError(422, "VALIDATION_ERROR", "Пустой файл")
    if len(data) > MAX_BYTES:
        raise ApiError(422, "VALIDATION_ERROR", "Файл больше 10 MiB")

    # Простая проверка сигнатур
    if mime == "application/pdf" and not data.startswith(b"%PDF"):
        raise ApiError(422, "VALIDATION_ERROR", "Файл не похож на PDF")
    if mime == "image/png" and not data.startswith(b"\x89PNG"):
        raise ApiError(422, "VALIDATION_ERROR", "Файл не похож на PNG")
    if mime == "image/jpeg" and data[:2] != b"\xff\xd8":
        raise ApiError(422, "VALIDATION_ERROR", "Файл не похож на JPEG")

    ext = ALLOWED_MIME[mime]
    content_hash = hashlib.sha256(data).hexdigest()
    key = f"{application_id}/{uuid4().hex}{ext}"
    root = Path(get_settings().documents_dir)
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key, content_hash, len(data)
