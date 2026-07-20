"""Shared test fixtures for the wheel_vocabulary test suite.

Fixture placement policy:
- Fixtures scoped to a single test module belong in that module.
- Fixtures shared across two or more modules in the same sub-directory belong
  in a conftest.py within that sub-directory.
- Fixtures shared across sub-directories (smoke/, unit/, api/, integration/)
  belong here at the tests/ root.

Slice A: this file is infrastructure scaffolding only.
Slice B adds: FrozenClock, TestClient factory, tmp_db_url, alembic_config.
"""
