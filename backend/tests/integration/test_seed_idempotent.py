"""B08: повторный seed не сбрасывает заявки и сохраняет демо-аккаунты."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import func, select

from backend.app.db.models import Application, Membership, Product, User
from backend.app.db.session import get_session_factory
from backend.app.identity.seed import run_seed

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)


def test_seed_twice_preserves_application(client) -> None:
    # client fixture: migrate + seed уже выполнены
    session = get_session_factory()()
    try:
        product = session.scalar(select(Product).where(Product.code == "WORKING_CAPITAL"))
        assert product is not None
        user = session.scalar(select(User).where(User.username == "client_romashka"))
        assert user is not None
        membership = session.scalar(select(Membership).where(Membership.user_id == user.id))
        assert membership is not None

        app = Application(
            company_id=membership.company_id,
            product_id=product.id,
            creator_id=user.id,
            status="DRAFT",
            version=1,
            current_revision=0,
            draft_json={"purpose": "working_capital"},
        )
        session.add(app)
        session.commit()
        app_id = app.id
        before = session.scalar(select(func.count()).select_from(Application))
    finally:
        session.close()

    counts = run_seed()
    assert isinstance(counts, dict)

    session = get_session_factory()()
    try:
        after = session.scalar(select(func.count()).select_from(Application))
        assert after == before
        assert session.get(Application, app_id) is not None
        assert session.scalar(select(User).where(User.username == "client_romashka")) is not None
        n_products = session.scalar(select(func.count()).select_from(Product))
        assert n_products == 2
    finally:
        session.close()
