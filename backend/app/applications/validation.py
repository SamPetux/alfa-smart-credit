"""Проверка обязательных полей черновика и документов перед submit."""

from __future__ import annotations

from typing import Any

from backend.app.schemas.common import FieldError
from backend.app.schemas.enums import ProductCode

REQUIRED_DRAFT_FIELDS = (
    "purpose",
    "requested_amount",
    "term_months",
    "company_form",
    "monthly_revenue",
    "monthly_operating_costs",
    "declared_monthly_debt_payments",
)

PURPOSE_BY_PRODUCT = {
    ProductCode.WORKING_CAPITAL: "working_capital",
    ProductCode.EQUIPMENT: "equipment",
}

REQUIRED_DOCS: dict[ProductCode, frozenset[str]] = {
    ProductCode.WORKING_CAPITAL: frozenset({"FINANCIAL_SUMMARY"}),
    ProductCode.EQUIPMENT: frozenset({"FINANCIAL_SUMMARY", "EQUIPMENT_QUOTE"}),
}


def validate_draft_for_submit(
    draft: dict[str, Any],
    product_code: ProductCode,
    document_kinds: set[str],
) -> list[FieldError]:
    errors: list[FieldError] = []
    for field in REQUIRED_DRAFT_FIELDS:
        value = draft.get(field)
        if value is None or value == "":
            errors.append(FieldError(field=field, message="Обязательное поле"))

    expected_purpose = PURPOSE_BY_PRODUCT[product_code]
    if draft.get("purpose") and draft.get("purpose") != expected_purpose:
        errors.append(
            FieldError(
                field="purpose",
                message=f"Для продукта {product_code.value} ожидается purpose={expected_purpose}",
            )
        )

    missing_docs = REQUIRED_DOCS[product_code] - document_kinds
    for kind in sorted(missing_docs):
        errors.append(FieldError(field="documents", message=f"Нужен документ {kind}"))

    return errors
