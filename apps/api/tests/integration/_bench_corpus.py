"""In-test synthetic corpus generator for T-BENCH (T216).

Test-infrastructure only — no `wheel_vocabulary` source change. The generated
corpus is never committed (Art. IV.1-2, H6): it is built at test run time from
a fixed PRNG seed, so every run reproduces byte-identical output without any
file ever touching the repository.

Every "word" is a synthetic ASCII string, never real prose — there is no
copyrighted content anywhere in this fixture. A Zipfian sampling weight
(`1/rank`) over a 30,000-word synthetic vocabulary approximates the
English-prose-like token distribution the design's arithmetic assumes
(design §3.1, §3.4.1 — Heaps' law type growth needs a genuinely skewed
frequency distribution to reproduce, not uniform random words).

REQ-002-008 (T-BENCH proves the persisted path at scale), Art. IV.1-2, H6.
"""

from __future__ import annotations

import itertools
import random
import string

__all__ = ["generate_synthetic_corpus"]

_VOCABULARY_SIZE = 30_000
_SEPARATOR_BYTES = 1


def _synthetic_word(rng: random.Random, index: int) -> str:
    """A short, deterministic ASCII string — never a real word."""
    length = 3 + (index % 8)
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(length))


def generate_synthetic_corpus(target_bytes: int, *, seed: int = 20260811) -> bytes:
    """Return exactly `target_bytes` of space-separated synthetic ASCII tokens.

    Deterministic for a fixed `seed`: the same call always returns the same
    bytes, so `read_bounded_and_hash` (production, T210) applied to this
    output is reproducible across runs — a real invariant, not merely a
    convenience. Pure ASCII on purpose: truncating at an exact byte boundary
    is always safe, since no codepoint spans more than one byte.
    """
    rng = random.Random(seed)  # noqa: S311 - synthetic test fixture, not cryptography
    vocabulary = [_synthetic_word(rng, index) for index in range(_VOCABULARY_SIZE)]
    weights = [1.0 / rank for rank in range(1, _VOCABULARY_SIZE + 1)]
    cumulative_weights = list(itertools.accumulate(weights))

    average_token_bytes = sum(len(word) for word in vocabulary) / len(vocabulary) + _SEPARATOR_BYTES
    estimate = int(target_bytes / average_token_bytes * 1.05) + 1_000

    words = rng.choices(vocabulary, cum_weights=cumulative_weights, k=estimate)
    text = " ".join(words)
    encoded = text.encode("ascii")

    while len(encoded) < target_bytes:
        extra = rng.choices(vocabulary, cum_weights=cumulative_weights, k=10_000)
        text += " " + " ".join(extra)
        encoded = text.encode("ascii")

    return encoded[:target_bytes]
