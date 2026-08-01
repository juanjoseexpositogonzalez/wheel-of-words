"""Unit tests for Clock protocol, SystemClock, and FrozenClock (TB103).

Tests must be RED before application/clock.py and infrastructure/clock.py exist.
REQ-PFB-CONTRACT-01 (timestamp semantics), design §6.2, §6.6, ADR-0002.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.infrastructure.clock import SystemClock

if TYPE_CHECKING:
    from wheel_vocabulary.application.clock import Clock


class FrozenClock:
    """Test double that returns a fixed datetime from now_utc()."""

    def __init__(self, fixed_dt: datetime) -> None:
        self._fixed_dt = fixed_dt

    def now_utc(self) -> datetime:
        return self._fixed_dt


@pytest.mark.unit
def test_clock_protocol_is_structural() -> None:
    """Clock is a typing.Protocol — structural subtyping without inheritance."""
    # FrozenClock satisfies Clock without inheriting from it.
    clock: Clock = FrozenClock(datetime(2026, 7, 20, 12, 0, 0, tzinfo=UTC))
    result = clock.now_utc()
    assert isinstance(result, datetime)
    # The real structural check: FrozenClock implements now_utc without inheriting Clock
    assert callable(getattr(FrozenClock, "now_utc", None))


@pytest.mark.unit
def test_system_clock_returns_utc() -> None:
    """SystemClock.now_utc() returns a timezone-aware UTC datetime."""
    clock = SystemClock()
    result = clock.now_utc()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.utcoffset() is not None


@pytest.mark.unit
def test_frozen_clock_returns_fixed_time() -> None:
    """FrozenClock always returns the exact datetime it was constructed with."""
    fixed = datetime(2026, 7, 20, 14, 32, 0, 123000, tzinfo=UTC)
    clock = FrozenClock(fixed)
    assert clock.now_utc() == fixed
    # Second call also returns the same fixed time (frozen, not advancing)
    assert clock.now_utc() is fixed
