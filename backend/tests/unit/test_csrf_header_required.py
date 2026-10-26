"""CSRF: мутации требуют X-CSRF-Token; cookie alone недостаточно."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.identity.deps import AuthContext, require_csrf
from backend.app.identity.tokens import hash_token


def _auth(*, csrf_plain: str) -> AuthContext:
    user = SimpleNamespace(id=uuid4(), role="CLIENT", active=True)
    row = SimpleNamespace(csrf_hash=hash_token(csrf_plain), user_id=user.id)
    return AuthContext(user=user, session_row=row, company_id=uuid4(), csrf_token=csrf_plain)


def test_require_csrf_rejects_missing_header() -> None:
    token = "csrf-plain-token-value"
    auth = _auth(csrf_plain=token)
    request = MagicMock()
    request.method = "POST"
    with pytest.raises(HTTPException) as exc:
        require_csrf(request, auth, csrf_header=None)
    assert exc.value.status_code == 403


def test_require_csrf_rejects_cookie_only_fallback() -> None:
    """Раньше deps подставлял cookie при отсутствии заголовка — double-submit ломался."""
    token = "csrf-plain-token-value"
    auth = _auth(csrf_plain=token)
    request = MagicMock()
    request.method = "PATCH"
    with pytest.raises(HTTPException) as exc:
        require_csrf(request, auth, csrf_header="")
    assert exc.value.status_code == 403


def test_require_csrf_accepts_matching_header() -> None:
    token = "csrf-plain-token-value"
    auth = _auth(csrf_plain=token)
    request = MagicMock()
    request.method = "POST"
    out = require_csrf(request, auth, csrf_header=token)
    assert out is auth
