"""Unit tests for the strict UTF-8 extractor — design §7.3 (T1B06).

Two behaviours are under test and they pull in opposite directions: the decode
must be strict (no sniffing, no fallback, no dependency) while a leading BOM must
be tolerated, because Windows editors emit one and rejecting it would be a
mystifying failure for a file that is perfectly valid UTF-8.

The third behaviour is negative and just as important: ``UnicodeDecodeError``
renders the offending byte and its offset into the user's text, so the
translation to ``InvalidEncodingError`` must break the chain rather than carry it
(Art. X.2, REQ-002-013).

REQ-002-004 / AC-002-05.
"""

from __future__ import annotations

import pytest

from wheel_vocabulary.application.imports.errors import InvalidEncodingError
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

_BOM = b"\xef\xbb\xbf"
_SENTINEL = "zzqxsentinel"


@pytest.fixture
def extractor() -> PlainTextExtractor:
    return PlainTextExtractor()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"", ""),
        (b"hola mundo", "hola mundo"),
        ("Stra\u00dfe caf\u00e9".encode(), "Stra\u00dfe caf\u00e9"),
        (
            "\u03a3\u03af\u03c3\u03c5\u03c6\u03bf\u03c2".encode(),
            "\u03a3\u03af\u03c3\u03c5\u03c6\u03bf\u03c2",
        ),
    ],
)
def test_valid_utf8_decodes_verbatim(
    extractor: PlainTextExtractor, data: bytes, expected: str
) -> None:
    """Non-ASCII scripts must survive untouched — no transliteration, no loss."""
    assert extractor.extract(data) == expected


@pytest.mark.unit
def test_leading_bom_is_stripped(extractor: PlainTextExtractor) -> None:
    """AC-002-05: a BOM-prefixed file imports, and U+FEFF does not enter the text."""
    text = extractor.extract(_BOM + b"hola")

    assert text == "hola"
    assert "\ufeff" not in text


@pytest.mark.unit
def test_bom_only_file_yields_empty_text(extractor: PlainTextExtractor) -> None:
    """REQ-002-012: a file that is nothing but a BOM is empty, not broken."""
    assert extractor.extract(_BOM) == ""


@pytest.mark.unit
def test_only_the_leading_bom_is_stripped(extractor: PlainTextExtractor) -> None:
    """A U+FEFF further in is content, not a byte-order mark."""
    assert extractor.extract(b"hola" + _BOM + b"mundo") == "hola\ufeffmundo"


@pytest.mark.unit
@pytest.mark.parametrize("data", [b"\xff", b"hola\xffmundo", b"\xc3\x28", b"\x80abc"])
def test_invalid_utf8_is_rejected(extractor: PlainTextExtractor, data: bytes) -> None:
    """AC-002-05: strict decoding — never guess, sniff, or fall back to Latin-1."""
    with pytest.raises(InvalidEncodingError):
        extractor.extract(data)


@pytest.mark.unit
def test_latin1_text_is_rejected_rather_than_silently_mangled(
    extractor: PlainTextExtractor,
) -> None:
    """The realistic case: a Latin-1 file must fail loudly, not import as mojibake."""
    with pytest.raises(InvalidEncodingError):
        extractor.extract("caf\u00e9".encode("latin-1"))


@pytest.mark.unit
def test_rejection_breaks_the_exception_chain(extractor: PlainTextExtractor) -> None:
    """`raise ... from None`: a chained UnicodeDecodeError renders into tracebacks."""
    with pytest.raises(InvalidEncodingError) as failure:
        extractor.extract(_SENTINEL.encode() + b"\xff")

    assert failure.value.__cause__ is None
    assert failure.value.__suppress_context__ is True


@pytest.mark.unit
def test_rejection_leaks_neither_the_text_nor_the_byte_offset(
    extractor: PlainTextExtractor,
) -> None:
    """Art. X.2: the offset is an index into the user's content, so it must not ship."""
    payload = _SENTINEL.encode() + b"\xff"

    with pytest.raises(InvalidEncodingError) as failure:
        extractor.extract(payload)

    rendered = f"{failure.value!s} {failure.value!r} {vars(failure.value)}"

    assert _SENTINEL not in rendered
    assert str(len(_SENTINEL)) not in rendered
    assert "0xff" not in rendered.casefold()
