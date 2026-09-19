"""Unit tests for password hashing and JWT tokens."""

from __future__ import annotations

import time
import uuid

import pytest

from oe_infrastructure.core.security import (
    Role,
    TokenClaims,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    role_at_least,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_password_over_72_bytes_is_truncated_consistently() -> None:
    long_password = "a" * 100
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed) is True


def test_verify_password_with_malformed_hash_returns_false() -> None:
    assert verify_password("x", "not-a-bcrypt-hash") is False


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    token = create_access_token(
        user_id=user_id,
        role=Role.OPERATOR,
        organization_id=org_id,
        username="alice",
    )
    claims = decode_token(token, expected_type="access")
    assert isinstance(claims, TokenClaims)
    assert claims.sub == str(user_id)
    assert claims.role == Role.OPERATOR.value
    assert claims.organization_id == str(org_id)
    assert claims.username == "alice"
    assert claims.token_type == "access"


def test_access_token_accepts_string_role() -> None:
    token = create_access_token(user_id=uuid.uuid4(), role="school_admin")
    claims = decode_token(token)
    assert claims.role == Role.SCHOOL_ADMIN.value


def test_refresh_token_type_enforced() -> None:
    token = create_refresh_token(user_id=uuid.uuid4(), role=Role.OPERATOR)
    assert decode_token(token, expected_type="refresh").token_type == "refresh"
    with pytest.raises(Exception):  # noqa: B017 — PyJWTError
        decode_token(token, expected_type="access")


def test_decode_rejects_tampered_token() -> None:
    token = create_access_token(user_id=uuid.uuid4(), role=Role.OPERATOR)
    with pytest.raises(Exception):  # noqa: B017
        decode_token(token + "x")


def test_role_hierarchy() -> None:
    assert role_at_least(Role.PLATFORM_ADMIN, Role.OPERATOR) is True
    assert role_at_least(Role.OPERATOR, Role.OPERATOR) is True
    assert role_at_least(Role.VERIFIER, Role.OPERATOR) is False
    assert role_at_least(Role.PLATFORM_ADMIN, Role.DEVELOPER) is True


def test_role_at_least_accepts_string() -> None:
    assert role_at_least("platform_admin", Role.OPERATOR) is True
    assert role_at_least("verifier", Role.OPERATOR) is False


def test_token_expiry_is_in_the_future() -> None:
    token = create_access_token(user_id=uuid.uuid4(), role=Role.OPERATOR)
    claims = decode_token(token)
    assert claims.exp > int(time.time())
    assert claims.iat <= claims.exp
