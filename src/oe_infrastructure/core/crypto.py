"""Cryptographic primitives.

All cryptography in this project uses audited, established primitives:

- HMAC-SHA256 for credential signatures (no custom crypto).
- JWT (PyJWT) for authentication tokens.
- bcrypt (passlib) for password hashing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

from sqlalchemy import TypeDecorator, String


def hmac_sha256_hex(key: bytes, message: bytes) -> str:
    """Return an HMAC-SHA256 signature as lowercase hex."""
    digest = hmac.new(key, message, hashlib.sha256).digest()
    return digest.hex()


def constant_time_equals(a: str | bytes, b: str | bytes) -> bool:
    """Compare two values in constant time."""
    return hmac.compare_digest(a, b)


def canonicalize(payload: dict[str, Any]) -> bytes:
    """Serialize a payload to a canonical byte string for signing.

    Keys are sorted; values are encoded deterministically. This makes the
    signature reproducible across clients and languages.
    """

    def _encode(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(_encode(item) for item in value) + "]"
        if isinstance(value, dict):
            parts = ",".join(f"{k}={_encode(v)}" for k, v in sorted(value.items()))
            return "{" + parts + "}"
        if value is None:
            return ""
        raise TypeError(f"Unsupported type for canonicalization: {type(value)!r}")

    ordered = sorted(payload.items(), key=lambda item: item[0])
    body = "&".join(f"{k}={_encode(v)}" for k, v in ordered)
    return body.encode("utf-8")


class HMACBuilder:
    """Create and verify HMAC signatures over canonicalized payloads."""

    def __init__(self, secret: str) -> None:
        self._key = secret.encode("utf-8")

    def sign(self, payload: dict[str, Any]) -> str:
        return hmac_sha256_hex(self._key, canonicalize(payload))

    def verify(self, payload: dict[str, Any], signature: str) -> bool:
        expected = hmac_sha256_hex(self._key, canonicalize(payload))
        return constant_time_equals(expected, signature)


class EncryptedString(TypeDecorator[str]):
    """Placeholder guard column type.

    NOTE: This package intentionally does not store personal data. Where an
    opaque token must be persisted (e.g. external references), it is stored
    as plain VARCHAR and MUST never contain PII. Use this type only as a
    marker that the value is an opaque reference, never a secret.
    """

    impl = String(255)
    cache_ok = True


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)