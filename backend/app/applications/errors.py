"""Ошибки API с envelope contracts/openapi.yaml."""

from __future__ import annotations

from uuid import uuid4

from backend.app.core.request_context import get_request_id
from backend.app.schemas.common import ErrorBody, ErrorEnvelope, FieldError


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        field_errors: list[FieldError] | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        rid = request_id or get_request_id() or f"req-{uuid4().hex[:12]}"
        self.envelope = ErrorEnvelope(
            error=ErrorBody(
                code=code,
                message=message,
                field_errors=field_errors or [],
                request_id=rid,
            )
        )
        super().__init__(message)
