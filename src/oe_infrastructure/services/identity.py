"""Student identity service (privacy-conscious references only)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import ConflictError, NotFoundError
from oe_infrastructure.modules.identity import StudentIdentity
from oe_infrastructure.schemas.schemas import IdentityCreate, IdentityUpdate


async def create_identity(
    session: AsyncSession,
    payload: IdentityCreate,
) -> StudentIdentity:
    existing = await session.execute(
        select(StudentIdentity.id).where(
            StudentIdentity.school_id == payload.school_id,
            StudentIdentity.code == payload.code,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            f"Identity code '{payload.code}' already exists in this school",
            code="code_exists",
        )
    identity = StudentIdentity(
        school_id=payload.school_id,
        code=payload.code,
        external_reference=payload.external_reference,
        status=payload.status.value,
    )
    session.add(identity)
    return identity


async def get_identity(session: AsyncSession, identity_id: uuid.UUID) -> StudentIdentity:
    identity = await session.get(StudentIdentity, identity_id)
    if identity is None:
        raise NotFoundError("Identity", str(identity_id))
    return identity


async def list_identities(
    session: AsyncSession,
    school_id: uuid.UUID | None,
    page: int,
    size: int,
) -> tuple[list[StudentIdentity], int]:
    query = select(StudentIdentity)
    count_query = select(func.count()).select_from(StudentIdentity)
    if school_id is not None:
        query = query.where(StudentIdentity.school_id == school_id)
        count_query = count_query.where(StudentIdentity.school_id == school_id)
    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(StudentIdentity.code.asc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total


async def update_identity(
    session: AsyncSession,
    identity_id: uuid.UUID,
    payload: IdentityUpdate,
) -> StudentIdentity:
    identity = await get_identity(session, identity_id)
    if payload.status is not None:
        identity.status = payload.status.value
    if payload.external_reference is not None:
        identity.external_reference = payload.external_reference
    return identity
