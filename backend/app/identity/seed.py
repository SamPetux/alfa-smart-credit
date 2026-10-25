"""Идемпотентный seed: компании, пользователи, продукты.

Не сбрасывает заявки. Безопасно вызывать повторно (B08 init).
"""

from __future__ import annotations

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Company, Membership, Product, User
from backend.app.db.session import session_scope
from backend.app.identity.seed_data import COMPANIES, PRODUCTS, USERS, password_hash_for


def seed_session(session: Session) -> dict[str, int]:
    created = {"companies": 0, "users": 0, "memberships": 0, "products": 0}

    companies_by_demo: dict[str, Company] = {}
    for item in COMPANIES:
        existing = session.scalar(
            select(Company).where(Company.demo_registration_id == item.demo_registration_id)
        )
        if existing is None:
            existing = Company(
                display_name=item.display_name,
                demo_registration_id=item.demo_registration_id,
                legal_form=item.legal_form,
            )
            session.add(existing)
            session.flush()
            created["companies"] += 1
        else:
            existing.display_name = item.display_name
            existing.legal_form = item.legal_form
        companies_by_demo[item.demo_registration_id] = existing

    for item in USERS:
        user = session.scalar(select(User).where(User.username == item.username))
        if user is None:
            user = User(
                username=item.username,
                role=item.role,
                display_name=item.display_name,
                password_hash=password_hash_for(item.password),
                active=True,
            )
            session.add(user)
            session.flush()
            created["users"] += 1
        else:
            user.role = item.role
            user.display_name = item.display_name
            user.active = True
            # Пароль не перезаписываем при повторном seed, чтобы не ломать локальные смены.
            if user.password_hash is None and item.password:
                user.password_hash = password_hash_for(item.password)

        if item.company_demo_id is not None:
            company = companies_by_demo[item.company_demo_id]
            membership = session.scalar(
                select(Membership).where(
                    Membership.user_id == user.id,
                    Membership.company_id == company.id,
                )
            )
            if membership is None:
                # P0: один user — одна компания; снести старые связи при смене seed
                old = session.scalars(select(Membership).where(Membership.user_id == user.id)).all()
                for row in old:
                    session.delete(row)
                session.flush()
                session.add(Membership(user_id=user.id, company_id=company.id))
                created["memberships"] += 1

    for item in PRODUCTS:
        product = session.scalar(select(Product).where(Product.code == item["code"]))
        if product is None:
            session.add(
                Product(
                    code=item["code"],
                    policy_version=item["policy_version"],
                    limits_json=item["limits_json"],
                    active=True,
                )
            )
            created["products"] += 1
        else:
            product.policy_version = item["policy_version"]
            product.limits_json = item["limits_json"]
            product.active = True

    return created


def run_seed() -> dict[str, int]:
    with session_scope() as session:
        counts = seed_session(session)
    return counts


def main() -> None:
    counts = run_seed()
    print(f"seed ok: {counts}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — CLI exit
        print(f"seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
