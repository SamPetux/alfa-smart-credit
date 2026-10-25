"""Обычный вход тестовых пользователей (хешированные пароли) и /me /logout."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import Field
from sqlalchemy import select

from backend.app.db.models import User
from backend.app.identity.cookies import clear_session_cookies, set_session_cookies
from backend.app.identity.deps import AppSettings, DbSession, RequireAuth
from backend.app.identity.passwords import verify_password
from backend.app.identity.sessions import create_session, revoke_session_by_token, session_info_for
from backend.app.schemas.common import ApiModel, SessionInfo

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(ApiModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login", response_model=SessionInfo)
def login(
    body: LoginRequest,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> SessionInfo:
    # В demo mode login тоже работает — для не-демо стенда основной путь.
    user = db.scalar(select(User).where(User.username == body.username, User.active.is_(True)))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    issued = create_session(db, user, settings=settings)
    db.flush()
    set_session_cookies(response, issued, settings)
    return issued.info


@router.get("/me", response_model=SessionInfo)
def me(
    db: DbSession,
    settings: AppSettings,
    auth: RequireAuth,
) -> SessionInfo:
    return session_info_for(db, auth.session_row, auth.csrf_token, settings=settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> None:
    raw = request.cookies.get(settings.cookie_name)
    revoke_session_by_token(db, raw)
    clear_session_cookies(response, settings)
