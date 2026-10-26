"""Контекст запроса: request_id без передачи через все слои явно."""

from __future__ import annotations

from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_application_id: ContextVar[str | None] = ContextVar("application_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


def get_application_id() -> str | None:
    return _application_id.get()


def set_application_id(value: str | None) -> None:
    _application_id.set(value)


def clear_request_context() -> None:
    _request_id.set(None)
    _application_id.set(None)
