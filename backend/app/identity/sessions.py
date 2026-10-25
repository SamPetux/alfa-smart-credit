"""Серверные сессии: opaque HttpOnly cookie, CSRF double-submit, отзыв при смене профиля."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import Company, Membership, SessionRow, User
from backend.app.identity.tokens import hash_token, new_token
from backend.app.schemas.common import CompanyBrief, SessionInfo, UserBrief


@dataclass(frozen=True, slots=True)
class IssuedSession:
    raw_token: str
    csrf_token: str
    info: SessionInfo
    expires_at: datetime


def _company_for_user(session: Session, user_id: UUID) -> Company | None:
    membership = session.scalar(
        select(Membership)
        .where(Membership.user_id == user_id)
        .options(selectinload(Membership.company))
    )
    return membership.company if membership else None


def build_session_info(
    user: User,
    company: Company | None,
    csrf_token: str,
    demo_mode: bool,
) -> SessionInfo:
    company_brief = None
    if company is not None:
        company_brief = CompanyBrief(
            id=company.id,
            display_name=company.display_name,
            demo_registration_id=company.demo_registration_id,
        )
    return SessionInfo(
        user=UserBrief(
            id=user.id,
            username=user.username,
            role=user.role,
            display_name=user.display_name,
            company=company_brief,
        ),
        csrf_token=csrf_token,
        demo_mode=demo_mode,
    )


def revoke_user_sessions(session: Session, user_id: UUID) -> None:
    now = datetime.now(UTC)
    rows = session.scalars(
        select(SessionRow).where(
            SessionRow.user_id == user_id,
            SessionRow.revoked_at.is_(None),
        )
    ).all()
    for row in rows:
        row.revoked_at = now


def create_session(session: Session, user: User, *, settings: Settings | None = None) -> IssuedSession:
    settings = settings or get_settings()
    revoke_user_sessions(session, user.id)

    raw_token = new_token()
    csrf_token = new_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.session_ttl_seconds)
    session.add(
        SessionRow(
            token_hash=hash_token(raw_token),
            user_id=user.id,
            csrf_hash=hash_token(csrf_token),
            expires_at=expires_at,
        )
    )
    company = _company_for_user(session, user.id)
    info = build_session_info(user, company, csrf_token, settings.demo_mode)
    return IssuedSession(
        raw_token=raw_token,
        csrf_token=csrf_token,
        info=info,
        expires_at=expires_at,
    )


def find_active_session_row(session: Session, raw_token: str | None) -> SessionRow | None:
    if not raw_token:
        return None
    now = datetime.now(UTC)
    return session.scalar(
        select(SessionRow)
        .where(
            SessionRow.token_hash == hash_token(raw_token),
            SessionRow.revoked_at.is_(None),
            SessionRow.expires_at > now,
        )
        .options(selectinload(SessionRow.user))
    )


def session_info_for(
    session: Session,
    row: SessionRow,
    csrf_token: str,
    *,
    settings: Settings | None = None,
) -> SessionInfo:
    settings = settings or get_settings()
    company = _company_for_user(session, row.user_id)
    return build_session_info(row.user, company, csrf_token, settings.demo_mode)


def revoke_session_by_token(session: Session, raw_token: str | None) -> None:
    row = find_active_session_row(session, raw_token)
    if row is not None:
        row.revoked_at = datetime.now(UTC)


def csrf_matches(session_row: SessionRow, csrf_token: str | None) -> bool:
    if not csrf_token:
        return False
    return hmac.compare_digest(session_row.csrf_hash, hash_token(csrf_token))
