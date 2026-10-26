"""Загрузка локальных JSON-профилей симуляторов (владелец содержимого — Илья)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROFILES = _REPO_ROOT / "fixtures" / "profiles"


@lru_cache
def _load(name: str) -> dict[str, Any]:
    path = _PROFILES / name
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def registry_profile(scenario: str) -> dict[str, Any]:
    # Пока один реестр; сценарии отличает БКИ
    return dict(_load("registry_active_30m.json"))


def bureau_profile(scenario: str) -> dict[str, Any]:
    mapping = {
        "g01": "bureau_g01.json",
        "g04": "bureau_g04_overdue.json",
        "timeout": "bureau_timeout.json",
        "incomplete": "bureau_incomplete_overdue.json",
    }
    filename = mapping.get(scenario, "bureau_g01.json")
    return dict(_load(filename))


# Профиль симулятора задаёт сервер по компании, не клиентский PATCH.
_COMPANY_SCENARIOS: dict[str, str] = {
    "DEMO-001": "g01",
    "DEMO-002": "g01",
}


def resolve_scenario(*, demo_registration_id: str | None, draft: dict[str, Any]) -> str:
    """Сценарий источника — только по demo_registration_id (draft игнорируется)."""
    del draft  # контракт вызова worker сохранён; клиентский override запрещён
    if not demo_registration_id:
        return "g01"
    return _COMPANY_SCENARIOS.get(demo_registration_id, "g01")
