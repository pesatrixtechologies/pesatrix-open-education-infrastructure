"""Authentication and authorization (JWT + role-based access control).

Roles (least-privilege):

- ``platform_admin``  â€” full access across all organizations.
- ``org_admin``       â€” full access within their organization.
- ``school_admin``    â€” full access within their school.
- ``operator``        â€” record events/attendance within scope, read core data.
- ``verifier``        â€” verify credentials only.
- ``developer``       â€” read-only access for integration.

Access scoping is enforced in dependencies (``core.deps``).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum

import bcrypt
import jwt

from oe_infrastructure.config import get_settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class Role(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    SCHOOL_ADMIN = "school_admin"
    OPERATOR = "operator"
    VERIFIER = "verifier"
    DEVELOPER = "developer"


# Role hierarchy used for coarse-grained permission checks.
HIERARCHY: dict[Role, int] = {
    Role.DEVELOPER: 0,
    Role.VERIFIER: 1,
    Role.OPERATOR: 3,
    Role.SCHOOL_ADMIN: 4,
    Role.ORG_ADMIN: 5,
    Role.PLATFORM_ADMIN: 9,
}


def role_at_least(user_role: Role | str, required: Role) -> bool:
    user_role = Role(user_role) if not isinstance(user_role, Role) else user_role
    return HIERARCHY[user_role] >= HIERARCHY[required]


_BCRYPT_MAX_BYTES = 72


def _password_bytes(password: str) -> bytes:
    """Encode and truncate to bcrypt's 72-byte limit (UTF-8 safe)."""
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    role: Role
    jti: str
    token_type: str
    exp: int
    iat: int
    organization_id: str | None = None
    school_id: str | None = None
    username: str | None = None


def create_access_token(
    *,
    user_id: uuid.UUID | str,
    role: Role | str,
    organization_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    username: str | None = None,
) -> str:
    return _create_token(
        token_type=TOKEN_TYPE_ACCESS,
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        school_id=school_id,
        username=username,
    )


def create_refresh_token(
    *,
    user_id: uuid.UUID | str,
    role: Role | str,
    organization_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    username: str | None = None,
) -> str:
    return _create_token(
        token_type=TOKEN_TYPE_REFRESH,
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        school_id=school_id,
        username=username,
    )


def _create_token(
    *,
    token_type: str,
    user_id: uuid.UUID | str,
    role: Role | str,
    organization_id: uuid.UUID | None,
    school_id: uuid.UUID | None,
    username: str | None,
) -> str:
    settings = get_settings()
    role = Role(role) if not isinstance(role, Role) else role
    now = int(time.time())
    if token_type == TOKEN_TYPE_REFRESH:
        lifetime = settings.jwt_refresh_expires_days * 86400
    else:
        lifetime = settings.jwt_expires_minutes * 60

    payload = {
        "sub": str(user_id),
        "role": role.value,
        "token_type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + lifetime,
    }
    if organization_id is not None:
        payload["organization_id"] = str(organization_id)
    if school_id is not None:
        payload["school_id"] = str(school_id)
    if username is not None:
        payload["username"] = username
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str, expected_type: str = TOKEN_TYPE_ACCESS) -> TokenClaims:
    """Decode and validate a JWT. Raises ``jwt.PyJWTError`` on failure."""
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    token_type = payload.get("token_type")
    if token_type != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    role = payload.get("role")
    if role not in {item.value for item in Role}:
        raise jwt.InvalidTokenError("Invalid role in token")
    return TokenClaims(
        sub=payload["sub"],
        role=Role(role),
        jti=payload["jti"],
        token_type=token_type,
        exp=payload["exp"],
        iat=payload["iat"],
        organization_id=payload.get("organization_id"),
        school_id=payload.get("school_id"),
        username=payload.get("username"),
    )
