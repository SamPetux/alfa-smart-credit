"""Клиентские и банковские схемы заявок (раздельные проекции)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from backend.app.schemas.common import ApiModel, MoneyStr, VersionedCommand
from backend.app.schemas.enums import AllowedAction, ApplicationStatus, ProductCode


class DraftFields(ApiModel):
    purpose: Literal["working_capital", "equipment"] | None = None
    requested_amount: MoneyStr | None = None
    term_months: int | None = Field(default=None, ge=1)
    company_form: str | None = None
    monthly_revenue: MoneyStr | None = None
    monthly_operating_costs: MoneyStr | None = None
    declared_monthly_debt_payments: MoneyStr | None = None
    # Только для локальных симуляторов (B05); не кредитный признак
    demo_scenario: str | None = None


class DraftPatch(ApiModel):
    expected_version: int = Field(ge=1)
    draft_fields: DraftFields


class CreateApplicationRequest(ApiModel):
    product_code: ProductCode


class ClientApplication(ApiModel):
    """Безопасная клиентская проекция. Без raw БКИ и полной risk assessment."""

    id: UUID
    status: ApplicationStatus
    version: int = Field(ge=1)
    current_revision: int = Field(ge=0)
    next_action: str
    allowed_actions: list[AllowedAction]
    is_simulation: bool = True
    updated_at: datetime
    product_code: ProductCode | None = None
    draft_fields: DraftFields | None = None


class ApplicationList(ApiModel):
    items: list[ClientApplication]
    next_cursor: str | None = None


class ResubmitRequest(VersionedCommand):
    info_request_id: UUID


class OfferCommand(VersionedCommand):
    offer_id: UUID


class SimulateSignRequest(VersionedCommand):
    agreement_id: UUID
    content_hash: str
    consent: Literal[True]


class OfficerDecisionRequest(VersionedCommand):
    run_id: UUID
    type: Literal["APPROVE_OFFER", "REJECT"]
    candidate_hash: str | None = None
    reason_code: str | None = None
    comment: str | None = None


class RequestInfoBody(VersionedCommand):
    fields: list[str] = Field(min_length=1)
    document_kinds: list[str] = Field(default_factory=list)
    message: str = Field(min_length=1)


class BankApplication(ApiModel):
    """Банковская проекция: досье, checks, risk, revisions, audit."""

    id: UUID
    status: ApplicationStatus
    version: int
    allowed_actions: list[AllowedAction]
    is_simulation: bool = True
    active_run_id: UUID | None = None
    risk_summary: dict | None = None
    checks: list[dict] = Field(default_factory=list)
    revisions: list[dict] = Field(default_factory=list)
    audit: list[dict] = Field(default_factory=list)
