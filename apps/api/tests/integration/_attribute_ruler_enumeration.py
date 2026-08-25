"""Runtime enumeration of the loaded attribute-ruler pipeline."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, cast

from wheel_vocabulary.infrastructure.nlp.spacy_analyzer import _EXCLUDED_PIPES

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


_OUTPUT_ATTRIBUTES_BY_EXCLUDED_PIPE: dict[str, frozenset[str]] = {
    "parser": frozenset({"DEP"}),
    "ner": frozenset({"ENT_IOB", "ENT_TYPE"}),
    "senter": frozenset({"SENT_START"}),
}


@dataclass(frozen=True)
class AttributeRulerRule:
    target: str | None
    fine_tags: frozenset[str]
    predicate_names: frozenset[str]


@dataclass(frozen=True)
class AttributeRulerEnumeration:
    rules: tuple[AttributeRulerRule, ...]
    target_fine_tags: dict[str, frozenset[str]]
    fine_tag_targets: dict[str, frozenset[str]]
    reachable_rules: tuple[AttributeRulerRule, ...]
    unreachable_rules: tuple[AttributeRulerRule, ...]
    exact_mappings: dict[str, str]
    exact_target_fine_tags: dict[str, frozenset[str]]
    unavailable_predicate_names: frozenset[str]


def enumerate_attribute_ruler(nlp: object) -> AttributeRulerEnumeration:
    """Compute model claims from a loaded spaCy pipeline without literals."""
    attribute_ruler = cast("Any", nlp).get_pipe("attribute_ruler")
    raw_rules = cast("Sequence[Mapping[str, object]]", attribute_ruler.patterns)
    unavailable_attributes = _excluded_output_attributes()
    rules = tuple(_rule_from(raw_rule) for raw_rule in raw_rules)
    target_fine_tags = _target_fine_tags(rules)
    fine_tag_targets = _fine_tag_targets(target_fine_tags)
    exact_mappings = {
        fine_tag: next(iter(targets))
        for fine_tag, targets in fine_tag_targets.items()
        if len(targets) == 1
    }
    exact_target_fine_tags = _exact_target_fine_tags(exact_mappings)
    reachable_rules = tuple(
        rule for rule in rules if rule.predicate_names.isdisjoint(unavailable_attributes)
    )
    unreachable_rules = tuple(
        rule for rule in rules if not rule.predicate_names.isdisjoint(unavailable_attributes)
    )
    return AttributeRulerEnumeration(
        rules=rules,
        target_fine_tags=target_fine_tags,
        fine_tag_targets=fine_tag_targets,
        reachable_rules=reachable_rules,
        unreachable_rules=unreachable_rules,
        exact_mappings=exact_mappings,
        exact_target_fine_tags=exact_target_fine_tags,
        unavailable_predicate_names=unavailable_attributes,
    )


def assert_matches_pipeline(nlp: object, expected: AttributeRulerEnumeration) -> None:
    """Reject a value that was not freshly derived from the loaded pipeline."""
    if enumerate_attribute_ruler(nlp) != expected:
        raise ValueError("runtime enumeration differs from supplied enumeration")


def mutate_one_enumerated_value(
    enumeration: AttributeRulerEnumeration,
) -> AttributeRulerEnumeration:
    """Return the K2 fixture with one runtime-derived value deliberately changed."""
    for position, rule in enumerate(enumeration.rules):
        if rule.target is not None:
            changed_rule = replace(rule, target=f"{rule.target}_mutated")
            return replace(
                enumeration,
                rules=(
                    enumeration.rules[:position]
                    + (changed_rule,)
                    + enumeration.rules[position + 1 :]
                ),
            )
    raise ValueError("runtime enumeration contains no target to mutate")


def _excluded_output_attributes() -> frozenset[str]:
    return frozenset().union(
        *(
            _OUTPUT_ATTRIBUTES_BY_EXCLUDED_PIPE.get(pipe_name, frozenset())
            for pipe_name in _EXCLUDED_PIPES
        )
    )


def _rule_from(raw_rule: Mapping[str, object]) -> AttributeRulerRule:
    attributes = cast("Mapping[str, object]", raw_rule["attrs"])
    target = attributes.get("POS")
    patterns = cast("Sequence[Sequence[Mapping[str, object]]]", raw_rule["patterns"])
    selected_index = cast("int", raw_rule["index"])
    selected_tokens = (pattern[selected_index] for pattern in patterns)
    fine_tags = frozenset(
        tag for token in selected_tokens if isinstance(tag := token.get("TAG"), str)
    )
    return AttributeRulerRule(
        target=target if isinstance(target, str) else None,
        fine_tags=fine_tags,
        predicate_names=frozenset(
            predicate_name for pattern in patterns for token in pattern for predicate_name in token
        ),
    )


def _target_fine_tags(rules: Sequence[AttributeRulerRule]) -> dict[str, frozenset[str]]:
    targets: dict[str, set[str]] = {}
    for rule in rules:
        if rule.target is not None and rule.fine_tags:
            targets.setdefault(rule.target, set()).update(rule.fine_tags)
    return {target: frozenset(fine_tags) for target, fine_tags in targets.items()}


def _fine_tag_targets(target_fine_tags: Mapping[str, frozenset[str]]) -> dict[str, frozenset[str]]:
    targets: dict[str, set[str]] = {}
    for target, fine_tags in target_fine_tags.items():
        for fine_tag in fine_tags:
            targets.setdefault(fine_tag, set()).add(target)
    return {fine_tag: frozenset(targets_for_tag) for fine_tag, targets_for_tag in targets.items()}


def _exact_target_fine_tags(exact_mappings: Mapping[str, str]) -> dict[str, frozenset[str]]:
    targets: dict[str, set[str]] = {}
    for fine_tag, target in exact_mappings.items():
        targets.setdefault(target, set()).add(fine_tag)
    return {target: frozenset(fine_tags) for target, fine_tags in targets.items()}
