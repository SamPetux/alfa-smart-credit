from backend.app.applications.validation import validate_draft_for_submit
from backend.app.schemas.enums import ProductCode


def test_submit_validation_missing_fields() -> None:
    errors = validate_draft_for_submit({}, ProductCode.WORKING_CAPITAL, set())
    fields = {e.field for e in errors}
    assert "requested_amount" in fields
    assert "documents" in fields


def test_submit_validation_ok() -> None:
    draft = {
        "purpose": "working_capital",
        "requested_amount": "1000000.00",
        "term_months": 12,
        "company_form": "LLC",
        "monthly_revenue": "600000.00",
        "monthly_operating_costs": "400000.00",
        "declared_monthly_debt_payments": "100000.00",
    }
    errors = validate_draft_for_submit(
        draft, ProductCode.WORKING_CAPITAL, {"FINANCIAL_SUMMARY"}
    )
    assert errors == []
