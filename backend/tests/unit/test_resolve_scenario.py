"""Сценарий симулятора — только по компании, не из клиентского draft."""

from backend.app.integrations.fixtures import resolve_scenario


def test_resolve_ignores_draft_demo_scenario() -> None:
    assert (
        resolve_scenario(
            demo_registration_id="DEMO-001",
            draft={"demo_scenario": "timeout"},
        )
        == "g01"
    )


def test_resolve_demo_002_is_overdue_bureau() -> None:
    assert resolve_scenario(demo_registration_id="DEMO-002", draft={}) == "g04"


def test_resolve_defaults_without_company() -> None:
    assert resolve_scenario(demo_registration_id=None, draft={}) == "g01"
