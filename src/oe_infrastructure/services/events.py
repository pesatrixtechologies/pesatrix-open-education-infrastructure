"""Educational event store service.

Events are immutable and appended with a monotonic ``seq`` watermark.
Idempotent ingestion is guaranteed by a unique ``idempotency_key``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import ConflictError, NotFoundError
from oe_infrastructure.modules.enums import EventKind
from oe_infrastructure.modules.events import EducationalEvent
from oe_infrastructure.schemas.schemas import EducationalEventCreate


async def _normalize_occurred_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def record_event(
    session: AsyncSession,
    payload: EducationalEventCreate,
    *,
    seq: int | None = None,
) -> tuple[EducationalEvent, bool]:
    """Record an event or return the existing one for the same idempotency key.

    Returns ``(event, created)`` where ``created`` is ``False`` when the call
    was a duplicate of an already-recorded event. ``seq`` is normally assigned
    by the database; supplying it explicitly is only for raw bootstrap paths.
    """
    occurred_at = await _normalize_occurred_at(payload.occurred_at)

    if payload.idempotency_key:
        existing = await session.execute(
            select(EducationalEvent).where(
                EducationalEvent.idempotency_key == payload.idempotency_key
            )
        )
        event = existing.scalar_one_or_none()
        if event is not None:
            return event, False

    event = EducationalEvent(
        school_id=payload.school_id,
        student_identity_id=payload.student_identity_id,
        event_kind=payload.event_kind.value
        if isinstance(payload.event_kind, EventKind)
        else payload.event_kind,
        occurred_at=occurred_at,
        device_id=payload.device_id,
        source=payload.source,
        idempotency_key=payload.idempotency_key,
        parent_event_id=payload.parent_event_id,
        payload=payload.payload,
    )
    session.add(event)

    try:
        await session.flush()
    except IntegrityError as exc:
        # Race on the unique idempotency key: another request won. Re-read.
        await session.rollback()
        if not payload.idempotency_key:
            raise
        existing = await session.execute(
            select(EducationalEvent).where(
                EducationalEvent.idempotency_key == payload.idempotency_key
            )
        )
        event = existing.scalar_one_or_none()
        if event is None:
            raise ConflictError("Duplicate event data rejected") from exc
        return event, False

    return event, True


async def get_event(session: AsyncSession, event_id: uuid.UUID) -> EducationalEvent:
    event = await session.get(EducationalEvent, event_id)
    if event is None:
        raise NotFoundError("Event", str(event_id))
    return event


async def list_events(
    session: AsyncSession,
    *,
    school_id: uuid.UUID | None,
    student_identity_id: uuid.UUID | None,
    kind: EventKind | None,
    since_seq: int | None,
    limit: int,
) -> tuple[list[EducationalEvent], int]:
    query = select(EducationalEvent)
    count_query = select(func.count()).select_from(EducationalEvent)
    if school_id is not None:
        query = query.where(EducationalEvent.school_id == school_id)
        count_query = count_query.where(EducationalEvent.school_id == school_id)
    if student_identity_id is not None:
        query = query.where(EducationalEvent.student_identity_id == student_identity_id)
        count_query = count_query.where(
            EducationalEvent.student_identity_id == student_identity_id
        )
    if kind is not None:
        query = query.where(EducationalEvent.event_kind == kind.value)
        count_query = count_query.where(EducationalEvent.event_kind == kind.value)
    if since_seq is not None:
        query = query.where(EducationalEvent.seq > since_seq)
        count_query = count_query.where(EducationalEvent.seq > since_seq)

    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(EducationalEvent.seq.asc()).limit(limit)
    )
    return list(result.scalars().all()), total


async def latest_seq(session: AsyncSession) -> int:
    value = await session.scalar(select(func.max(EducationalEvent.seq)))
    return value or 0