"""Synchronization routes (offline devices)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from oe_infrastructure.core.deps import SessionDep, UserDep, require_role_at_least
from oe_infrastructure.core.rate_limit import rate_limit
from oe_infrastructure.core.security import Role
from oe_infrastructure.schemas.schemas import (
    DeviceCreate,
    DeviceResponse,
    EducationalEventResponse,
    SyncDownloadRequest,
    SyncDownloadResponse,
    SyncUploadRequest,
    SyncUploadResponse,
)
from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.sync import (
    download_events,
    register_device,
    upload_events,
)

router = APIRouter()


@router.post(
    "/devices",
    response_model=DeviceResponse,
    summary="Register a device for offline sync",
    dependencies=[Depends(require_role_at_least(Role.SCHOOL_ADMIN)), Depends(rate_limit(30))],
)
async def register(
    body: DeviceCreate,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> DeviceResponse:
    device = await register_device(session, body)
    await audit(
        session,
        action="create",
        resource_type="device",
        resource_id=str(device.id),
        actor_type="user",
        actor_id=str(actor.id),
        school_id=body.school_id,
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return DeviceResponse.model_validate(device)


@router.post(
    "/upload",
    response_model=SyncUploadResponse,
    summary="Upload an offline event batch",
    dependencies=[Depends(require_role_at_least(Role.OPERATOR)), Depends(rate_limit(120))],
)
async def upload(
    body: SyncUploadRequest,
    request: Request,
    session: SessionDep,
    actor: UserDep,
) -> SyncUploadResponse:
    result = await upload_events(
        session,
        device_id=body.device_id,
        batch_seq=body.batch_seq,
        records=body.records,
        received=request.client.host if request.client else None,
    )
    await audit(
        session,
        action="upload",
        resource_type="sync_batch",
        resource_id=str(result["batch_id"]),
        actor_type="device",
        actor_id=str(body.device_id),
        data={
            "accepted": result["accepted"],
            "duplicates": result["duplicates"],
            "errors": result["errors"],
        },
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return SyncUploadResponse(
        accepted=result["accepted"],
        duplicates=result["duplicates"],
        errors=result["errors"],
        watermark_after=result["watermark_after"],
        batch_id=result["batch_id"],
        failed=result["failed"],
    )


@router.post(
    "/download",
    response_model=SyncDownloadResponse,
    summary="Download events since a watermark",
    dependencies=[Depends(require_role_at_least(Role.OPERATOR)), Depends(rate_limit(120))],
)
async def download(
    body: SyncDownloadRequest,
    request: Request,
    session: SessionDep,
) -> SyncDownloadResponse:
    events, more = await download_events(
        session,
        device_id=body.device_id,
        since_seq=body.since_seq,
        limit=body.limit,
        received=request.client.host if request.client else None,
    )
    await audit(
        session,
        action="download",
        resource_type="sync_batch",
        actor_type="device",
        actor_id=str(body.device_id),
        data={"since_seq": body.since_seq, "records": len(events)},
        client_ip=request.client.host if request.client else None,
    )
    await session.commit()
    return SyncDownloadResponse(
        device_id=body.device_id,
        since_seq=body.since_seq,
        watermark_after=events[-1].seq if events else body.since_seq,
        records=[EducationalEventResponse.model_validate(e) for e in events],
        more=more,
    )
