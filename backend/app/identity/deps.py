"""FastAPI-зависимости: текущий пользователь, роль, CSRF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import Membership, SessionRow, User
from backend.app.db.session import get_session_factory
from backend.app.identity.cookies import CSRF_COOKIE
from backend.app.identity.sessions import csrf_matches, find_active_session_row
from backend.app.schemas.enums import Role


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: User
    session_row: SessionRow
    company_id: UUID | None
    csrf_token: str


def get_db():
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _forbidden(detail: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_optional_auth(
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> AuthContext | None:
    raw = request.cookies.get(settings.cookie_name)
    row = find_active_session_row(db, raw)
    if row is None or not row.user.active:
        return None
    membership = db.scalar(select(Membership).where(Membership.user_id == row.user_id))
    csrf = request.cookies.get(CSRF_COOKIE) or ""
    return AuthContext(
        user=row.user,
        session_row=row,
        company_id=membership.company_id if membership else None,
        csrf_token=csrf,
    )


def require_auth(auth: Annotated[AuthContext | None, Depends(get_optional_auth)]) -> AuthContext:
    if auth is None:
        raise _unauthorized()
    return auth


def require_csrf(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth)],
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> AuthContext:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return auth
    token = csrf_header or auth.csrf_token
    if not csrf_matches(auth.session_row, token):
        raise _forbidden("CSRF token mismatch")
    return auth


def require_role(*roles: Role):
    allowed = {r.value for r in roles}

    def _dep(auth: Annotated[AuthContext, Depends(require_auth)]) -> AuthContext:
        if auth.user.role not in allowed:
            raise _forbidden(f"Role {auth.user.role} not allowed")
        return auth

    return _dep


RequireAuth = Annotated[AuthContext, Depends(require_auth)]
RequireCsrf = Annotated[AuthContext, Depends(require_csrf)]
RequireClient = Annotated[AuthContext, Depends(require_role(Role.CLIENT))]
RequireOfficer = Annotated[AuthContext, Depends(require_role(Role.OFFICER))]
