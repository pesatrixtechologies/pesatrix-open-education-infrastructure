"""Offline synchronization: devices and sync batches."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class SyncDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sync_devices"

    school_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    device_type: Mapped[str] = mapped_column(String(40), nullable=False, default="mobile")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSON, name="metadata", nullable=False, default=dict
    )

    def __repr__(self) -> str:
        return f"<SyncDevice name={self.name!r}>"


class SyncBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sync_batches"

    device_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sync_devices.id"), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # upload/download
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    batch_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watermark_after: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    device = relationship("SyncDevice")

    def __repr__(self) -> str:
        return f"<SyncBatch {self.direction} seq={self.batch_seq} status={self.status!r}>"
