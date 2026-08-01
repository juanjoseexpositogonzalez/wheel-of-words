"""SQLAlchemy declarative base for persistence mappings.

REQ-001-006, REQ-PFB-CONTRACT-002, design §6.5, TB204.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base"]


class Base(DeclarativeBase):
    """Declarative base with intentionally empty metadata for SPEC-001."""
