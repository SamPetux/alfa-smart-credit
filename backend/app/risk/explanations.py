"""Стабильные reason_codes и тексты для клиента / сотрудника."""

from __future__ import annotations

CLIENT: dict[str, str] = {
    "MISSING_DATA": "Укажите конкретное недостающее сведение",
    "DEBT_DATA_MISMATCH": "Уточните платежи по действующим кредитам",
    "REGISTRY_INACTIVE": (
        "По данным демонстрационного источника статус компании "
        "требует отрицательного решения"
    ),
    "BUSINESS_TOO_YOUNG": (
        "В демонстрационной политике этот продукт доступен бизнесу от {min_age} месяцев"
    ),
    "OVERDUE_LIMIT": (
        "В демонстрационной проверке выявлена просрочка выше допустимого порога"
    ),
    "RISK_POLICY_LIMIT": (
        "Профиль не соответствует правилам этой демонстрационной политики"
    ),
    "LOWER_AMOUNT_REQUIRED": (
        "Предложена меньшая сумма с учётом текущих платежей и доходов"
    ),
    "AFFORDABILITY_BELOW_MINIMUM": (
        "В текущих параметрах расчёт не позволяет предложить минимальную сумму продукта"
    ),
    "CASHFLOW_NON_POSITIVE": (
        "Указанные расходы не оставляют положительного потока для расчёта"
    ),
}


def client_text(code: str, **params: object) -> str:
    template = CLIENT.get(code, code)
    try:
        return template.format(**params)
    except (KeyError, ValueError):
        return template


def officer_text(code: str, detail: str) -> str:
    return f"{code}: {detail}"
