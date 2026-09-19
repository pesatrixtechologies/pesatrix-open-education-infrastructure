"""Unit tests for the pure cryptographic primitives."""

from __future__ import annotations

from oe_infrastructure.core.crypto import (
    HMACBuilder,
    b64url_decode,
    b64url_encode,
    canonicalize,
    constant_time_equals,
    hmac_sha256_hex,
)


def test_canonicalize_sorts_keys_deterministically() -> None:
    a = canonicalize({"b": 2, "a": 1})
    b = canonicalize({"a": 1, "b": 2})
    assert a == b
    assert a == b"a=1&b=2"


def test_canonicalize_encodes_types() -> None:
    assert canonicalize({"t": True, "f": False, "n": None}) == b"f=false&n=&t=true"
    assert canonicalize({"x": [1, 2, 3]}) == b"x=[1,2,3]"
    assert canonicalize({"x": {"k": "v"}}) == b"x={k=v}"


def test_hmac_sign_and_verify_roundtrip() -> None:
    builder = HMACBuilder("secret")
    payload = {"v": 1, "id": "abc", "iat": 1700000000}
    signature = builder.sign(payload)
    assert builder.verify(payload, signature) is True
    assert builder.verify({**payload, "id": "tampered"}, signature) is False


def test_hmac_is_stable_for_equivalent_payloads() -> None:
    builder = HMACBuilder("secret")
    assert builder.sign({"a": 1, "b": 2}) == builder.sign({"b": 2, "a": 1})


def test_hmac_sha256_hex_known_vector() -> None:
    assert (
        hmac_sha256_hex(b"key", b"The quick brown fox jumps over the lazy dog")
        == "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8"
    )


def test_constant_time_equals() -> None:
    assert constant_time_equals("abc", "abc") is True
    assert constant_time_equals("abc", "abd") is False


def test_b64url_roundtrip() -> None:
    raw = b"\x00\xff\x10binary data?"
    assert b64url_decode(b64url_encode(raw)) == raw
