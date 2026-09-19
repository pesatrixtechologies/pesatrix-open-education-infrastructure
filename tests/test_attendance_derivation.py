"""Unit tests for attendance derivation rules (no database required)."""

from __future__ import annotations

from datetime import UTC, datetime, time

import pytest

from oe_infrastructure.core.errors import ValidationFailure
from oe_infrastructure.modules.enums import AttendanceStatus
from oe_infrastructure.services.attendance import derive_status


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 1, 15, hour, minute, tzinfo=UTC)


def test_no_check_ins_is_unrecorded() -> None:
    assert derive_status([]) == AttendanceStatus.UNRECORDED


def test_early_check_in_is_present() -> None:
    assert derive_status([_at(8, 0)]) == AttendanceStatus.PRESENT


def test_check_in_at_threshold_is_late() -> None:
    assert derive_status([_at(9, 30)]) == AttendanceStatus.LATE


def test_latest_check_in_decides_status() -> None:
    # One early, one late -> late wins.
    assert derive_status([_at(8, 0), _at(9, 45)]) == AttendanceStatus.LATE


def test_naive_datetimes_are_treated_as_utc() -> None:
    naive = datetime(2026, 1, 15, 8, 0)
    assert derive_status([naive]) == AttendanceStatus.PRESENT


def test_custom_late_threshold() -> None:
    assert derive_status([_at(10, 0)], late_threshold=time.fromisoformat("11:00")) == (
        AttendanceStatus.PRESENT
    )


def test_override_wins_over_check_ins() -> None:
    assert derive_status([_at(8, 0)], override="excused") == AttendanceStatus.EXCUSED
    assert derive_status([_at(9, 45)], override="present") == AttendanceStatus.PRESENT


def test_invalid_override_raises_validation_failure() -> None:
    with pytest.raises(ValidationFailure):
        derive_status([], override="teleported")
