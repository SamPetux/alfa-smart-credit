"""Интеграция: alembic upgrade на реальном PostgreSQL.

Требует DATABASE_URL. Без переменной — skip (локально/CI без БД).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def engine():
    url = os.environ["DATABASE_URL"]
    eng = create_engine(url, future=True)
    yield eng
    eng.dispose()


def test_alembic_upgrade_creates_tables(engine) -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    # URL берёт env.py из DATABASE_URL
    command.upgrade(cfg, "head")

    names = set(inspect(engine).get_table_names())
    assert "applications" in names
    assert "jobs" in names
    assert "risk_assessments" in names
    assert "alembic_version" in names

    with engine.connect() as conn:
        fk = conn.execute(
            text(
                "SELECT 1 FROM pg_constraint WHERE conname = 'fk_applications_active_run'"
            )
        ).scalar()
        assert fk == 1
