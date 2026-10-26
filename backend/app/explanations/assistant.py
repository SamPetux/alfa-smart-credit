"""Шаблонный помощник объяснений (P1-lite). Без LLM и сети.

Собирает понятный ответ из reason_codes и статуса заявки.
Не принимает кредитных решений и не подменяет OFFICER/CLIENT команды.
"""

from __future__ import annotations

from typing import Any

from backend.app.risk import explanations as risk_expl

NEXT_STEP: dict[str, str] = {
    "DRAFT": "Заполните обязательные поля и отправьте заявку.",
    "SUBMITTED": "Дождитесь автоматической проверки. Можно закрыть страницу и вернуться позже.",
    "CHECKING": "Идёт проверка сведений. Это займёт немного времени.",
    "NEEDS_INFO": "Откройте список уточнений, дополните данные и отправьте снова.",
    "PROCESSING_ERROR": "Проверка временно недоступна. Сотрудник может повторить обработку.",
    "MANUAL_REVIEW": "Заявка у специалиста. Дождитесь решения банка.",
    "OFFERED": "Ознакомьтесь с условиями и примите или отклоните предложение.",
    "ACCEPTED": "Откройте документ соглашения и подтвердите имитацию подписи.",
    "SIGNED": "Ожидайте имитацию выдачи. Повтор подписи не требуется.",
    "COMPLETED": "Имитация выдачи завершена. Можно посмотреть итог в истории.",
    "REJECTED": "Решение отрицательное. Причины — в объяснениях ниже.",
    "DECLINED_BY_CLIENT": "Вы отклонили предложение. При необходимости создайте новую заявку.",
}

TOPIC_HINTS: dict[str, str] = {
    "why": "Ниже — причины по кодам демонстрационной политики, не вероятность одобрения.",
    "next": "Следующий шаг зависит только от статуса заявки на сервере.",
    "amount": "Если предложена меньшая сумма — это следствие правил доступности (DSCR), не «скидка».",
    "general": "Это учебный прототип на синтетических данных; решение сотрудника обязательно.",
}


def explain_application(
    *,
    status: str,
    reason_codes: list[str] | None = None,
    client_explanations: list[str] | None = None,
    recommendation: str | None = None,
    topic: str = "general",
) -> dict[str, Any]:
    codes = list(reason_codes or [])
    ready_texts = list(client_explanations or [])
    if not ready_texts and codes:
        ready_texts = [risk_expl.client_text(c) for c in codes]

    topic_key = topic if topic in TOPIC_HINTS else "general"
    bullets = ready_texts[:]
    if recommendation:
        bullets.insert(
            0,
            f"Рекомендация risk-модуля: {recommendation} "
            "(не финальное решение банка).",
        )

    return {
        "engine": "template-v1",
        "is_simulation": True,
        "uses_llm": False,
        "topic": topic_key,
        "headline": TOPIC_HINTS[topic_key],
        "next_step": NEXT_STEP.get(status, "Обновите карточку заявки."),
        "reason_codes": codes,
        "bullets": bullets,
        "disclaimer": (
            "Помощник не принимает решение и не обращается к внешним моделям. "
            "Тексты шаблонные по reason_codes."
        ),
    }
