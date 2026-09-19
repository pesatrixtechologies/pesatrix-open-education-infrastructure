"""API routers."""

from __future__ import annotations

from fastapi import APIRouter

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

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(identities.router, prefix="/identities", tags=["identities"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])