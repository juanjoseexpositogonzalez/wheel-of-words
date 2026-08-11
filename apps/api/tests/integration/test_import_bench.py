"""T-BENCH: import + read benchmark at the 4 MiB size ceiling — design §3.3-3.5 (T215).

**Maintainer amendment, binding (tasks.md contradiction note 7).** `design.md`
§3.5 defines this benchmark as a *decision trigger*: it measures whether the
read-path aggregation segment exceeds 250 ms p95, to decide later whether a
`form_frequency` aggregate table is warranted. Its job is to produce a
measurement, not to gate the build on second-scale wall-clock budgets —
shared GitHub-hosted CI runners produce intermittent red on those budgets with
no defect behind it, and a flaky test is the first one anyone stops trusting,
which is exactly the test carrying the architecture trigger.

Default run (every CI invocation): only DETERMINISTIC invariants fail the
build — response row count self-consistency, a sane response-body-size range,
and Σfrequency == total_token_count. Wall-clock numbers (import time, GET
latency, the isolated aggregation segment) are measured, reported in the test
output, and the aggregation segment is compared against the §3.5 250 ms
trigger — but a breach does not fail this run.

Set `WHEEL_BENCH_STRICT=1` to additionally assert the §3.3/§3.4.5 wall-clock
budgets, on known hardware. Not run by default CI (`@pytest.mark.bench`
documents the opt-in surface in `pyproject.toml`; the env var is the actual
gate, since this repo's `addopts` does not exclude markers by default).

The corpus is generated in-test by `_bench_corpus.generate_synthetic_corpus`
and never committed (Art. IV.1-2, H6, T216).

REQ-002-008.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import pytest
from _bench_corpus import generate_synthetic_corpus
from fastapi.testclient import TestClient

from wheel_vocabulary.api.dependencies import get_book_repository, get_import_text
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.imports.use_cases import ImportText, read_bounded_and_hash
from wheel_vocabulary.domain.frequency import build_table
from wheel_vocabulary.infrastructure.clock import SystemClock
from wheel_vocabulary.infrastructure.persistence.book_repository import (
    SqlAlchemyBookRepository,
)
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sqlalchemy import Engine

_TARGET_BYTES = 4_194_304  # design §3.6 — the amended 4 MiB ceiling
_AGGREGATION_TRIGGER_SECONDS = 0.25  # design §3.5 — the 250 ms p95 decision trigger
_STRICT = os.environ.get("WHEEL_BENCH_STRICT") == "1"
_STRICT_IMPORT_BUDGET_SECONDS = 6.0  # design §3.3: "~4.9 s" with headroom for CI variance
_STRICT_GET_BUDGET_SECONDS = 2.0  # design §3.4.5: "0.53-1.26 s" with headroom


@pytest.mark.bench
def test_import_and_read_benchmark_at_the_size_ceiling(
    tmp_path: Path,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """Import a 4 MiB synthetic corpus, read it back, measure both paths."""
    corpus = generate_synthetic_corpus(_TARGET_BYTES)
    assert len(corpus) == _TARGET_BYTES

    from wheel_vocabulary.infrastructure.persistence.base import Base
    from wheel_vocabulary.infrastructure.persistence.engine import (
        create_engine_from_url,
        create_session_factory,
    )

    engine = managed_engine(create_engine_from_url(f"sqlite:///{tmp_path / 'bench.db'}"))
    Base.metadata.create_all(engine)
    repository = SqlAlchemyBookRepository(create_session_factory(engine))

    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: repository
    app.dependency_overrides[get_import_text] = lambda: ImportText(
        extractor=PlainTextExtractor(),
        max_size_bytes=_TARGET_BYTES,
        repository=repository,
        clock=SystemClock(),
    )
    client = TestClient(app)

    import_started = time.perf_counter()
    response = client.post("/api/v1/imports", files={"file": ("corpus.txt", corpus, "text/plain")})
    import_elapsed = time.perf_counter() - import_started

    assert response.status_code == 201
    body = response.json()

    # Deterministic invariant 1: Σfrequency == total_token_count (AC-002-08).
    assert sum(row["frequency"] for row in body["forms"]) == body["total_token_count"]
    # Non-vacuity: a 4 MiB corpus must yield thousands of distinct forms, not a
    # degenerate handful — proves the real domain pipeline ran at scale.
    assert body["distinct_form_count"] > 1_000

    read_started = time.perf_counter()
    get_response = client.get(f"/api/v1/imports/{body['id']}")
    read_elapsed = time.perf_counter() - read_started

    assert get_response.status_code == 200
    read_body = get_response.json()

    # Deterministic invariant 2: response row count is self-consistent between
    # the reported count and the actual list length.
    assert len(read_body["forms"]) == read_body["distinct_form_count"]
    assert read_body["distinct_form_count"] == body["distinct_form_count"]
    # Deterministic invariant 3: Σfrequency == total_token_count on the read path too.
    assert sum(row["frequency"] for row in read_body["forms"]) == read_body["total_token_count"]

    response_bytes = len(get_response.content)
    # Deterministic invariant 4: response body size falls in a sane range for a
    # 4 MiB import (design §3.4.3: ~2.2-6.3 MB). Not an exact byte count — the
    # corpus generator's internals may shift slightly — but a value outside a
    # generous multiple of that range means something is badly wrong (e.g. a
    # truncated or duplicated response).
    assert 200_000 < response_bytes < 20_000_000

    # The aggregation segment, isolated from HTTP/serialisation overhead —
    # exactly the span design §3.5's trigger measures.
    aggregation_started = time.perf_counter()
    pairs = repository.frequency_pairs(body["id"])
    assert pairs is not None
    forms = build_table(pairs)
    aggregation_elapsed = time.perf_counter() - aggregation_started
    assert len(forms) == body["distinct_form_count"]

    trigger_breached = aggregation_elapsed > _AGGREGATION_TRIGGER_SECONDS
    report = (
        "T-BENCH measurements — "
        f"corpus={len(corpus)}B import={import_elapsed:.3f}s "
        f"GET_total={read_elapsed:.3f}s aggregation_segment={aggregation_elapsed:.3f}s "
        f"(design §3.5 250ms p95 trigger: {'BREACH' if trigger_breached else 'within budget'}) "
        f"rows={len(forms)} response_body={response_bytes}B "
        f"strict_mode={'on' if _STRICT else 'off'}"
    )
    print(report)  # noqa: T201 - deliberate: a human reading CI output must see the numbers

    if _STRICT:
        assert import_elapsed < _STRICT_IMPORT_BUDGET_SECONDS, report
        assert read_elapsed < _STRICT_GET_BUDGET_SECONDS, report


def test_generate_synthetic_corpus_is_deterministic_and_ascii_only() -> None:
    """A property of the generator itself, not the import path (fast, no HTTP)."""
    first = generate_synthetic_corpus(10_000)
    second = generate_synthetic_corpus(10_000)

    assert first == second
    assert len(first) == 10_000
    first.decode("ascii")  # raises if any byte is non-ASCII


def test_read_bounded_and_hash_matches_generated_corpus_bytes() -> None:
    """T210: the shared helper hashes the corpus generator's own output identically."""
    import hashlib
    import io

    corpus = generate_synthetic_corpus(50_000)
    stream = io.BytesIO(corpus)

    data, digest = read_bounded_and_hash(stream, len(corpus))

    assert data == corpus
    assert digest == hashlib.sha256(corpus).hexdigest()
