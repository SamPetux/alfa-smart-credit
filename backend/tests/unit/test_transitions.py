import pytest

from backend.app.schemas.enums import ApplicationStatus, Role, WorkflowCommand
from backend.app.workflow.transitions import IllegalTransitionError, next_status


def test_submit_draft_to_submitted() -> None:
    assert (
        next_status(
            ApplicationStatus.DRAFT,
            WorkflowCommand.SUBMIT,
            actor=Role.CLIENT,
        )
        == ApplicationStatus.SUBMITTED
    )


def test_client_cannot_approve() -> None:
    with pytest.raises(IllegalTransitionError):
        next_status(
            ApplicationStatus.MANUAL_REVIEW,
            WorkflowCommand.APPROVE_OFFER,
            actor=Role.CLIENT,
        )


def test_cannot_patch_terminal_via_submit() -> None:
    with pytest.raises(IllegalTransitionError):
        next_status(
            ApplicationStatus.COMPLETED,
            WorkflowCommand.SUBMIT,
            actor=Role.CLIENT,
        )
