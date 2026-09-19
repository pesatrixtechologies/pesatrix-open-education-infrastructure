"""Immutable audit log.

Records who did what, when, in which scope. Used for governance oversight
and incident investigation. Must never contain personal data.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    # Actor
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)  # user|device|system
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(48), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    organization_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    school_id: Mapped[Any | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action!r}>"
