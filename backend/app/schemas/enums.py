"""Канонические enum статусов и действий. Зеркало contracts/statuses.json."""

from enum import StrEnum


class ApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    CHECKING = "CHECKING"
    NEEDS_INFO = "NEEDS_INFO"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    SIGNED = "SIGNED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    DECLINED_BY_CLIENT = "DECLINED_BY_CLIENT"


TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.COMPLETED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.DECLINED_BY_CLIENT,
    }
)


class AllowedAction(StrEnum):
    SAVE = "SAVE"
    SUBMIT = "SUBMIT"
    SAVE_SUPPLEMENT = "SAVE_SUPPLEMENT"
    RESUBMIT = "RESUBMIT"
    ACCEPT_OFFER = "ACCEPT_OFFER"
    DECLINE_OFFER = "DECLINE_OFFER"
    SIMULATE_SIGN = "SIMULATE_SIGN"
    REQUEST_INFO = "REQUEST_INFO"
    APPROVE_OFFER = "APPROVE_OFFER"
    REJECT = "REJECT"
    RETRY_CHECKS = "RETRY_CHECKS"
    RETRY_DISBURSEMENT = "RETRY_DISBURSEMENT"


class Role(StrEnum):
    CLIENT = "CLIENT"
    OFFICER = "OFFICER"


class ProductCode(StrEnum):
    WORKING_CAPITAL = "WORKING_CAPITAL"
    EQUIPMENT = "EQUIPMENT"


class RiskRecommendation(StrEnum):
    OFFER = "OFFER"
    REJECT = "REJECT"
    NEEDS_INFO = "NEEDS_INFO"


class DecisionType(StrEnum):
    APPROVE_OFFER = "APPROVE_OFFER"
    REJECT = "REJECT"


class WorkflowCommand(StrEnum):
    SAVE = "save"
    SUBMIT = "submit"
    START = "start"
    REQUIRE_INFO = "require_info"
    FINISH = "finish"
    PROCESSING_FAILED = "processing_failed"
    RETRY_CHECKS = "retry_checks"
    SAVE_SUPPLEMENT = "save_supplement"
    RESUBMIT = "resubmit"
    REQUEST_INFO = "request_info"
    APPROVE_OFFER = "approve_offer"
    REJECT = "reject"
    ACCEPT_OFFER = "accept_offer"
    DECLINE_OFFER = "decline_offer"
    SIMULATE_SIGN = "simulate_sign"
    COMPLETE_SIMULATION = "complete_simulation"
