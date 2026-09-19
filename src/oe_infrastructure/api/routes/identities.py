"""Student identity routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.schemas.schemas import (
    IdentityCreate,
    IdentityResponse,
    IdentityUpdate,
    PaginatedIdentity,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.identity import (
    create_identity,
    get_identity,
    list_identities,
    update_identity,
)

router = APIRouter()


@router.post(
    "",
    response_model=IdentityResponse,
    summary="Create a student identity reference",
    dependencies=[Depends(require_role_at_least(Role.SCHOOL_ADMIN)), Depends(rate_limit(60))],
)
async def create(
    body: IdentityCreate,
    request: Request,
    session: SessionDep,
) -> IdentityResponse:
    identity = await create_identity(session, body)
    await audit(
        session,
        action="create",
        resource_type="identity",
        resource_id=str(identity.id),
        actor_type="user",
        school_id=body.school_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return IdentityResponse.model_validate(identity)


@router.get(
    "",
    response_model=PaginatedIdentity,
    summary="List student identity references",
    dependencies=[Depends(rate_limit(120))],
)
async def list_identities_route(
    session: SessionDep,
    school_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedIdentity:
    identities, total = await list_identities(session, school_id, page, size)
    return PaginatedIdentity(
        items=[IdentityResponse.model_validate(i) for i in identities],
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )


@router.get(
    "/{identity_id}",
    response_model=IdentityResponse,
    summary="Get a student identity reference",
    dependencies=[Depends(rate_limit(120))],
)
async def get(
    identity_id: uuid.UUID,
    session: SessionDep,
) -> IdentityResponse:
    identity = await get_identity(session, identity_id)
    return IdentityResponse.model_validate(identity)


@router.patch(
    "/{identity_id}",
    response_model=IdentityResponse,
    summary="Update a student identity reference (admin)",
    dependencies=[Depends(require_role_at_least(Role.SCHOOL_ADMIN)), Depends(rate_limit(60))],
)
async def update(
    identity_id: uuid.UUID,
    body: IdentityUpdate,
    request: Request,
    session: SessionDep,
) -> IdentityResponse:
    identity = await update_identity(session, identity_id, body)
    await audit(
        session,
        action="update",
        resource_type="identity",
        resource_id=str(identity.id),
        actor_type="user",
        school_id=identity.school_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return IdentityResponse.model_validate(identity)
