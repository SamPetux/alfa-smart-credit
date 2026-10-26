"""Q02: сверка evaluate с независимыми expected из fixtures/golden/cases.json.

Expected не вычисляются вызовом evaluate «для эталона» — берутся из golden JSON
(согласовано с владельцем risk). evaluate вызывается только как тестируемая реализация.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from backend.app.risk.evaluate import evaluate
from backend.app.schemas.enums import ProductCode, RiskRecommendation
from backend.app.schemas.risk import RiskInput

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = json.loads((ROOT / "fixtures" / "golden" / "cases.json").read_text(encoding="utf-8"))
APP = UUID("00000000-0000-4000-8000-000000000201")


def _case(case_id: str) -> dict:
    for row in GOLDEN["cases"]:
        if row["id"] == case_id:
            return row["expect"]
    raise KeyError(case_id)


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


def test_golden_g01_matches_independent_expect() -> None:
    expect = _case("G01")
    result = evaluate(_input())
    assert result.recommendation.value == expect["recommendation"]
    assert result.risk_score == expect["risk_score"]
    assert result.risk_band == expect["risk_band"]
    assert result.candidate is not None
    assert f"{result.candidate.amount:.2f}" == expect["candidate_amount"]
    assert result.candidate.is_alternative is expect["is_alternative"]


def test_golden_g02_matches_independent_expect() -> None:
    expect = _case("G02")
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
        )
    )
    assert result.recommendation.value == expect["recommendation"]
    assert result.candidate is not None
    assert f"{result.candidate.amount:.2f}" == expect["candidate_amount"]
    assert result.candidate.is_alternative is expect["is_alternative"]
    assert result.affordability is not None
    assert f"{result.affordability.offered_payment:.2f}" == expect["offered_payment"]
    for code in expect["reason_codes"]:
        assert code in result.reason_codes


def test_golden_g03_matches_independent_expect() -> None:
    expect = _case("G03")
    result = evaluate(
        _input(
            monthly_revenue=Decimal("600000.00"),
            monthly_operating_costs=Decimal("400000.00"),
            declared_monthly_debt_payments=Decimal("0.00"),
            verified_monthly_debt_payments=Decimal("100000.00"),
        )
    )
    assert result.recommendation.value == expect["recommendation"]
    assert result.reason_codes == expect["reason_codes"]
    assert result.requested_fields == expect["requested_fields"]


def test_golden_g04_matches_independent_expect() -> None:
    expect = _case("G04")
    result = evaluate(_input(max_overdue_days_12m=35))
    assert result.recommendation.value == expect["recommendation"]
    assert result.reason_codes == expect["reason_codes"]
    assert result.risk_score is expect["risk_score"]


def test_golden_g05_matches_independent_expect() -> None:
    expect = _case("G05")
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
    assert result.recommendation.value == expect["recommendation"]
    assert result.risk_score == expect["risk_score"]
    assert result.risk_band == expect["risk_band"]
    assert result.reason_codes == expect["reason_codes"]
