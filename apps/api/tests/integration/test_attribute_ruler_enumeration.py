"""Integration coverage for runtime-only attribute-ruler claims.

K2 mutation fixture observed failure output:
``ValueError: runtime enumeration differs from supplied enumeration``.
"""

from __future__ import annotations

import ast
import sys
from itertools import combinations
from pathlib import Path

import pytest
import spacy
from _attribute_ruler_enumeration import (
    assert_matches_pipeline,
    enumerate_attribute_ruler,
    mutate_one_enumerated_value,
)

from wheel_vocabulary.infrastructure.nlp.spacy_analyzer import _EXCLUDED_PIPES

_MODEL_NAME = "en_core_web_sm"
_DOMAIN_PATH = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary" / "domain"


def _imported_roots(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


def _absolute_import_modules(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None
    }


@pytest.fixture
def loaded_pipeline() -> object:
    """Load the pinned model directly; absence must fail this integration test."""
    return spacy.load(_MODEL_NAME, exclude=_EXCLUDED_PIPES)


@pytest.mark.integration
def test_runtime_enumeration_has_only_computed_shape_and_partition_predicates(
    loaded_pipeline: object,
) -> None:
    enumeration = enumerate_attribute_ruler(loaded_pipeline)

    assert enumeration.rules
    assert enumeration.target_fine_tags
    assert all(fine_tags for fine_tags in enumeration.target_fine_tags.values())
    assert set(enumeration.reachable_rules).isdisjoint(enumeration.unreachable_rules)
    assert set(enumeration.reachable_rules) | set(enumeration.unreachable_rules) == set(
        enumeration.rules
    )
    assert enumeration.unreachable_rules
    assert all(
        not rule.predicate_names.isdisjoint(enumeration.unavailable_predicate_names)
        for rule in enumeration.unreachable_rules
    )
    assert all(
        set(left).isdisjoint(right)
        for left, right in combinations(enumeration.exact_target_fine_tags.values(), 2)
    )


@pytest.mark.integration
def test_exact_mappings_are_derived_from_the_runtime_enumeration(
    loaded_pipeline: object,
) -> None:
    enumeration = enumerate_attribute_ruler(loaded_pipeline)

    for fine_tag, target in enumeration.exact_mappings.items():
        assert enumeration.fine_tag_targets[fine_tag] == frozenset({target})
    assert {
        fine_tag: next(iter(targets))
        for fine_tag, targets in enumeration.fine_tag_targets.items()
        if len(targets) == 1
    } == enumeration.exact_mappings


@pytest.mark.integration
def test_mutating_one_runtime_value_is_rejected_by_a_fresh_enumeration(
    loaded_pipeline: object,
) -> None:
    enumeration = enumerate_attribute_ruler(loaded_pipeline)

    with pytest.raises(ValueError, match="runtime enumeration differs from supplied enumeration"):
        assert_matches_pipeline(loaded_pipeline, mutate_one_enumerated_value(enumeration))


@pytest.mark.integration
def test_domain_imports_remain_stdlib_only_after_enumeration_lands() -> None:
    module_paths = tuple(_DOMAIN_PATH.rglob("*.py"))
    imported_roots = set().union(*(_imported_roots(path) for path in module_paths))
    absolute_imports = set().union(*(_absolute_import_modules(path) for path in module_paths))

    assert not (imported_roots - sys.stdlib_module_names - {"wheel_vocabulary"})
    assert all(
        module.startswith("wheel_vocabulary.domain")
        for module in absolute_imports
        if module.split(".")[0] not in sys.stdlib_module_names
    )
