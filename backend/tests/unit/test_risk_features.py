from uuid import UUID

from backend.app.risk.features import build_risk_input


def test_build_does_not_zero_missing_bureau_overdue() -> None:
    inp = build_risk_input(
        application_id=UUID("00000000-0000-4000-8000-000000000101"),
        revision=1,
        product_code="WORKING_CAPITAL",
        draft={
            "requested_amount": "1000000.00",
            "term_months": 12,
            "monthly_revenue": "600000.00",
            "monthly_operating_costs": "400000.00",
            "declared_monthly_debt_payments": "100000.00",
        },
        registry={"status": "ACTIVE", "company_age_months": 30},
        bureau={
            "monthly_debt_payments": "100000.00",
            "max_overdue_days_12m": None,
        },
        required_documents_present=True,
        sources_complete=False,
    )
    assert inp.max_overdue_days_12m is None
    assert inp.sources_complete is False
