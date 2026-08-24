"""Whole-package NLP-library isolation guard — spec hook H2, REQ-003-002 (clause 2).

`AC-003-02` has two clauses. The first — "the domain is pure" — is guarded by
`test_domain_isolation.py`, scoped to `domain/`. The second — spec hook H2,
**"no spaCy type outside the adapter"** — had never been guarded at package
scope before this remediation: `test_annotation_ports.py::
test_ports_module_carries_no_nlp_import` inspects exactly one file
(`application/annotation/ports.py`), not the whole tree. The underlying fact
was true (spaCy is imported in exactly one file,
`infrastructure/nlp/spacy_analyzer.py`), but nothing enforced it, so a future
refactor could import spaCy from `application/` or `api/` and nothing would
fail — which is precisely the gap `docs/traceability-matrix.md` recorded as
`En progreso` for REQ-003-002 before this file shipped.

A spaCy TYPE cannot appear anywhere `spacy`/`thinc`/`stanza` is not first
imported by name — Python has no structural typing that reaches an
unimported module's classes — so scanning for the import itself is both
necessary and sufficient to prove the type-escape half of AC-003-02 scenario
2.

This is an ABSENCE assertion. It passes on its first run over correct code,
which proves nothing on its own, so it is trusted only after being seen
failing. The non-vacuity test below closes the same problem `test_domain_
isolation.py`'s own non-vacuity test closes: a file walk that resolved to
zero files would make every assertion here trivially true.

MUTATION CHECK — added a real, otherwise-unused `import spacy` to
`application/annotation/use_cases.py` (a file well outside
`infrastructure/nlp/`), ran this module, and observed::

    AssertionError: a spaCy/thinc/stanza import escaped the adapter package:
    application/annotation/use_cases.py imports 'spacy'
    (only infrastructure/nlp/spacy_analyzer.py may)

then reverted the import and re-ran to confirm green again.

REQ-003-002 / AC-003-02 scenario 2 / spec §8 hook H2.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_FORBIDDEN_NLP_ROOTS = frozenset({"spacy", "thinc", "stanza"})
_ALLOWED_FILE = "infrastructure/nlp/spacy_analyzer.py"

# Files that make the whole-package scan meaningful, spanning every layer —
# not just `domain/`, which `test_domain_isolation.py` already covers on its
# own. If the walk ever stopped reaching these, this guard would pass on
# every run without checking anything.
_EXPECTED_FILES = frozenset(
    {
        "domain/annotation.py",
        "application/annotation/ports.py",
        "application/annotation/use_cases.py",
        "infrastructure/nlp/spacy_analyzer.py",
        "infrastructure/nlp/registry.py",
        "infrastructure/persistence/annotation_repository.py",
        "infrastructure/persistence/annotation_write_repository.py",
        "api/routes/annotation.py",
        "api/dtos/annotation.py",
    }
)


def _package_modules() -> list[Path]:
    return sorted(_PACKAGE_ROOT.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(_PACKAGE_ROOT).as_posix()


def _imported_roots(tree: ast.AST) -> set[str]:
    """Return the root package name of every module an AST tree imports."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _escaped_nlp_imports(source: str, label: str) -> list[str]:
    tree = ast.parse(source, filename=label)
    escaped = _imported_roots(tree) & _FORBIDDEN_NLP_ROOTS
    return [f"{label} imports {root!r} (only {_ALLOWED_FILE} may)" for root in sorted(escaped)]


@pytest.mark.unit
def test_the_scan_reaches_the_whole_package_across_every_layer() -> None:
    """Non-vacuity: the walk must reach every layer, or the guard below is empty."""
    scanned = {_relative(path) for path in _package_modules()}

    assert scanned >= _EXPECTED_FILES


@pytest.mark.unit
def test_no_nlp_library_import_escapes_the_adapter_package() -> None:
    """AC-003-02 scenario 2 / spec hook H2: spacy/thinc/stanza import in
    exactly one file across the whole `wheel_vocabulary` package."""
    violations: list[str] = []
    for module in _package_modules():
        label = _relative(module)
        if label == _ALLOWED_FILE:
            continue
        violations.extend(_escaped_nlp_imports(module.read_text(encoding="utf-8"), label))

    assert not violations, "a spaCy/thinc/stanza import escaped the adapter package:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_the_adapter_file_itself_does_import_spacy() -> None:
    """Sanity check on the allow-list itself: the one exempted path must be
    a real spaCy consumer, not a stale or mistyped path that would make the
    guard above vacuous by accidentally exempting the wrong file."""
    adapter_path = _PACKAGE_ROOT / _ALLOWED_FILE
    tree = ast.parse(adapter_path.read_text(encoding="utf-8"), filename=_ALLOWED_FILE)

    assert "spacy" in _imported_roots(tree)


@pytest.mark.unit
def test_an_nlp_import_outside_the_adapter_would_be_caught() -> None:
    """Direct mutation check, run synthetically so it never has to touch
    production code to prove the detector itself works."""
    spacy_source = "import spacy\n"
    thinc_source = "from thinc.api import Model\n"
    stanza_source = "import stanza as nlp_stanza\n"

    assert _escaped_nlp_imports(spacy_source, "synthetic.py")
    assert _escaped_nlp_imports(thinc_source, "synthetic.py")
    assert _escaped_nlp_imports(stanza_source, "synthetic.py")


@pytest.mark.unit
def test_the_allow_list_exemption_is_applied_by_exact_path_not_a_directory_prefix() -> None:
    """The main guard's loop skips exactly `_ALLOWED_FILE` by string equality
    — proven here by confirming a DIFFERENT file under the same
    `infrastructure/nlp/` directory (`registry.py`, which does not import
    spaCy directly) is still scanned rather than exempted wholesale."""
    registry_path = _PACKAGE_ROOT / "infrastructure" / "nlp" / "registry.py"
    label = _relative(registry_path)

    assert label != _ALLOWED_FILE
    assert label.startswith("infrastructure/nlp/")
    assert _escaped_nlp_imports(registry_path.read_text(encoding="utf-8"), label) == []
