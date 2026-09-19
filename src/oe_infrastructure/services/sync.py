"""Offline synchronization service.

Devices register against a school, then:

- **Upload**: devices send a batch of raw events with per-record
  ``idempotency_key``. The server deduplicates, appends events to the
  immutable store, and returns the new watermark plus acknowledgment
  statistics. Retries are safe.
- **Download**: devices request events newer than their last watermark in
  mono-increasing ``seq`` order. They advance their watermark only after
  local persistence succeeds (exactly-once, at-least-once streaming).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oe_infrastructure.core.errors import NotFoundError, ValidationFailure
from oe_infrastructure.modules.enums import BatchStatus, SyncDirection
from oe_infrastructure.modules.events import EducationalEvent
from oe_infrastructure.modules.sync import SyncBatch, SyncDevice
from oe_infrastructure.schemas.schemas import (
    DeviceCreate,
    EducationalEventCreate,
    SyncUploadRecord,
)
from oe_infrastructure.services.events import record_event


async def register_device(
    session: AsyncSession,
    payload: DeviceCreate,
) -> SyncDevice:
    device = SyncDevice(
        school_id=payload.school_id,
        name=payload.name,
        device_type=payload.device_type,
    )
    session.add(device)
    return device


async def get_device(session: AsyncSession, device_id: uuid.UUID) -> SyncDevice:
    device = await session.get(SyncDevice, device_id)
    if device is None:
        raise NotFoundError("Device", str(device_id))
    return device


async def touch_device(session: AsyncSession, device: SyncDevice) -> None:
    device.last_seen_at = datetime.now(timezone.utc)


async def upload_events(
    session: AsyncSession,
    *,
    device_id: uuid.UUID,
    batch_seq: int,
    records: list[SyncUploadRecord],
    received: str | None = None,
) -> dict:
    """Ingest a device upload batch.

    Returns a result dict::

        {
          "accepted": int,
          "duplicates": int,
          "errors": int,
          "failed": [{"idempotency_key": str, "error": str}, ...],
          "watermark_after": int,
          "batch_id": uuid.UUID,
        }
    """
    device = await get_device(session, device_id)
    if device.status != "active":
        raise ValidationFailure(f"Device is {device.status}", code="device_inactive")
    await touch_device(session, device)

    batch = SyncBatch(
        device_id=device_id,
        direction=SyncDirection.UPLOAD.value,
        status=BatchStatus.PROCESSING.value,
        batch_seq=batch_seq,
    )
    session.add(batch)

    accepted = 0
    duplicates = 0
    failed: list[dict] = []

    for record in records:
        event_payload = EducationalEventCreate(
            school_id=record.school_id,
            student_identity_id=record.student_identity_id,
            event_kind=record.event_kind,
            occurred_at=record.occurred_at,
            device_id=device_id,
            source=record.source,
            idempotency_key=record.idempotency_key,
            payload=record.payload,
        )
        try:
            _, created = await record_event(
                session,
                event_payload,
            )
        except Exception as exc:  # noqa: BLE001 — record-level isolation
            session.rollback()
            failed.append(
                {
                    "idempotency_key": record.idempotency_key,
                    "error": str(exc),
                }
            )
            continue
        if created:
            accepted += 1
        else:
            duplicates += 1

    watermark = await _current_watermark(session)
    batch.status = BatchStatus.COMPLETED.value
    batch.event_count = accepted + duplicates
    batch.watermark_after = watermark
    batch.processed_at = datetime.now(timezone.utc)
    await session.flush()
    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "errors": len(failed),
        "failed": failed,
        "watermark_after": watermark,
        "batch_id": batch.id,
    }


async def download_events(
    session: AsyncSession,
    *,
    device_id: uuid.UUID,
    since_seq: int,
    limit: int,
    received: str | None = None,
) -> tuple[list[EducationalEvent], bool]:
    """Download events newer than ``since_seq``.

    Returns ``(events, more)``. Events are ordered ascending by ``seq`` so
    consumers can safely advance watermarks.
    """
    device = await get_device(session, device_id)
    await touch_device(session, device)

    result = await session.execute(
        select(EducationalEvent)
        .where(EducationalEvent.seq > since_seq)
        .order_by(EducationalEvent.seq.asc())
        .limit(limit + 1)
    )
    rows = list(result.scalars().all())
    more = len(rows) > limit
    events = rows[:limit]

    batch = SyncBatch(
        device_id=device_id,
        direction=SyncDirection.DOWNLOAD.value,
        status=BatchStatus.COMPLETED.value,
        batch_seq=0,
        event_count=len(events),
        watermark_after=events[-1].seq if events else since_seq,
        processed_at=datetime.now(timezone.utc),
    )
    session.add(batch)
    return events, more


async def _current_watermark(session: AsyncSession) -> int:
    from sqlalchemy import func

    value = await session.scalar(select(func.max(EducationalEvent.seq)))
    return value or 0