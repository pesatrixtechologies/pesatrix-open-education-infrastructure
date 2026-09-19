"""Derived attendance records.

Attendance is NOT stored directly from raw ``check_in`` events; those raw
events live in the immutable event store, and attendance records are *derived*
from them by deterministic rules. This keeps a clean, replayable audit trail
and makes offline reconstruction identical on every replica.

Derivation rules (see ``services.attendance``):

1. If an ``attendance_override`` event exists for (school, student, date),
   its ``payload.status`` wins.
2. Else, the latest ``check_in`` determines status: before the late
   threshold time -> ``present``; at or after it -> ``late``.
3. If there is no ``check_in`` and no override, the student is
   ``unrecorded`` (an absence is an explicit claim, not an inference).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from oe_infrastructure.modules.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AttendanceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "student_identity_id",
            "date",
            name="uq_attendance_school_student_date",
        ),
    )

    school_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    student_identity_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("student_identities.id"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source_event_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    derived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<AttendanceRecord {self.date} {self.student_identity_id!r} {self.status!r}>"