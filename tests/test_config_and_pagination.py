"""Unit tests for config validation and pagination helpers."""

from __future__ import annotations

import pytest

from oe_infrastructure.config import Settings
from oe_infrastructure.schemas import paginate

DEFAULT_SECRET = (
    "dev-only-insecure-secret-key-change-me-please-1234567890-abcdefghijklmnopqrstuvwxyz"
)


def test_cors_origins_are_parsed_and_trimmed() -> None:
    settings = Settings(cors_origins="https://a.example, https://b.example ,")
    assert settings.cors_origin_list() == ["https://a.example", "https://b.example"]


def test_empty_cors_origins_yields_empty_list() -> None:
    assert Settings(cors_origins="").cors_origin_list() == []


def test_is_production_flag() -> None:
    assert Settings(env="production").is_production is True
    assert Settings(env="development").is_production is False


def test_production_rejects_default_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OE_SECRET_KEY", raising=False)
    settings = Settings(
        env="production",
        secret_key=DEFAULT_SECRET,
        bootstrap_admin_password="strong-password",
    )
    with pytest.raises(RuntimeError, match="OE_SECRET_KEY"):
        settings.validate_for_production()


def test_production_rejects_default_admin_password() -> None:
    settings = Settings(
        env="production",
        secret_key="a-very-strong-production-secret-value",
        bootstrap_admin_password="admin",
    )
    with pytest.raises(RuntimeError, match="OE_BOOTSTRAP_ADMIN_PASSWORD"):
        settings.validate_for_production()


def test_production_accepts_safe_settings() -> None:
    settings = Settings(
        env="production",
        secret_key="a-very-strong-production-secret-value",
        bootstrap_admin_password="not-the-default",
    )
    settings.validate_for_production()


def test_paginate_computes_has_more() -> None:
    page = paginate([1, 2, 3], total=10, page=1, size=3)
    assert page.has_more is True
    assert page.total == 10
    assert page.items == [1, 2, 3]


def test_paginate_last_page_has_no_more() -> None:
    page = paginate([9], total=10, page=4, size=3)
    assert page.has_more is False
