"""Package version reader using importlib.metadata.

Reads the installed package version from the build metadata, with a graceful
fallback when the package is not installed (e.g., in bare source checkouts
or test environments that run from source without installing).

REQ-PFB-CONTRACT-01 (version field must match package metadata), design §6.4.
NEW-APPLY-DECISION-1: fallback value is "0.0.0" (not "unknown") to satisfy
the semver pattern required by health.v1.json schema.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as metadata_version

__all__ = ["get_package_version"]

_PACKAGE_NAME = "wheel-vocabulary"
_FALLBACK_VERSION = "0.0.0"


def get_package_version() -> str:
    """Return the installed version of wheel-vocabulary.

    Falls back to ``"0.0.0"`` when the package is not installed or metadata
    is unavailable (e.g., during local development from source without ``pip
    install -e .``).
    """
    try:
        return metadata_version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION
