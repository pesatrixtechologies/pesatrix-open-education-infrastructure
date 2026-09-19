"""Organization and school services."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import ConflictError, NotFoundError
from oe_infrastructure.modules.organizations import Organization, School
from oe_infrastructure.schemas.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    SchoolCreate,
)


async def create_organization(
    session: AsyncSession,
    payload: OrganizationCreate,
) -> Organization:
    existing = await session.execute(
        select(Organization.code).where(Organization.code == payload.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Organization code '{payload.code}' already exists")
    org = Organization(
        name=payload.name,
        code=payload.code,
        org_type=payload.org_type.value,
        parent_organization_id=payload.parent_organization_id,
    )
    session.add(org)
    return org


async def get_organization(session: AsyncSession, org_id: uuid.UUID) -> Organization:
    org = await session.get(Organization, org_id)
    if org is None:
        raise NotFoundError("Organization", str(org_id))
    return org


async def list_organizations(
    session: AsyncSession,
    page: int,
    size: int,
) -> tuple[list[Organization], int]:
    total = await session.scalar(select(func.count()).select_from(Organization)) or 0
    result = await session.execute(
        select(Organization)
        .order_by(Organization.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all()), total


async def update_organization(
    session: AsyncSession,
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
) -> Organization:
    org = await get_organization(session, org_id)
    if payload.name is not None:
        org.name = payload.name
    return org


async def create_school(session: AsyncSession, payload: SchoolCreate) -> School:
    await get_organization(session, payload.organization_id)
    existing = await session.execute(select(School.code).where(School.code == payload.code))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"School code '{payload.code}' already exists")
    school = School(
        organization_id=payload.organization_id,
        name=payload.name,
        code=payload.code,
    )
    session.add(school)
    return school


async def get_school(session: AsyncSession, school_id: uuid.UUID) -> School:
    school = await session.get(School, school_id)
    if school is None:
        raise NotFoundError("School", str(school_id))
    return school


async def list_schools(
    session: AsyncSession,
    organization_id: uuid.UUID | None,
    page: int,
    size: int,
) -> tuple[list[School], int]:
    query = select(School)
    count_query = select(func.count()).select_from(School)
    if organization_id is not None:
        query = query.where(School.organization_id == organization_id)
        count_query = count_query.where(School.organization_id == organization_id)
    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(School.created_at.asc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total
