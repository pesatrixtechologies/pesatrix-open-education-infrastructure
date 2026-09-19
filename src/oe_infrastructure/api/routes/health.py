"""API route handlers."""

from __future__ import annotations

from fastapi import APIRouter

from oe_infrastructure import __version__
from oe_infrastructure.core.deps import SessionDep
from oe_infrastructure.schemas.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health(
    session: SessionDep,
) -> HealthResponse:
    """Liveness probe. Reports service and database status."""
    db_status = "ok"
    try:
        from sqlalchemy import text

        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "unavailable"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=__version__,
        database=db_status,
    )
