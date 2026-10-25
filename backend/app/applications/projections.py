"""Клиентская проекция заявки и allowed_actions."""

from __future__ import annotations

from backend.app.db.models import Application, Product
from backend.app.schemas.applications import ClientApplication, DraftFields
from backend.app.schemas.enums import AllowedAction, ApplicationStatus, ProductCode

NEXT_ACTION: dict[ApplicationStatus, str] = {
    ApplicationStatus.DRAFT: "Заполнить и отправить",
    ApplicationStatus.SUBMITTED: "Дождаться результата, можно вернуться позже",
    ApplicationStatus.CHECKING: "Дождаться результата, можно вернуться позже",
    ApplicationStatus.NEEDS_INFO: "Открыть список уточнений",
    ApplicationStatus.MANUAL_REVIEW: "Дождаться решения",
    ApplicationStatus.OFFERED: "Принять или отклонить",
    ApplicationStatus.ACCEPTED: "Ознакомиться с документом",
    ApplicationStatus.SIGNED: "Дождаться имитации выдачи",
    ApplicationStatus.COMPLETED: "Посмотреть результат",
    ApplicationStatus.REJECTED: "Прочитать объяснение",
    ApplicationStatus.DECLINED_BY_CLIENT: "При необходимости создать новую заявку",
    ApplicationStatus.PROCESSING_ERROR: "Заявка сохранена, требуется повтор обработки",
}


def allowed_actions_for(status: ApplicationStatus) -> list[AllowedAction]:
    if status == ApplicationStatus.DRAFT:
        return [AllowedAction.SAVE, AllowedAction.SUBMIT]
    if status == ApplicationStatus.NEEDS_INFO:
        return [AllowedAction.SAVE_SUPPLEMENT, AllowedAction.RESUBMIT]
    if status == ApplicationStatus.OFFERED:
        return [AllowedAction.ACCEPT_OFFER, AllowedAction.DECLINE_OFFER]
    if status == ApplicationStatus.ACCEPTED:
        return [AllowedAction.SIMULATE_SIGN]
    return []


def to_client_application(app: Application, product: Product | None) -> ClientApplication:
    status = ApplicationStatus(app.status)
    draft = DraftFields.model_validate(app.draft_json or {}) if app.draft_json else DraftFields()
    product_code = ProductCode(product.code) if product else None
    return ClientApplication(
        id=app.id,
        status=status,
        version=app.version,
        current_revision=app.current_revision,
        next_action=NEXT_ACTION[status],
        allowed_actions=allowed_actions_for(status),
        is_simulation=True,
        updated_at=app.updated_at,
        product_code=product_code,
        draft_fields=draft,
    )
