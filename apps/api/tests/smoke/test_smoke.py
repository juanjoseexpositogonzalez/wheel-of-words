"""Smoke test — first RED test of the cycle.

Purpose: prove the test runner executes. Once pytest is installed and this
file exists, the test transitions from RED (file missing, collection error)
to GREEN (trivial assertion passes).

TDD transition boundary per spec REQ-PFB-BOOT-02: from this task forward,
[BOOTSTRAP] MUST NOT be used. Every new behavior begins with a failing test.
"""

import pytest


@pytest.mark.smoke
def test_pytest_runs() -> None:
    """Assert the test runner executes.

    RED  — before this file exists, pytest reports a collection error.
    GREEN — once this file is committed, the assertion passes immediately.
    """
    assert True
