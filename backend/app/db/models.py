"""ORM-модели по docs/planning/02-architecture.md §5.

Деньги — Numeric(18, 2). Сырой session token не хранится (только token_hash).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

Money = Numeric(18, 2)


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = _uuid_pk()
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")
    sessions: Mapped[list[SessionRow]] = relationship(back_populates="user")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = _uuid_pk()
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    demo_registration_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    legal_form: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    memberships: Mapped[list[Membership]] = relationship(back_populates="company")
    applications: Mapped[list[Application]] = relationship(back_populates="company")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_memberships_user_company"),
        # P0: один клиент — одна компания
        UniqueConstraint("user_id", name="uq_memberships_user"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    company: Mapped[Company] = relationship(back_populates="memberships")


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)

    id: Mapped[UUID] = _uuid_pk()
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    csrf_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    limits_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_company_id", "company_id"),
        Index("ix_applications_status", "status"),
        CheckConstraint("version >= 1", name="ck_applications_version_ge_1"),
        CheckConstraint("current_revision >= 0", name="ck_applications_revision_ge_0"),
    )

    id: Mapped[UUID] = _uuid_pk()
    company_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    creator_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'DRAFT'"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    active_run_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", use_alter=True, name="fk_applications_active_run"),
        nullable=True,
    )
    draft_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[Company] = relationship(back_populates="applications")
    revisions: Mapped[list[ApplicationRevision]] = relationship(back_populates="application")


class ApplicationRevision(Base):
    __tablename__ = "application_revisions"
    __table_args__ = (
        UniqueConstraint("application_id", "revision_no", name="uq_application_revisions_app_no"),
    )

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped[Application] = relationship(back_populates="revisions")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_application_id", "application_id"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        UniqueConstraint("application_id", "revision_no", "run_no", name="uq_evaluation_runs_app_rev_run"),
        Index("ix_evaluation_runs_application_id", "application_id"),
    )

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    run_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    checks: Mapped[list[IntegrationCheck]] = relationship(back_populates="run")
    risk_assessment: Mapped[RiskAssessment | None] = relationship(back_populates="run")


class IntegrationCheck(Base):
    __tablename__ = "integration_checks"
    __table_args__ = (Index("ix_integration_checks_run_id", "run_id"),)

    id: Mapped[UUID] = _uuid_pk()
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    run: Mapped[EvaluationRun] = relationship(back_populates="checks")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (UniqueConstraint("run_id", name="uq_risk_assessments_run"),)

    id: Mapped[UUID] = _uuid_pk()
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    band: Mapped[str | None] = mapped_column(String(8), nullable=True)
    factors_json: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    affordability_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    reasons_json: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    candidate_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped[EvaluationRun] = relationship(back_populates="risk_assessment")


class InfoRequest(Base):
    __tablename__ = "info_requests"
    __table_args__ = (Index("ix_info_requests_application_id", "application_id"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    based_on_run_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=True
    )
    fields_json: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    document_kinds_json: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_application_id", "application_id"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    officer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    offer: Mapped[Offer | None] = relationship(back_populates="decision")


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (Index("ix_offers_application_id", "application_id"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    decision_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("decisions.id"), unique=True, nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    terms_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    decision: Mapped[Decision] = relationship(back_populates="offer")
    agreement: Mapped[Agreement | None] = relationship(back_populates="offer")


class Agreement(Base):
    __tablename__ = "agreements"
    __table_args__ = (UniqueConstraint("offer_id", name="uq_agreements_offer"),)

    id: Mapped[UUID] = _uuid_pk()
    offer_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("offers.id"), nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    offer: Mapped[Offer] = relationship(back_populates="agreement")
    disbursement: Mapped[DisbursementSimulation | None] = relationship(back_populates="agreement")


class DisbursementSimulation(Base):
    __tablename__ = "disbursement_simulations"
    __table_args__ = (UniqueConstraint("application_id", name="uq_disbursement_simulations_application"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    agreement_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("agreements.id"), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    agreement: Mapped[Agreement] = relationship(back_populates="disbursement")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_claim", "state", "available_at"),
        Index("ix_jobs_application_id", "application_id"),
    )

    id: Mapped[UUID] = _uuid_pk()
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=True
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "actor_id",
            "command_scope",
            "idempotency_key",
            name="uq_idempotency_actor_scope_key",
        ),
    )

    id: Mapped[UUID] = _uuid_pk()
    actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    command_scope: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    body_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_application_id", "application_id"),)

    id: Mapped[UUID] = _uuid_pk()
    application_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    revision_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
