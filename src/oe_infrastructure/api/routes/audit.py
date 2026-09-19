"""Audit log routes (admin)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from oe_infrastructure.core.deps import SessionDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.modules.audit import AuditLog
from oe_infrastructure.schemas.schemas import AuditLogResponse, PaginatedAudit

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedAudit,
    summary="List audit log entries (admin)",
    dependencies=[Depends(require_role_at_least(Role.ORG_ADMIN)), Depends(rate_limit(60))],
)
async def list_audit(
    session: SessionDep,
    action: str | None = None,
    resource_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedAudit:
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    total = await session.scalar(count_query) or 0
    result = await session.execute(
        query.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    entries = result.scalars().all()
    return PaginatedAudit(
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )
