"""Идемпотентные синтетические профили для demo и non-demo login.

Пароли только для DEMO_MODE=false. Не являются production credentials.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.identity.passwords import hash_password

# Документированные тестовые пароли (см. docs/demo-accounts.md)
TEST_PASSWORD_CLIENT = "client-demo-pass"
TEST_PASSWORD_OFFICER = "officer-demo-pass"


@dataclass(frozen=True, slots=True)
class SeedCompany:
    demo_registration_id: str
    display_name: str
    legal_form: str


@dataclass(frozen=True, slots=True)
class SeedUser:
    profile_id: str
    username: str
    role: str
    display_name: str
    password: str | None
    company_demo_id: str | None


COMPANIES: tuple[SeedCompany, ...] = (
    SeedCompany("DEMO-001", "ООО «Ромашка» (синтетика)", "OOO"),
    SeedCompany("DEMO-002", "ИП Иванов (синтетика)", "IP"),
)

USERS: tuple[SeedUser, ...] = (
    SeedUser(
        profile_id="client-romashka",
        username="client_romashka",
        role="CLIENT",
        display_name="Клиент · ООО Ромашка",
        password=TEST_PASSWORD_CLIENT,
        company_demo_id="DEMO-001",
    ),
    SeedUser(
        profile_id="client-ivanov",
        username="client_ivanov",
        role="CLIENT",
        display_name="Клиент · ИП Иванов",
        password=TEST_PASSWORD_CLIENT,
        company_demo_id="DEMO-002",
    ),
    SeedUser(
        profile_id="officer",
        username="officer",
        role="OFFICER",
        display_name="Кредитный специалист (синтетика)",
        password=TEST_PASSWORD_OFFICER,
        company_demo_id=None,
    ),
)

PRODUCTS: tuple[dict, ...] = (
    {
        "code": "WORKING_CAPITAL",
        "policy_version": "policy-v1",
        "limits_json": {
            "title": "Оборотный кредит",
            "amount_min": "100000.00",
            "amount_max": "3000000.00",
            "term_months": [6, 12, 18, 24],
            "description": "Демонстрационный продукт для пополнения оборотных средств",
        },
    },
    {
        "code": "EQUIPMENT",
        "policy_version": "policy-v1",
        "limits_json": {
            "title": "Кредит на оборудование",
            "amount_min": "300000.00",
            "amount_max": "5000000.00",
            "term_months": [12, 24, 36],
            "description": "Демонстрационный продукт на покупку оборудования",
        },
    },
)


def password_hash_for(password: str | None) -> str | None:
    if password is None:
        return None
    return hash_password(password)
