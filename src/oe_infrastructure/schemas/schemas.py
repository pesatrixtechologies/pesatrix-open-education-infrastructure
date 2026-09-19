"""Domain-specific Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oe_infrastructure.modules.enums import (
    AttendanceStatus,
    CredentialStatus,
    CredentialType,
    DeviceStatus,
    EventKind,
    IdentityStatus,
    OrganizationType,
    RecordStatus,
)
from oe_infrastructure.schemas import ORMModel, PaginatedResponse

# --- Organizations -----------------------------------------------------------


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    org_type: OrganizationType = OrganizationType.OTHER
    parent_organization_id: uuid.UUID | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class OrganizationResponse(ORMModel):
    name: str
    code: str
    org_type: OrganizationType
    status: RecordStatus
    parent_organization_id: uuid.UUID | None = None


# --- Schools -----------------------------------------------------------------


class SchoolCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")


class SchoolResponse(ORMModel):
    organization_id: uuid.UUID
    name: str
    code: str
    status: RecordStatus


# --- Identities ----------------------------------------------------------


class IdentityCreate(BaseModel):
    school_id: uuid.UUID
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    external_reference: str | None = None
    status: IdentityStatus = IdentityStatus.ACTIVE


class IdentityUpdate(BaseModel):
    status: IdentityStatus | None = None
    external_reference: str | None = None


class IdentityResponse(ORMModel):
    school_id: uuid.UUID
    code: str
    external_reference: str | None = None
    status: IdentityStatus


# --- Credentials ---------------------------------------------------------


class CredentialCreate(BaseModel):
    student_identity_id: uuid.UUID
    issuer_organization_id: uuid.UUID
    credential_type: CredentialType
    title: str = Field(min_length=1, max_length=200)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class CredentialRevoke(BaseModel):
    reason: str = Field(min_length=1, max_length=200)


class CredentialResponse(ORMModel):
    student_identity_id: uuid.UUID
    credential_type: CredentialType
    title: str
    status: CredentialStatus
    issued_at: datetime
    expires_at: datetime | None = None
    issuer_organization_id: uuid.UUID
    signature: str
    revoked_at: datetime | None = None
    revoke_reason: str | None = None


class CredentialVerifyRequest(BaseModel):
    credential_id: uuid.UUID
    issuer_code: str | None = None


class CredentialVerifyResponse(BaseModel):
    valid: bool
    status: CredentialStatus | None = None
    reason: str | None = None
    student_identity_id: uuid.UUID | None = None
    credential_type: CredentialType | None = None


# --- Events ------------------------------------------------------------------


class EducationalEventCreate(BaseModel):
    school_id: uuid.UUID
    student_identity_id: uuid.UUID | None = None
    event_kind: EventKind
    occurred_at: datetime | None = None
    device_id: uuid.UUID | None = None
    source: str = "api"
    idempotency_key: str | None = Field(default=None, max_length=128, pattern=r"^[\w\-]{8,128}$")
    parent_event_id: uuid.UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EducationalEventResponse(ORMModel):
    seq: int
    school_id: uuid.UUID
    student_identity_id: uuid.UUID | None = None
    event_kind: EventKind
    occurred_at: datetime
    recorded_at: datetime
    device_id: uuid.UUID | None = None
    source: str
    idempotency_key: str | None = None
    parent_event_id: uuid.UUID | None = None
    version: int
    payload: dict[str, Any]


# --- Attendance --------------------------------------------------------------


class AttendanceRollupSchema(BaseModel):
    school_id: uuid.UUID
    date: str


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    student_identity_id: uuid.UUID
    date: date
    status: AttendanceStatus
    source_event_id: uuid.UUID | None = None
    derived_at: datetime


class AttendanceSummaryEntry(BaseModel):
    date: str
    present: int
    late: int
    absent: int
    excused: int
    unrecorded: int
    total: int


class AttendanceSummaryResponse(BaseModel):
    school_id: uuid.UUID
    date: str
    total_students: int
    entries: list[AttendanceSummaryEntry]


# --- Sync --------------------------------------------------------------------


class DeviceCreate(BaseModel):
    school_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    device_type: str = "mobile"


class DeviceResponse(ORMModel):
    school_id: uuid.UUID
    name: str
    device_type: str
    status: DeviceStatus
    last_seen_at: datetime | None = None


class SyncUploadRecord(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=128, pattern=r"^[\w\-]+$")
    school_id: uuid.UUID
    student_identity_id: uuid.UUID | None = None
    event_kind: EventKind
    occurred_at: datetime
    device_id: uuid.UUID | None = None
    source: str = Field(default="offline_device", max_length=24)
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncUploadRequest(BaseModel):
    device_id: uuid.UUID
    batch_seq: int = Field(ge=1)
    records: list[SyncUploadRecord] = Field(min_length=1)


class SyncUploadResponse(BaseModel):
    accepted: int
    duplicates: int
    errors: int = 0
    watermark_after: int
    batch_id: uuid.UUID
    failed: list[dict[str, Any]] = Field(default_factory=list)


class SyncDownloadRequest(BaseModel):
    device_id: uuid.UUID
    since_seq: int = 0
    limit: int = Field(default=200, ge=1, le=1000)


class SyncDownloadResponse(BaseModel):
    device_id: uuid.UUID
    since_seq: int
    watermark_after: int
    records: list[EducationalEventResponse]
    more: bool


# --- Auth --------------------------------------------------------------------


class AuthTokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=120)
    role: str = "operator"
    organization_id: uuid.UUID | None = None
    school_id: uuid.UUID | None = None


class UserResponse(ORMModel):
    username: str
    display_name: str
    role: str
    status: RecordStatus
    organization_id: uuid.UUID | None = None
    school_id: uuid.UUID | None = None
    last_login_at: datetime | None = None


# --- Audit -------------------------------------------------------------------


class AuditLogResponse(ORMModel):
    actor_type: str
    actor_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    organization_id: uuid.UUID | None = None
    school_id: uuid.UUID | None = None
    request_id: str | None = None
    data: dict[str, Any] | None = None


# --- Common ------------------------------------------------------------------


class MessageResponse(BaseModel):
    message: str
    details: dict[str, Any] | None = None


# --- Health ------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    checks: dict[str, Any] = Field(default_factory=dict)


PaginatedOrganization = PaginatedResponse[OrganizationResponse]
PaginatedSchool = PaginatedResponse[SchoolResponse]
PaginatedIdentity = PaginatedResponse[IdentityResponse]
PaginatedCredential = PaginatedResponse[CredentialResponse]
PaginatedEvent = PaginatedResponse[EducationalEventResponse]
PaginatedAudit = PaginatedResponse[AuditLogResponse]
PaginatedUser = PaginatedResponse[UserResponse]
PaginatedDevice = PaginatedResponse[DeviceResponse]
