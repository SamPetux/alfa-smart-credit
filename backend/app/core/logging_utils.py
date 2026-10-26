"""Структурированные логи без токенов и содержимого документов."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.core.request_context import get_application_id, get_request_id

_log = logging.getLogger("asc")

# Поля, которые никогда не пишем в лог
_FORBIDDEN_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "session_token",
        "csrf",
        "csrf_token",
        "authorization",
        "cookie",
        "document_bytes",
        "file_bytes",
        "content",
        "body",
        "raw_body",
    }
)


def log_event(
    event_code: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    safe: dict[str, Any] = {
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": logging.getLevelName(level),
        "event_code": event_code,
    }
    rid = get_request_id()
    if rid:
        safe["request_id"] = rid
    app_id = get_application_id()
    if app_id:
        safe["application_id"] = app_id

    for key, value in fields.items():
        if key.lower() in _FORBIDDEN_KEYS or value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            safe[key] = value
        else:
            safe[key] = str(value)

    _log.log(level, json.dumps(safe, ensure_ascii=False, separators=(",", ":")))
