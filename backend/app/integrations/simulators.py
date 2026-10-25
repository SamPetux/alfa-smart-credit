"""Локальные симуляторы реестра и БКИ. Без внешней сети."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from backend.app.integrations.fixtures import bureau_profile, registry_profile

Outcome = Literal["success", "timeout", "unavailable", "schema_error", "incomplete"]


@dataclass(frozen=True, slots=True)
class SourceResult:
    source: str
    outcome: Outcome
    payload: dict[str, Any]
    observed_at: datetime | None


def _parse_observed_at(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    text = str(raw).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def fetch_registry(scenario: str) -> SourceResult:
    data = registry_profile(scenario)
    return SourceResult(
        source="registry",
        outcome="success",
        payload=data,
        observed_at=_parse_observed_at(data.get("observed_at")),
    )


def fetch_bureau(scenario: str) -> SourceResult:
    data = bureau_profile(scenario)
    raw_outcome = str(data.get("outcome") or "success")
    if raw_outcome == "timeout":
        outcome: Outcome = "timeout"
    elif raw_outcome == "success_incomplete":
        outcome = "incomplete"
    elif raw_outcome in {"unavailable", "schema_error"}:
        outcome = raw_outcome  # type: ignore[assignment]
    else:
        outcome = "success"
    return SourceResult(
        source="bureau",
        outcome=outcome,
        payload=data,
        observed_at=_parse_observed_at(data.get("observed_at")),
    )
