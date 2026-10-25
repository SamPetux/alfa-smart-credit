"""Демо-вход: только заранее созданные профили, только DEMO_MODE=true."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import Field
from sqlalchemy import select

from backend.app.db.models import User
from backend.app.identity.cookies import set_session_cookies
from backend.app.identity.deps import AppSettings, DbSession
from backend.app.identity.seed_data import USERS
from backend.app.identity.sessions import create_session
from backend.app.schemas.common import ApiModel, SessionInfo
from backend.app.schemas.enums import Role

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoProfile(ApiModel):
    id: str
    display_name: str
    role: Role


class DemoProfilesResponse(ApiModel):
    profiles: list[DemoProfile]


class DemoSessionRequest(ApiModel):
    profile_id: str = Field(min_length=1)


def _demo_disabled() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Demo mode is disabled",
    )


@router.get("/profiles", response_model=DemoProfilesResponse)
def list_demo_profiles(settings: AppSettings) -> DemoProfilesResponse:
    if not settings.demo_mode:
        raise _demo_disabled()
    return DemoProfilesResponse(
        profiles=[
            DemoProfile(id=u.profile_id, display_name=u.display_name, role=Role(u.role))
            for u in USERS
        ]
    )


@router.post("/session", response_model=SessionInfo)
def create_demo_session(
    body: DemoSessionRequest,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> SessionInfo:
    if not settings.demo_mode:
        raise _demo_disabled()

    seed_user = next((u for u in USERS if u.profile_id == body.profile_id), None)
    if seed_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown demo profile")

    user = db.scalar(select(User).where(User.username == seed_user.username, User.active.is_(True)))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo profile not seeded",
        )

    issued = create_session(db, user, settings=settings)
    db.flush()
    set_session_cookies(response, issued, settings)
    return issued.info
