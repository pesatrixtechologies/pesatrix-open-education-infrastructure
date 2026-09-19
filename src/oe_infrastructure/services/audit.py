"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.modules.audit import AuditLog


async def audit(
    session: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    actor_type: str = "system",
    actor_id: str | None = None,
    organization_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    client_ip: str | None = None,
    data: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        actor_type=actor_type,
        actor_id=actor_id,
        organization_id=organization_id,
        school_id=school_id,
        client_ip=client_ip,
        data=data or {},
    )
    session.add(entry)
    return entry