"""Общие DTO и envelope ошибок API v1."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


MoneyStr = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{v:.2f}", return_type=str, when_used="json"),
]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


class FieldError(ApiModel):
    field: str
    message: str


class ErrorBody(ApiModel):
    code: str
    message: str
    field_errors: list[FieldError] = Field(default_factory=list)
    request_id: str


class ErrorEnvelope(ApiModel):
    error: ErrorBody


class VersionedCommand(ApiModel):
    expected_version: int = Field(ge=1)


class CompanyBrief(ApiModel):
    id: UUID
    display_name: str
    demo_registration_id: str


class UserBrief(ApiModel):
    id: UUID
    username: str
    role: str
    display_name: str
    company: CompanyBrief | None = None


class SessionInfo(ApiModel):
    user: UserBrief
    csrf_token: str
    demo_mode: bool = False


class Timestamped(ApiModel):
    updated_at: datetime
