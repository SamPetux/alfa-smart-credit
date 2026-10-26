"""B09: structured log без forbidden полей."""

from __future__ import annotations

import json
import logging

import pytest

from backend.app.core.logging_utils import log_event
from backend.app.core.request_context import clear_request_context, set_request_id


def test_log_event_json_and_strips_secrets(caplog: pytest.LogCaptureFixture) -> None:
    set_request_id("req-test-1")
    with caplog.at_level(logging.INFO, logger="asc"):
        log_event(
            "TEST_EVENT",
            application_id="app-1",
            password="secret",
            token="tok",
            ok_field=42,
        )
    clear_request_context()

    assert caplog.records
    payload = json.loads(caplog.records[-1].message)
    assert payload["event_code"] == "TEST_EVENT"
    assert payload["request_id"] == "req-test-1"
    assert payload["ok_field"] == 42
    assert "password" not in payload
    assert "token" not in payload
