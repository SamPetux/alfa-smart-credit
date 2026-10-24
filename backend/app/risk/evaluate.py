"""Точка входа risk-модуля (заглушка для Ильи).

Правила реализуются только здесь. Нет ORM, FastAPI, сети и БД.
"""

from backend.app.schemas.risk import RiskInput, RiskResult


class RiskContractError(ValueError):
    """Невалидная структура входа — техническая ошибка, не кредитный отказ."""


def evaluate(input: RiskInput, policy: dict | None = None) -> RiskResult:
    """Чистая функция. Реализация score/policy — задача Sxx (Илья)."""
    if not input.sources_complete:
        raise RiskContractError(
            "sources_complete=false: worker must not call evaluate; "
            "route to SOURCE_INCOMPLETE"
        )
    raise NotImplementedError(
        "Risk rules not implemented yet — owner: Илья (backend/app/risk/)"
    )
