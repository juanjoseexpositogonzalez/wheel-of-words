"""Naming guard — hook H1, AC-002-10 (T1B20), backend leg.

This capability groups by *normalized form*. It does not lemmatize, and it must
not imply that it does. A display form is the most frequent inflected spelling in
its group; calling it a lemma would tell the user that `corro`, `corres` and
`corría` had been merged into one dictionary headword when they are in fact three
separate rows (Art. V.1, REQ-002-007).

The repo-wide half is an ABSENCE assertion: it passes on the first run over
correct code, which proves nothing at all. It is trusted only after being seen
failing — rename `normalized_form` to `lemma_form` in `dtos/imports.py`, confirm
the `AssertionError` names the file and the matched token, revert. The
non-vacuity test below closes the other half of the same problem, because a file
walk that resolved to zero files would make every assertion here trivially true.

Cut 1c extends this module with the frontend leg over `apps/web/src/`.

REQ-002-007 / AC-002-10.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.main import create_app

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_FORBIDDEN_PATTERN = "lemma|lemas|lexeme|lexema"
_FORBIDDEN = re.compile(_FORBIDDEN_PATTERN, re.IGNORECASE)
_SCANNED_SUFFIXES = frozenset({".py", ".json"})

# Files that make the scan meaningful. If the walk ever stops reaching these,
# the guard has silently stopped guarding anything.
_EXPECTED_FILES = frozenset(
    {
        "api/routes/imports.py",
        "api/dtos/imports.py",
        "api/schemas/import.v1.json",
        "application/imports/use_cases.py",
        "domain/models.py",
    }
)

_ROW_KEYS = {"normalized_form", "display_form", "frequency"}


def _scanned_files() -> list[Path]:
    return sorted(
        path
        for path in _PACKAGE_ROOT.rglob("*")
        if path.is_file() and path.suffix in _SCANNED_SUFFIXES
    )


def _relative(path: Path) -> str:
    return path.relative_to(_PACKAGE_ROOT).as_posix()


@pytest.fixture
def imported_body() -> dict[str, Any]:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/imports",
        files={"file": ("sample.txt", "corro corres corr\u00eda corro".encode(), "text/plain")},
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.unit
def test_the_scan_reaches_the_shipped_backend_sources() -> None:
    """Without this, an empty walk would make the guard below vacuously green."""
    scanned = {_relative(path) for path in _scanned_files()}

    assert scanned >= _EXPECTED_FILES


@pytest.mark.unit
def test_no_backend_source_mentions_a_lemma_or_a_lexeme() -> None:
    """AC-002-10: zero matches across the shipped package, sources and schema alike."""
    violations = [
        f"{_relative(path)}:{number} matches {_FORBIDDEN_PATTERN!r} -> {match.group(0)!r}"
        for path in _scanned_files()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        for match in [_FORBIDDEN.search(line)]
        if match is not None
    ]

    assert not violations, "lemma naming leaked into the backend:\n" + "\n".join(violations)


@pytest.mark.unit
def test_each_response_row_uses_the_specified_key_names(
    imported_body: dict[str, Any],
) -> None:
    """AC-002-10: the grouping key is `normalized_form`, the display value `display_form`."""
    assert imported_body["forms"]
    for row in imported_body["forms"]:
        assert set(row) == _ROW_KEYS


@pytest.mark.unit
def test_the_response_envelope_introduces_no_lemma_naming(
    imported_body: dict[str, Any],
) -> None:
    """Every key on the wire, not only the row keys."""
    keys = set(imported_body) | {key for row in imported_body["forms"] for key in row}

    assert not [key for key in keys if _FORBIDDEN.search(key)]


@pytest.mark.unit
def test_inflected_forms_stay_separate_rows(imported_body: dict[str, Any]) -> None:
    """The naming is honest because the behaviour is: nothing is merged (Art. V.1)."""
    assert [row["normalized_form"] for row in imported_body["forms"]] == [
        "corres",
        "corr\u00eda",
        "corro",
    ]
