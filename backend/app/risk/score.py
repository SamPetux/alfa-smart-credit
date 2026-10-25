"""Эвристический score-v1. Не вероятность одобрения/дефолта."""

from __future__ import annotations

from decimal import Decimal

from backend.app.schemas.risk import RiskFactor, RiskInput
from backend.app.risk.policy import band_for_score


def _age_points(age_months: int) -> int:
    if age_months >= 24:
        return 25
    if age_months >= 12:
        return 15
    if age_months >= 6:
        return 5
    return 0


def _margin_points(revenue: Decimal, costs: Decimal) -> int:
    if revenue <= 0:
        return 0
    margin = (revenue - costs) / revenue
    if margin >= Decimal("0.25"):
        return 25
    if margin >= Decimal("0.10"):
        return 15
    if margin > 0:
        return 5
    return 0


def _payment_history_points(max_overdue_days: int) -> int:
    if max_overdue_days == 0:
        return 30
    if max_overdue_days <= 7:
        return 20
    if max_overdue_days <= 30:
        return 5
    return 0


def _existing_debt_points(revenue: Decimal, debt: Decimal) -> int:
    if revenue <= 0:
        return 0
    ratio = debt / revenue
    if ratio <= Decimal("0.20"):
        return 20
    if ratio <= Decimal("0.40"):
        return 10
    return 0


def compute_score(
    inp: RiskInput,
    *,
    policy: dict,
) -> tuple[int, str, list[RiskFactor]]:
    """Требует заполненных полей для score; иначе вызывающий код не должен сюда заходить."""
    assert inp.company_age_months is not None
    assert inp.monthly_revenue is not None
    assert inp.monthly_operating_costs is not None
    assert inp.verified_monthly_debt_payments is not None
    assert inp.max_overdue_days_12m is not None

    factors = [
        RiskFactor(code="AGE", points=_age_points(inp.company_age_months)),
        RiskFactor(
            code="MARGIN",
            points=_margin_points(inp.monthly_revenue, inp.monthly_operating_costs),
        ),
        RiskFactor(
            code="PAYMENT_HISTORY",
            points=_payment_history_points(inp.max_overdue_days_12m),
        ),
        RiskFactor(
            code="EXISTING_DEBT",
            points=_existing_debt_points(
                inp.monthly_revenue, inp.verified_monthly_debt_payments
            ),
        ),
    ]
    total = sum(f.points for f in factors)
    band = band_for_score(policy, total)
    return total, band, factors
