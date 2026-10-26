from backend.app.explanations.assistant import explain_application


def test_explain_templates_no_llm() -> None:
    out = explain_application(
        status="OFFERED",
        reason_codes=["LOWER_AMOUNT_REQUIRED"],
        recommendation="OFFER",
        topic="why",
    )
    assert out["uses_llm"] is False
    assert out["engine"] == "template-v1"
    assert "LOWER_AMOUNT_REQUIRED" in out["reason_codes"]
    assert out["bullets"]
    assert "принят" in out["next_step"].lower() or "отклон" in out["next_step"].lower()
