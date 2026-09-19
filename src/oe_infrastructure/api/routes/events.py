"""Educational event routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.enums import EventKind
from oe_infrastructure.schemas.schemas import (
    EducationalEventCreate,
    EducationalEventResponse,
    PaginatedEvent,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.events import list_events, record_event

router = APIRouter()


@router.post(
    "",
    response_model=EducationalEventResponse,
    status_code=201,
    summary="Record an educational event (idempotent)",
    dependencies=[Depends(require_role_at_least(Role.OPERATOR)), Depends(rate_limit(120))],
)
async def create_event(
    body: EducationalEventCreate,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> EducationalEventResponse:
    event, created = await record_event(session, body)
    await audit(
        session,
        action="create" if created else "replay",
        resource_type="event",
        resource_id=str(event.id),
        actor_type="user",
        actor_id=str(actor.id),
        school_id=event.school_id,
        data={"kind": event.event_kind, "created": created},
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return EducationalEventResponse.model_validate(event)


@router.get(
    "",
    response_model=PaginatedEvent,
    summary="List educational events",
    dependencies=[Depends(rate_limit(120))],
)
async def list_events_route(
    session: SessionDep,
    school_id: uuid.UUID | None = None,
    student_identity_id: uuid.UUID | None = None,
    event_kind: EventKind | None = None,
    since_seq: int | None = None,
    limit: int = 100,
) -> PaginatedEvent:
    limit = min(max(limit, 1), 1000)
    events, total = await list_events(
        session,
        school_id=school_id,
        student_identity_id=student_identity_id,
        kind=event_kind,
        since_seq=since_seq,
        limit=limit,
    )
    return PaginatedEvent(
        items=[EducationalEventResponse.model_validate(e) for e in events],
        total=total,
        page=1,
        size=limit,
        has_more=len(events) == limit,
    )
