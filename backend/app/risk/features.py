"""S03 Feature builder: заявка + ответы симуляторов → RiskInput.

Чистая функция. Missing не заполняется нулём. Не использует email/имя/scenario_id
как кредитный признак.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.app.schemas.enums import ProductCode
from backend.app.schemas.risk import RiskInput
from backend.app.risk.money import money


class FeatureBuildError(ValueError):
    """Недостаточно структуры для сборки входа — техническая ошибка контракта."""


def _money_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return money(value)


def build_risk_input(
    *,
    application_id: UUID,
    revision: int,
    product_code: str,
    draft: dict[str, Any],
    registry: dict[str, Any] | None,
    bureau: dict[str, Any] | None,
    required_documents_present: bool,
    sources_complete: bool,
    data_conflicts: list[str] | None = None,
) -> RiskInput:
    """Собрать RiskInput из черновика и локальных симуляторов.

    registry/bureau — payload успешного ответа. При timeout/unavailable worker
    не вызывает evaluate и не должен подставлять нули.
    """
    try:
        code = ProductCode(product_code)
    except ValueError as exc:
        raise FeatureBuildError(f"Invalid product_code: {product_code}") from exc

    company_age = None
    registry_status = None
    if registry is not None:
        company_age = registry.get("company_age_months")
        registry_status = registry.get("status")

    verified_debt = None
    max_overdue = None
    if bureau is not None:
        verified_debt = _money_or_none(bureau.get("monthly_debt_payments"))
        # Явный null в успешном ответе = missing → sources_complete должен быть false у worker
        if "max_overdue_days_12m" in bureau:
            raw = bureau.get("max_overdue_days_12m")
            max_overdue = None if raw is None else int(raw)

    return RiskInput(
        application_id=application_id,
        revision=revision,
        product_code=code,
        requested_amount=money(draft["requested_amount"]),
        term_months=int(draft["term_months"]),
        monthly_revenue=_money_or_none(draft.get("monthly_revenue")),
        monthly_operating_costs=_money_or_none(draft.get("monthly_operating_costs")),
        declared_monthly_debt_payments=_money_or_none(
            draft.get("declared_monthly_debt_payments")
        ),
        verified_monthly_debt_payments=verified_debt,
        company_age_months=None if company_age is None else int(company_age),
        registry_status=registry_status,
        max_overdue_days_12m=max_overdue,
        required_documents_present=required_documents_present,
        sources_complete=sources_complete,
        data_conflicts=list(data_conflicts or []),
        is_synthetic=True,
    )
