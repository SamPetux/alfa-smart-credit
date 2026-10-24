"""Таблица разрешённых переходов state machine. Зеркало contracts/statuses.json."""

from backend.app.schemas.enums import ApplicationStatus, Role, WorkflowCommand

TransitionKey = tuple[ApplicationStatus, WorkflowCommand]

# (from_status, command) -> to_status
TRANSITIONS: dict[TransitionKey, ApplicationStatus] = {
    (ApplicationStatus.DRAFT, WorkflowCommand.SAVE): ApplicationStatus.DRAFT,
    (ApplicationStatus.DRAFT, WorkflowCommand.SUBMIT): ApplicationStatus.SUBMITTED,
    (ApplicationStatus.SUBMITTED, WorkflowCommand.START): ApplicationStatus.CHECKING,
    (ApplicationStatus.CHECKING, WorkflowCommand.REQUIRE_INFO): ApplicationStatus.NEEDS_INFO,
    (ApplicationStatus.CHECKING, WorkflowCommand.FINISH): ApplicationStatus.MANUAL_REVIEW,
    (
        ApplicationStatus.CHECKING,
        WorkflowCommand.PROCESSING_FAILED,
    ): ApplicationStatus.PROCESSING_ERROR,
    (
        ApplicationStatus.PROCESSING_ERROR,
        WorkflowCommand.RETRY_CHECKS,
    ): ApplicationStatus.SUBMITTED,
    (
        ApplicationStatus.NEEDS_INFO,
        WorkflowCommand.SAVE_SUPPLEMENT,
    ): ApplicationStatus.NEEDS_INFO,
    (ApplicationStatus.NEEDS_INFO, WorkflowCommand.RESUBMIT): ApplicationStatus.SUBMITTED,
    (
        ApplicationStatus.MANUAL_REVIEW,
        WorkflowCommand.REQUEST_INFO,
    ): ApplicationStatus.NEEDS_INFO,
    (ApplicationStatus.MANUAL_REVIEW, WorkflowCommand.APPROVE_OFFER): ApplicationStatus.OFFERED,
    (ApplicationStatus.MANUAL_REVIEW, WorkflowCommand.REJECT): ApplicationStatus.REJECTED,
    (ApplicationStatus.OFFERED, WorkflowCommand.ACCEPT_OFFER): ApplicationStatus.ACCEPTED,
    (
        ApplicationStatus.OFFERED,
        WorkflowCommand.DECLINE_OFFER,
    ): ApplicationStatus.DECLINED_BY_CLIENT,
    (ApplicationStatus.ACCEPTED, WorkflowCommand.SIMULATE_SIGN): ApplicationStatus.SIGNED,
    (
        ApplicationStatus.SIGNED,
        WorkflowCommand.COMPLETE_SIMULATION,
    ): ApplicationStatus.COMPLETED,
}

COMMAND_ACTORS: dict[WorkflowCommand, frozenset[Role | str]] = {
    WorkflowCommand.SAVE: frozenset({Role.CLIENT}),
    WorkflowCommand.SUBMIT: frozenset({Role.CLIENT}),
    WorkflowCommand.START: frozenset({"WORKER"}),
    WorkflowCommand.REQUIRE_INFO: frozenset({"WORKER"}),
    WorkflowCommand.FINISH: frozenset({"WORKER"}),
    WorkflowCommand.PROCESSING_FAILED: frozenset({"WORKER"}),
    WorkflowCommand.RETRY_CHECKS: frozenset({Role.OFFICER}),
    WorkflowCommand.SAVE_SUPPLEMENT: frozenset({Role.CLIENT}),
    WorkflowCommand.RESUBMIT: frozenset({Role.CLIENT}),
    WorkflowCommand.REQUEST_INFO: frozenset({Role.OFFICER}),
    WorkflowCommand.APPROVE_OFFER: frozenset({Role.OFFICER}),
    WorkflowCommand.REJECT: frozenset({Role.OFFICER}),
    WorkflowCommand.ACCEPT_OFFER: frozenset({Role.CLIENT}),
    WorkflowCommand.DECLINE_OFFER: frozenset({Role.CLIENT}),
    WorkflowCommand.SIMULATE_SIGN: frozenset({Role.CLIENT}),
    WorkflowCommand.COMPLETE_SIMULATION: frozenset({"WORKER"}),
}


class IllegalTransitionError(ValueError):
    """Команда недопустима в текущем статусе или для данного актора."""


def next_status(
    current: ApplicationStatus,
    command: WorkflowCommand,
    *,
    actor: Role | str,
) -> ApplicationStatus:
    allowed_actors = COMMAND_ACTORS.get(command)
    if allowed_actors is None or actor not in allowed_actors:
        raise IllegalTransitionError(
            f"Actor {actor!r} cannot run command {command.value}"
        )
    key = (current, command)
    if key not in TRANSITIONS:
        raise IllegalTransitionError(
            f"Command {command.value} is not allowed from {current.value}"
        )
    return TRANSITIONS[key]
