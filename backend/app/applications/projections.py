"""Клиентская и банковская проекции заявки."""

from __future__ import annotations

from typing import Any

from backend.app.db.models import Application, Company, Product
from backend.app.schemas.applications import BankApplication, ClientApplication, DraftFields
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


def allowed_actions_for_officer(
    status: ApplicationStatus,
    risk_summary: dict[str, Any] | None,
    *,
    disbursement_retry_available: bool = False,
) -> list[AllowedAction]:
    actions: list[AllowedAction] = []
    if status == ApplicationStatus.MANUAL_REVIEW:
        actions.append(AllowedAction.REQUEST_INFO)
        actions.append(AllowedAction.REJECT)
        if risk_summary and risk_summary.get("recommendation") == "OFFER":
            actions.append(AllowedAction.APPROVE_OFFER)
    if status == ApplicationStatus.PROCESSING_ERROR:
        actions.append(AllowedAction.RETRY_CHECKS)
    if status == ApplicationStatus.SIGNED and disbursement_retry_available:
        actions.append(AllowedAction.RETRY_DISBURSEMENT)
    return actions


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


def to_bank_application(
    app: Application,
    *,
    product: Product | None,
    company: Company | None,
    risk_summary: dict[str, Any] | None,
    checks: list[dict[str, Any]],
    revisions: list[dict[str, Any]],
    audit: list[dict[str, Any]],
    allowed: list[AllowedAction],
    next_action: str,
) -> BankApplication:
    status = ApplicationStatus(app.status)
    return BankApplication(
        id=app.id,
        status=status,
        version=app.version,
        current_revision=app.current_revision,
        allowed_actions=allowed,
        is_simulation=True,
        active_run_id=app.active_run_id,
        next_action=next_action,
        product_code=ProductCode(product.code) if product else None,
        company_id=company.id if company else None,
        company_name=company.display_name if company else None,
        demo_registration_id=company.demo_registration_id if company else None,
        draft_fields=DraftFields.model_validate(app.draft_json or {}) if app.draft_json else None,
        risk_summary=risk_summary,
        checks=checks,
        revisions=revisions,
        audit=audit,
        updated_at=app.updated_at,
    )
