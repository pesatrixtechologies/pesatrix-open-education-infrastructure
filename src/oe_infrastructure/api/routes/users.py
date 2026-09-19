"""User management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select

from oe_infrastructure.core.deps import SessionDep, UserDep
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.auth import User
from oe_infrastructure.schemas.schemas import PaginatedUser, UserCreate, UserResponse
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.auth import create_user

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    summary="Create a user (admin)",
    dependencies=[Depends(rate_limit(60))],
)
async def create(
    body: UserCreate,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> UserResponse:
    try:
        role = Role(body.role)
    except ValueError as err:
        from oe_infrastructure.core.errors import ValidationFailure

        raise ValidationFailure(f"Invalid role '{body.role}'", code="invalid_role") from err
    user = await create_user(
        session,
        username=body.username,
        password=body.password,
        display_name=body.display_name,
        role=role,
        organization_id=body.organization_id,
        school_id=body.school_id,
    )
    await audit(
        session,
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        actor_type="user",
        actor_id=str(actor.id),
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=PaginatedUser,
    summary="List users (admin)",
    dependencies=[Depends(rate_limit(120))],
)
async def list_users(
    session: SessionDep,
    actor: UserDep,
    page: int = 1,
    size: int = 20,
) -> PaginatedUser:
    query = select(User).order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    total = await session.scalar(select(func.count()).select_from(User)) or 0
    result = await session.execute(query)
    users = result.scalars().all()
    items = [UserResponse.model_validate(u) for u in users]
    return PaginatedUser(
        items=items, total=total, page=page, size=size, has_more=(page * size) < total
    )
