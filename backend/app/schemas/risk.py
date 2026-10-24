"""Контракт risk-v1: вход/выход чистой функции evaluate.

Модуль risk не импортирует ORM/FastAPI. Эти схемы — граница для worker и Ильи.
"""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field

from backend.app.schemas.common import ApiModel, MoneyStr
from backend.app.schemas.enums import ProductCode, RiskRecommendation


class RiskFactor(ApiModel):
    code: Literal["AGE", "MARGIN", "PAYMENT_HISTORY", "EXISTING_DEBT"]
    points: int


class OfferCandidate(ApiModel):
    product_code: ProductCode
    amount: MoneyStr
    term_months: int = Field(ge=1)
    annual_rate: Decimal
    currency: Literal["RUB"] = "RUB"
    fees: MoneyStr
    is_alternative: bool


class Affordability(ApiModel):
    free_cashflow: MoneyStr | None = None
    existing_payment: MoneyStr | None = None
    requested_payment: MoneyStr | None = None
    requested_dscr: str | None = None
    offered_payment: MoneyStr | None = None
    offered_dscr: str | None = None
    total_payment: MoneyStr | None = None


class RiskInput(ApiModel):
    schema_version: Literal["risk-v1"] = "risk-v1"
    application_id: UUID
    revision: int = Field(ge=1)
    product_code: ProductCode
    requested_amount: MoneyStr
    term_months: int = Field(ge=1)
    monthly_revenue: MoneyStr | None = None
    monthly_operating_costs: MoneyStr | None = None
    declared_monthly_debt_payments: MoneyStr | None = None
    verified_monthly_debt_payments: MoneyStr | None = None
    company_age_months: int | None = Field(default=None, ge=0)
    registry_status: Literal["ACTIVE", "INACTIVE"] | None = None
    max_overdue_days_12m: int | None = Field(default=None, ge=0)
    required_documents_present: bool
    sources_complete: bool
    data_conflicts: list[str] = Field(default_factory=list)
    is_synthetic: bool = True


class RiskResult(ApiModel):
    schema_version: Literal["risk-v1"] = "risk-v1"
    model_version: Literal["score-v1"] = "score-v1"
    policy_version: Literal["policy-v1"] = "policy-v1"
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_band: Literal["A", "B", "C"] | None = None
    recommendation: RiskRecommendation
    requires_officer: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    requested_fields: list[str] = Field(default_factory=list)
    factors: list[RiskFactor] | None = None
    candidate: OfferCandidate | None = None
    affordability: Affordability | None = None
    client_explanations: list[str] = Field(default_factory=list)
    officer_explanations: list[str] = Field(default_factory=list)
