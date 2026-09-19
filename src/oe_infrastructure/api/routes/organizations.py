"""Organization and school routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.schemas.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    PaginatedOrganization,
    PaginatedSchool,
    SchoolCreate,
    SchoolResponse,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.organizations import (
    create_organization,
    create_school,
    get_organization,
    get_school,
    list_organizations,
    list_schools,
    update_organization,
)

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    summary="Create an organization",
    dependencies=[Depends(rate_limit(60))],
)
async def create_org(
    body: OrganizationCreate,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> OrganizationResponse:
    org = await create_organization(session, body)
    await audit(
        session,
        action="create",
        resource_type="organization",
        resource_id=str(org.id),
        actor_type="user",
        actor_id=str(actor.id),
        organization_id=org.id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return OrganizationResponse.model_validate(org)


@router.get(
    "",
    response_model=PaginatedOrganization,
    summary="List organizations",
    dependencies=[Depends(rate_limit(120))],
)
async def list_orgs(
    session: SessionDep,
    page: int = 1,
    size: int = 20,
) -> PaginatedOrganization:
    orgs, total = await list_organizations(session, page, size)
    return PaginatedOrganization(
        items=[OrganizationResponse.model_validate(o) for o in orgs],
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get an organization",
    dependencies=[Depends(rate_limit(120))],
)
async def get_org(
    organization_id: uuid.UUID,
    session: SessionDep,
) -> OrganizationResponse:
    org = await get_organization(session, organization_id)
    return OrganizationResponse.model_validate(org)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update an organization (admin)",
    dependencies=[Depends(require_role_at_least(Role.ORG_ADMIN)), Depends(rate_limit(60))],
)
async def update_org(
    organization_id: uuid.UUID,
    body: OrganizationUpdate,
    request: Request,
    session: SessionDep,
) -> OrganizationResponse:
    org = await update_organization(session, organization_id, body)
    await audit(
        session,
        action="update",
        resource_type="organization",
        resource_id=str(org.id),
        actor_type="user",
        organization_id=org.id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return OrganizationResponse.model_validate(org)


@router.post(
    "/{organization_id}/schools",
    response_model=SchoolResponse,
    summary="Create a school under an organization",
    dependencies=[Depends(require_role_at_least(Role.ORG_ADMIN)), Depends(rate_limit(60))],
)
async def create_school_route(
    organization_id: uuid.UUID,
    body: SchoolCreate,
    request: Request,
    session: SessionDep,
) -> SchoolResponse:
    if body.organization_id != organization_id:
        from oe_infrastructure.core.errors import ValidationFailure

        raise ValidationFailure("Mismatched school organization", code="scope_mismatch")
    school = await create_school(session, body)
    await audit(
        session,
        action="create",
        resource_type="school",
        resource_id=str(school.id),
        actor_type="user",
        organization_id=organization_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return SchoolResponse.model_validate(school)


@router.get(
    "/{organization_id}/schools",
    response_model=PaginatedSchool,
    summary="List schools in an organization",
    dependencies=[Depends(rate_limit(120))],
)
async def list_schools_route(
    organization_id: uuid.UUID,
    session: SessionDep,
    page: int = 1,
    size: int = 20,
) -> PaginatedSchool:
    schools, total = await list_schools(session, organization_id, page, size)
    return PaginatedSchool(
        items=[SchoolResponse.model_validate(s) for s in schools],
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )


@router.get(
    "/schools/{school_id}",
    response_model=SchoolResponse,
    summary="Get a school",
    dependencies=[Depends(rate_limit(120))],
)
async def get_school_route(
    school_id: uuid.UUID,
    session: SessionDep,
) -> SchoolResponse:
    school = await get_school(session, school_id)
    return SchoolResponse.model_validate(school)
