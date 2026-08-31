"""Executable response-budget benchmark for the vocabulary endpoint."""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from _vocabulary_bench_corpus import seed_vocabulary_benchmark_corpus
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from wheel_vocabulary.api.dependencies import get_read_vocabulary
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.vocabulary.use_cases import ReadVocabulary
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection, Occurrence
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
)
from wheel_vocabulary.infrastructure.settings import Settings

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine

_OCCURRENCE_COUNT = 688_000
_MANUAL_CORRECTION_COUNT = 5_000
_RESPONSE_BODY_BUDGET_BYTES = 4_194_304
_LATENCY_P95_BUDGET_MS = 1_000
_MEASUREMENTS = 9
_STRICT = os.environ.get("WHEEL_BENCH_STRICT") == "1"


def _p95_ms(samples_ms: list[float]) -> float:
    """Return the inclusive p95 for the fixed benchmark sample size."""
    return statistics.quantiles(samples_ms, n=100, method="inclusive")[94]


def _assert_response_budget(
    *,
    response_bytes: int,
    p95_ms: float,
    max_response_bytes: int = _RESPONSE_BODY_BUDGET_BYTES,
    max_p95_ms: int = _LATENCY_P95_BUDGET_MS,
) -> None:
    """Assert the two named bounds from design §Response budget."""
    assert response_bytes <= max_response_bytes
    assert p95_ms <= max_p95_ms


def _client_for_benchmark(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> tuple[TestClient, int]:
    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary_bench.db'}"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    corpus = seed_vocabulary_benchmark_corpus(
        session_factory,
        occurrence_count=_OCCURRENCE_COUNT,
        manual_correction_count=_MANUAL_CORRECTION_COUNT,
    )
    repository = SqlAlchemyVocabularyReadRepository(session_factory)
    app = create_app()
    app.dependency_overrides[get_read_vocabulary] = lambda: ReadVocabulary(repository=repository)
    return TestClient(app), corpus.book_id


def test_response_body_budget_is_derived_from_the_external_import_size_limit() -> None:
    """AC-005-11: the named body budget equals its externally anchored input limit."""
    design_path = Path(__file__).parents[4] / "openspec/changes/vocabulary-browser/design.md"
    design = design_path.read_text(encoding="utf-8")

    assert Settings().max_import_size_bytes == _RESPONSE_BODY_BUDGET_BYTES
    assert "4,194,304 = 4,194,304" in design
    assert "must not exceed the input that produced it" in design


def test_occurrence_level_benchmark_corpus_has_the_specified_composition(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    engine = managed_engine(
        create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary_corpus.db'}")
    )
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    corpus = seed_vocabulary_benchmark_corpus(
        session_factory,
        occurrence_count=10_000,
        manual_correction_count=100,
    )

    with session_factory() as session:
        occurrence_count = session.scalar(
            select(func.count()).select_from(Occurrence).where(Occurrence.book_id == corpus.book_id)
        )
        unannotated_count = session.scalar(
            select(func.count())
            .select_from(Occurrence)
            .where(Occurrence.book_id == corpus.book_id, Occurrence.lemma.is_(None))
        )
        correction_count = session.scalar(select(func.count()).select_from(ManualCorrection))

    assert occurrence_count == corpus.occurrence_count == 10_000
    assert corpus.homograph_lemma_count == 3_600
    assert unannotated_count == corpus.unannotated_count == 200
    assert correction_count == corpus.manual_correction_count == 100


@pytest.mark.bench
def test_vocabulary_response_stays_within_the_named_budget_at_the_occurrence_ceiling(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """REQ-005-011: measure all groups at 688,000 occurrences through HTTP."""
    client, book_id = _client_for_benchmark(tmp_path, managed_engine)

    samples_ms: list[float] = []
    response = None
    for _ in range(_MEASUREMENTS):
        started = time.perf_counter()
        response = client.get(f"/api/v1/imports/{book_id}/vocabulary")
        samples_ms.append((time.perf_counter() - started) * 1_000)

    assert response is not None
    assert response.status_code == 200
    body = response.json()
    assert len(body["groups"]) == body["group_count"]
    assert sum(group["occurrence_count"] for group in body["groups"]) == _OCCURRENCE_COUNT

    response_bytes = len(response.content)
    p95_ms = _p95_ms(samples_ms)
    report = (
        "T-VOCAB-BENCH measurements — "
        f"occurrences={_OCCURRENCE_COUNT} groups={body['group_count']} "
        f"response_body={response_bytes}B p95={p95_ms:.0f}ms "
        f"strict_mode={'on' if _STRICT else 'off'}"
    )
    print(report)  # noqa: T201 - benchmark observations belong in CI output

    assert response_bytes <= _RESPONSE_BODY_BUDGET_BYTES
    if _STRICT:
        assert p95_ms <= _LATENCY_P95_BUDGET_MS, report


def test_lowering_each_named_bound_below_its_measurement_fails() -> None:
    """AC-005-11 mutation checks: 2,063,621B and 533ms each breach a lowered bound."""
    with pytest.raises(AssertionError):
        _assert_response_budget(
            response_bytes=2_063_621,
            p95_ms=533,
            max_response_bytes=2_063_620,
        )

    with pytest.raises(AssertionError):
        _assert_response_budget(
            response_bytes=2_063_621,
            p95_ms=533,
            max_p95_ms=532,
        )
