"""API routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from oe_infrastructure.api.routes import (
    attendance,
    audit,
    auth,
    credentials,
    events,
    health,
    identities,
    organizations,
    sync,
    users,
)
from oe_infrastructure.core.deps import current_user

# Every route except the public ones (health, auth token/refresh) requires a
# valid bearer token. Route-level ``require_role_at_least`` adds the finer RBAC
# gate on top; this is the authentication floor (defense in depth).
_authed = [Depends(current_user)]

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"], dependencies=_authed)
api_router.include_router(
    organizations.router, prefix="/organizations", tags=["organizations"], dependencies=_authed
)
api_router.include_router(
    identities.router, prefix="/identities", tags=["identities"], dependencies=_authed
)
api_router.include_router(
    credentials.router, prefix="/credentials", tags=["credentials"], dependencies=_authed
)
api_router.include_router(events.router, prefix="/events", tags=["events"], dependencies=_authed)
api_router.include_router(
    attendance.router, prefix="/attendance", tags=["attendance"], dependencies=_authed
)
api_router.include_router(sync.router, prefix="/sync", tags=["sync"], dependencies=_authed)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"], dependencies=_authed)
