"""Services facade."""

from __future__ import annotations

from oe_infrastructure.services.audit import audit
from oe_infrastructure.services.auth import (
    create_user,
    login,
    logout,
    refresh,
)
from oe_infrastructure.services.credentials import (
    issue_credential,
    revoke_credential,
    verify_credential,
)
from oe_infrastructure.services.events import record_event
from oe_infrastructure.services.identity import (
    create_identity,
    get_identity,
    list_identities,
    update_identity,
)
from oe_infrastructure.services.organizations import (
    create_organization,
    create_school,
    get_organization,
    get_school,
    list_organizations,
    list_schools,
)
from oe_infrastructure.services.sync import (
    download_events,
    register_device,
    upload_events,
)

__all__ = [
    "audit",
    "create_user",
    "login",
    "logout",
    "refresh",
    "issue_credential",
    "revoke_credential",
    "verify_credential",
    "record_event",
    "create_identity",
    "get_identity",
    "list_identities",
    "update_identity",
    "create_organization",
    "create_school",
    "get_organization",
    "get_school",
    "list_organizations",
    "list_schools",
    "download_events",
    "register_device",
    "upload_events",
]