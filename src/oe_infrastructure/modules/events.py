"""Immutable educational event store.

Events are append-only. Records are never updated or deleted; corrections are
modelled as new events referencing a ``parent_event_id``. This design:

- preserves an auditable, forensic history of what happened,
- makes offline replay safe (idempotency by ``idempotency_key``),
- makes distributed replication and conflict handling tractable,
- gives analysts a clean, immutable source of truth.

A global monotonic ``seq`` column is the synchronization watermark used by the
sync engine for incremental downloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class EducationalEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "educational_events"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_events_idempotency_key",
        ),
    )

    seq: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False, start=1, increment=1),
        unique=True,
        nullable=False,
        index=True,
    )
    school_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    student_identity_id: Mapped[Any | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("student_identities.id"), nullable=True
    )
    event_kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    device_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False, default="api")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parent_event_id: Mapped[Any | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("educational_events.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    parent = relationship("EducationalEvent", remote_side="EducationalEvent.id")

    def __repr__(self) -> str:
        return f"<EducationalEvent seq={self.seq} kind={self.event_kind!r}>"
