"""Контракт ORM: все таблицы архитектуры §5 зарегистрированы в metadata."""

from backend.app.db.base import Base
from backend.app.db import models  # noqa: F401


EXPECTED_TABLES = {
    "users",
    "companies",
    "memberships",
    "sessions",
    "products",
    "applications",
    "application_revisions",
    "documents",
    "evaluation_runs",
    "integration_checks",
    "risk_assessments",
    "info_requests",
    "decisions",
    "offers",
    "agreements",
    "disbursement_simulations",
    "jobs",
    "idempotency_records",
    "audit_events",
}


def test_metadata_contains_architecture_tables() -> None:
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_applications_have_active_run_fk() -> None:
    apps = Base.metadata.tables["applications"]
    fk_names = {fk.name for fk in apps.foreign_keys}
    assert "fk_applications_active_run" in fk_names


def test_money_column_precision() -> None:
    amount = Base.metadata.tables["disbursement_simulations"].c.amount
    assert amount.type.precision == 18
    assert amount.type.scale == 2
