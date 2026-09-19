"""SQLAlchemy table enum values in their canonical string form.

Values are stored as short strings, not native enums, so deployments can add
new values without a migration and so device firmware written in other
languages interops without native enum support.
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    SCHOOL_ADMIN = "school_admin"
    OPERATOR = "operator"
    VERIFIER = "verifier"
    DEVELOPER = "developer"


class RoleAtLeast:
    """Strictly increasing role ladder for hierarchy checks."""

    _LADDER = (
        Role.DEVELOPER,
        Role.VERIFIER,
        Role.OPERATOR,
        Role.SCHOOL_ADMIN,
        Role.ORG_ADMIN,
        Role.PLATFORM_ADMIN,
    )

    @classmethod
    def index(cls, role: Role) -> int:
        return cls._LADDER.index(role)

    @classmethod
    def at_least(cls, required: Role) -> tuple[Role, ...]:
        i = cls.index(required)
        return cls._LADDER[i:]


class RecordStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class OrganizationType(str, Enum):
    SCHOOL = "school"
    DISTRICT = "district"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    OTHER = "other"


class EventKind(str, Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    LESSON_STARTED = "lesson_started"
    LESSON_COMPLETED = "lesson_completed"
    ATTENDANCE_OVERRIDE = "attendance_override"
    CREDENTIAL_ISSUED = "credential_issued"
    CREDENTIAL_VERIFIED = "credential_verified"
    SYNC_BATCH = "sync_batch"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"
    UNRECORDED = "unrecorded"


class CredentialType(str, Enum):
    STUDENT_ID_CARD = "student_id_card"
    ENROLMENT_CERTIFICATE = "enrolment_certificate"
    PARTICIPATION = "participation"
    COMPLETION = "completion"
    OTHER = "other"


class CredentialStatus(str, Enum):
    ISSUED = "issued"
    REVOKED = "revoked"
    EXPIRED = "expired"


class DeviceStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class DeviceType(str, Enum):
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    OTHER = "other"


class SyncDirection(str, Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"


class IdentityStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class BatchStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ISSUE = "issue"
    REVOKE = "revoke"
    VERIFY = "verify"
    LOGIN = "login"
    LOGOUT = "logout"
    SYNC_UPLOAD = "sync_upload"
    SYNC_DOWNLOAD = "sync_download"
    BOOTSTRAP = "bootstrap"