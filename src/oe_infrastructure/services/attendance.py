"""Attendance derivation service.

Pure derivation function ``derive_status`` is exported separately so it can
be unit-tested without a database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import ValidationFailure
from oe_infrastructure.modules.attendance import AttendanceRecord
from oe_infrastructure.modules.enums import AttendanceStatus, EventKind
from oe_infrastructure.modules.events import EducationalEvent
from oe_infrastructure.modules.identity import StudentIdentity

# Default: any check-in at or after 09:30 local counts as "late".
LATE_THRESHOLD = time.fromisoformat("09:30")


def derive_status(
    check_ins: list[datetime],
    override: str | None = None,
    *,
    late_threshold: time = LATE_THRESHOLD,
) -> AttendanceStatus:
    """Derive a single student's attendance status deterministically."""
    if override is not None:
        try:
            return AttendanceStatus(override)
        except ValueError as err:
            raise ValidationFailure(
                f"Invalid override status '{override}'",
                code="invalid_status",
            ) from err
    if not check_ins:
        return AttendanceStatus.UNRECORDED
    latest = max(check_ins)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=UTC)
    if latest.time() < late_threshold:
        return AttendanceStatus.PRESENT
    return AttendanceStatus.LATE


async def rollup_attendance(
    session: AsyncSession,
    school_id: uuid.UUID,
    day: date,
) -> list[AttendanceRecord]:
    """Compute (or recompute) attendance records for a school on a date."""
    students = await _active_students(session, school_id)
    events = await _events_for_day(session, school_id, day)

    records: list[AttendanceRecord] = []
    for student in students:
        check_ins = [
            evt.occurred_at
            for evt in events[student.id]
            if evt.event_kind == EventKind.CHECK_IN.value
        ]
        overrides = [
            evt
            for evt in events[student.id]
            if evt.event_kind == EventKind.ATTENDANCE_OVERRIDE.value
        ]

        override_status: str | None = None
        source_event_id: uuid.UUID | None = None
        if overrides:
            latest_override = max(overrides, key=lambda evt: evt.occurred_at)
            override_status = (latest_override.payload or {}).get("status")
            source_event_id = latest_override.id
        elif check_ins:
            latest_check_in = max(events[student.id], key=lambda evt: evt.occurred_at)
            source_event_id = latest_check_in.id

        status = derive_status(check_ins, override_status)

        existing = await session.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.school_id == school_id,
                AttendanceRecord.student_identity_id == student.id,
                AttendanceRecord.date == day,
            )
        )
        record = existing.scalar_one_or_none()
        if record is None:
            record = AttendanceRecord(
                school_id=school_id,
                student_identity_id=student.id,
                date=day,
                status=status.value,
                source_event_id=source_event_id,
                derived_at=datetime.now(UTC),
            )
            session.add(record)
        else:
            record.status = status.value
            record.source_event_id = source_event_id
            record.derived_at = datetime.now(UTC)
        records.append(record)

    return records


async def _active_students(
    session: AsyncSession,
    school_id: uuid.UUID,
) -> list[StudentIdentity]:
    result = await session.execute(
        select(StudentIdentity).where(
            StudentIdentity.school_id == school_id,
            StudentIdentity.status == "active",
        )
    )
    return list(result.scalars().all())


async def _events_for_day(
    session: AsyncSession,
    school_id: uuid.UUID,
    day: date,
) -> dict[uuid.UUID, list[EducationalEvent]]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = datetime.combine(day, time.max, tzinfo=UTC)
    result = await session.execute(
        select(EducationalEvent).where(
            EducationalEvent.school_id == school_id,
            EducationalEvent.occurred_at >= start,
            EducationalEvent.occurred_at <= end,
        )
    )
    grouped: dict[uuid.UUID, list[EducationalEvent]] = {}
    for evt in result.scalars().all():
        if evt.student_identity_id is None:
            continue
        grouped.setdefault(evt.student_identity_id, []).append(evt)
    return grouped


async def list_attendance(
    session: AsyncSession,
    *,
    school_id: uuid.UUID,
    day: date | None,
    student_identity_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[AttendanceRecord], int]:
    query = select(AttendanceRecord)
    count_query = select(func.count()).select_from(AttendanceRecord)
    query = query.where(AttendanceRecord.school_id == school_id)
    count_query = count_query.where(AttendanceRecord.school_id == school_id)
    if day is not None:
        query = query.where(AttendanceRecord.date == day)
        count_query = count_query.where(AttendanceRecord.date == day)
    if student_identity_id is not None:
        query = query.where(AttendanceRecord.student_identity_id == student_identity_id)
        count_query = count_query.where(AttendanceRecord.student_identity_id == student_identity_id)
    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(AttendanceRecord.date.desc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total
