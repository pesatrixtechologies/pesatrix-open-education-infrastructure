"""Organizations and schools."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from oe_infrastructure.modules.base import (
    Base,
    CodeMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Organization(Base, UUIDPrimaryKeyMixin, CodeMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    parent_organization_id: Mapped[Any | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, name="metadata", nullable=False, default=dict)

    schools = relationship("School", back_populates="organization")
    children = relationship("Organization")

    def __repr__(self) -> str:
        return f"<Organization code={self.code!r}>"


class School(Base, UUIDPrimaryKeyMixin, CodeMixin, TimestampMixin):
    __tablename__ = "schools"

    organization_id: Mapped[Any] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, name="metadata", nullable=False, default=dict)

    organization = relationship("Organization", back_populates="schools")

    def __repr__(self) -> str:
        return f"<School code={self.code!r}>"