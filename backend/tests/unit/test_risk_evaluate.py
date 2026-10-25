"""Golden cases и свойства risk-модуля (S04–S09)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest

from backend.app.risk.evaluate import RiskContractError, evaluate
from backend.app.risk.money import monthly_payment
from backend.app.risk.policy import load_policy
from backend.app.schemas.enums import ProductCode, RiskRecommendation
from backend.app.schemas.risk import RiskInput

APP = UUID("00000000-0000-4000-8000-000000000101")


def _input(**overrides) -> RiskInput:
    base = dict(
        application_id=APP,
        revision=1,
        product_code=ProductCode.WORKING_CAPITAL,
        requested_amount=Decimal("1000000.00"),
        term_months=12,
        monthly_revenue=Decimal("1500000.00"),
        monthly_operating_costs=Decimal("1000000.00"),
        declared_monthly_debt_payments=Decimal("100000.00"),
        verified_monthly_debt_payments=Decimal("100000.00"),
        company_age_months=30,
        registry_status="ACTIVE",
        max_overdue_days_12m=0,
        required_documents_present=True,
        sources_complete=True,
        data_conflicts=[],
        is_synthetic=True,
    )
    base.update(overrides)
    return RiskInput(**base)


def test_g01_full_offer() -> None:
    result = evaluate(_input())
    assert result.recommendation == RiskRecommendation.OFFER
    assert result.risk_score == 100
    assert result.risk_band == "A"
    assert result.candidate is not None
    assert result.candidate.amount == Decimal("1000000.00")
    assert result.candidate.is_alternative is False
    assert result.requires_officer is True


def test_g02_alternative_amount() -> None:
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
        )
    )
    assert result.recommendation == RiskRecommendation.OFFER
    assert result.risk_score == 100
    assert result.risk_band == "A"
    assert result.candidate is not None
    assert result.candidate.amount == Decimal("641000.00")
    assert result.candidate.is_alternative is True
    assert result.candidate.annual_rate == Decimal("0.22")
    assert "LOWER_AMOUNT_REQUIRED" in result.reason_codes
    assert result.affordability is not None
    assert result.affordability.offered_payment == Decimal("59994.00")
    assert result.affordability.offered_dscr is not None
    assert Decimal(result.affordability.offered_dscr) >= Decimal("1.25")


def test_g03_debt_mismatch_needs_info() -> None:
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
            declared_monthly_debt_payments=Decimal("0.00"),
            verified_monthly_debt_payments=Decimal("100000.00"),
        )
    )
    assert result.recommendation == RiskRecommendation.NEEDS_INFO
    assert result.reason_codes == ["DEBT_DATA_MISMATCH"]
    assert result.requested_fields == ["declared_monthly_debt_payments"]
    assert result.risk_score is None
    assert result.candidate is None


def test_g04_overdue_reject_without_fake_score() -> None:
    result = evaluate(_input(max_overdue_days_12m=35))
    assert result.recommendation == RiskRecommendation.REJECT
    assert result.reason_codes == ["OVERDUE_LIMIT"]
    assert result.risk_score is None
    assert result.requires_officer is True


def test_g05_affordability_below_minimum() -> None:
    result = evaluate(
        _input(
            requested_amount=Decimal("100000.00"),
            monthly_revenue=Decimal("300000.00"),
            monthly_operating_costs=Decimal("260000.00"),
            declared_monthly_debt_payments=Decimal("30000.00"),
            verified_monthly_debt_payments=Decimal("30000.00"),
        )
    )
    assert result.recommendation == RiskRecommendation.REJECT
    assert result.risk_score == 90
    assert result.risk_band == "A"
    assert result.reason_codes == ["AFFORDABILITY_BELOW_MINIMUM"]
    assert result.candidate is None


def test_g06_sources_incomplete_is_contract_error() -> None:
    with pytest.raises(RiskContractError):
        evaluate(_input(sources_complete=False))


def test_g07_band_b_rate() -> None:
    result = evaluate(
        _input(
            requested_amount=Decimal("100000.00"),
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("500000.00"),
            company_age_months=18,
            max_overdue_days_12m=5,
        )
    )
    assert result.risk_score == 70
    assert result.risk_band == "B"
    if result.recommendation == RiskRecommendation.OFFER:
        assert result.candidate is not None
        assert result.candidate.annual_rate == Decimal("0.26")


def test_g08_missing_overdue_needs_info_not_zero() -> None:
    """Если overdue дошёл до evaluate как null — NEEDS_INFO, не «0 дней»."""
    result = evaluate(_input(max_overdue_days_12m=None))
    assert result.recommendation == RiskRecommendation.NEEDS_INFO
    assert "max_overdue_days_12m" in result.requested_fields
    assert result.risk_score is None


def test_missing_not_replaced_by_zero_in_score() -> None:
    result = evaluate(_input(monthly_revenue=None))
    assert result.recommendation == RiskRecommendation.NEEDS_INFO
    assert result.risk_score is None
    assert "monthly_revenue" in result.requested_fields


def test_higher_requested_amount_does_not_lower_payment() -> None:
    low = evaluate(_input(requested_amount=Decimal("500000.00")))
    high = evaluate(_input(requested_amount=Decimal("1000000.00")))
    assert low.candidate is not None and high.candidate is not None
    assert high.affordability is not None and low.affordability is not None
    assert high.affordability.offered_payment >= low.affordability.offered_payment


def test_higher_existing_debt_does_not_improve_affordability() -> None:
    better = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
            verified_monthly_debt_payments=Decimal("50000.00"),
            declared_monthly_debt_payments=Decimal("50000.00"),
        )
    )
    worse = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
            verified_monthly_debt_payments=Decimal("100000.00"),
            declared_monthly_debt_payments=Decimal("100000.00"),
        )
    )
    assert better.candidate is not None and worse.candidate is not None
    assert better.candidate.amount >= worse.candidate.amount


def test_offer_within_product_limits() -> None:
    policy = load_policy()
    product = policy["products"]["WORKING_CAPITAL"]
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
        )
    )
    assert result.candidate is not None
    assert Decimal(product["amount_min"]) <= result.candidate.amount
    assert result.candidate.amount <= Decimal(product["amount_max"])


def test_alternative_rechecked_against_dscr() -> None:
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
        )
    )
    assert result.candidate is not None
    payment = monthly_payment(
        result.candidate.amount,
        result.candidate.annual_rate,
        result.candidate.term_months,
    )
    assert payment == result.affordability.offered_payment
    assert Decimal(result.affordability.offered_dscr) >= Decimal("1.25")


def test_cashflow_non_positive() -> None:
    result = evaluate(
        _input(
            monthly_revenue=Decimal("100000.00"),
            monthly_operating_costs=Decimal("100000.00"),
        )
    )
    assert result.recommendation == RiskRecommendation.REJECT
    assert result.reason_codes == ["CASHFLOW_NON_POSITIVE"]


def test_registry_inactive() -> None:
    result = evaluate(_input(registry_status="INACTIVE"))
    assert result.recommendation == RiskRecommendation.REJECT
    assert result.reason_codes == ["REGISTRY_INACTIVE"]


def test_deterministic() -> None:
    a = evaluate(_input())
    b = evaluate(_input())
    assert a.model_dump() == b.model_dump()
