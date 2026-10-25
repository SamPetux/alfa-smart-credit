"""Установка/сброс session и CSRF cookies."""

from __future__ import annotations

from fastapi import Response

from backend.app.core.config import Settings
from backend.app.identity.sessions import IssuedSession

CSRF_COOKIE = "asc_csrf"


def set_session_cookies(response: Response, issued: IssuedSession, settings: Settings) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=issued.raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        expires=issued.expires_at,
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=issued.csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        expires=issued.expires_at,
    )


def clear_session_cookies(response: Response, settings: Settings) -> None:
    for name, httponly in ((settings.cookie_name, True), (CSRF_COOKIE, False)):
        response.delete_cookie(
            key=name,
            path="/",
            httponly=httponly,
            samesite="lax",
            secure=settings.cookie_secure,
        )
