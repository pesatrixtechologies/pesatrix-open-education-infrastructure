"""Attendance routes."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.enums import AttendanceStatus
from oe_infrastructure.modules.identity import StudentIdentity
from oe_infrastructure.schemas.schemas import (
    AttendanceRecordResponse,
    AttendanceSummaryEntry,
    AttendanceSummaryResponse,
    MessageResponse,
)
from oe_infrastructure.services.attendance import list_attendance, rollup_attendance
from oe_infrastructure.services.audit import audit

router = APIRouter()


@router.post(
    "/rollup",
    response_model=MessageResponse,
    summary="Compute (or recompute) attendance records for a school on a date",
    dependencies=[Depends(require_role_at_least(Role.OPERATOR)), Depends(rate_limit(30))],
)
async def rollup(
    school_id: uuid.UUID,
    day: date,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> MessageResponse:
    records = await rollup_attendance(session, school_id, day)
    await audit(
        session,
        action="update",
        resource_type="attendance_rollup",
        resource_id=str(school_id),
        actor_type="user",
        actor_id=str(actor.id),
        school_id=school_id,
        data={"date": day.isoformat(), "records": len(records)},
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return MessageResponse(
        message="Attendance rollup complete",
        details={"school_id": str(school_id), "day": day.isoformat(), "records": len(records)},
    )


@router.get(
    "",
    response_model=list[AttendanceRecordResponse],
    summary="List attendance records",
    dependencies=[Depends(rate_limit(120))],
)
async def list_records(
    session: SessionDep,
    school_id: uuid.UUID,
    day: date | None = None,
    student_identity_id: uuid.UUID | None = None,
) -> list[AttendanceRecordResponse]:
    records, _ = await list_attendance(
        session,
        school_id=school_id,
        day=day,
        student_identity_id=student_identity_id,
    )
    return [AttendanceRecordResponse.model_validate(r) for r in records]


@router.get(
    "/summary",
    response_model=AttendanceSummaryResponse,
    summary="Attendance summary counts for a school on a date",
    dependencies=[Depends(rate_limit(120))],
)
async def summary(
    session: SessionDep,
    school_id: uuid.UUID,
    day: date | None = None,
) -> AttendanceSummaryResponse:
    counts = {
        AttendanceStatus.PRESENT.value: 0,
        AttendanceStatus.LATE.value: 0,
        AttendanceStatus.ABSENT.value: 0,
        AttendanceStatus.EXCUSED.value: 0,
        AttendanceStatus.UNRECORDED.value: 0,
    }
    if day is not None:
        records, _ = await list_attendance(session, school_id=school_id, day=day)
        for record in records:
            counts[record.status] = counts.get(record.status, 0) + 1

    total_students = await session.scalar(
        select(func.count())
        .select_from(StudentIdentity)
        .where(StudentIdentity.school_id == school_id, StudentIdentity.status == "active")
    ) or 0
    day_label = day.isoformat() if day else "all"

    return AttendanceSummaryResponse(
        school_id=school_id,
        date=day_label,
        total_students=total_students,
        entries=[
            AttendanceSummaryEntry(
                date=day_label,
                present=counts[AttendanceStatus.PRESENT.value],
                late=counts[AttendanceStatus.LATE.value],
                absent=counts[AttendanceStatus.ABSENT.value],
                excused=counts[AttendanceStatus.EXCUSED.value],
                unrecorded=counts[AttendanceStatus.UNRECORDED.value],
                total=sum(counts.values()),
            )
        ],
    )