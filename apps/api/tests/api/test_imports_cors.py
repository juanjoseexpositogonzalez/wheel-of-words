"""CORS preflight tests for POST /api/v1/imports — design §14.1 (T1B17).

Every other test in this suite passes whether or not `POST` is allowed through
CORS, because `TestClient` sends no `Origin` header by default and Starlette's
`CORSMiddleware` only acts on requests that carry one. The middleware is
perfectly testable — it just has to be asked explicitly, which is what these
tests do. Without them, a browser-only failure would surface for the first time
in the Playwright suite of a later cut, or in production.

REQ-002-001, design §14.1.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.main import create_app

_ENDPOINT = "/api/v1/imports"
_ORIGIN = "http://127.0.0.1:5173"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _preflight(client: TestClient, method: str, **extra: str) -> object:
    return client.options(
        _ENDPOINT,
        headers={
            "Origin": _ORIGIN,
            "Access-Control-Request-Method": method,
            **extra,
        },
    )


@pytest.mark.unit
def test_a_post_preflight_is_allowed(client: TestClient) -> None:
    """A browser cannot upload at all unless this preflight succeeds."""
    response = _preflight(client, "POST")

    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]


@pytest.mark.unit
def test_the_preflight_echoes_the_configured_origin(client: TestClient) -> None:
    """The dev frontend origin must be the one that is allowed."""
    assert _preflight(client, "POST").headers["access-control-allow-origin"] == _ORIGIN


@pytest.mark.unit
def test_a_multipart_content_type_needs_no_allow_headers_entry(client: TestClient) -> None:
    """`Content-Type` is in Starlette's SAFELISTED_HEADERS, so `allow_headers=[]` is correct.

    This is the assertion that makes "fixing" `allow_headers` unnecessary
    demonstrable rather than merely asserted in a comment (Art. VII.6).
    """
    response = _preflight(client, "POST", **{"Access-Control-Request-Headers": "content-type"})

    assert response.status_code == 200


@pytest.mark.unit
def test_the_health_preflight_still_works(client: TestClient) -> None:
    """Extending the method list must not disturb the surface that already shipped."""
    response = client.options(
        "/api/v1/health",
        headers={"Origin": _ORIGIN, "Access-Control-Request-Method": "GET"},
    )

    assert response.status_code == 200
    assert "GET" in response.headers["access-control-allow-methods"]


@pytest.mark.unit
def test_a_delete_preflight_is_allowed(client: TestClient) -> None:
    """T305/AC-002-15: a browser cannot issue DELETE at all unless this preflight succeeds."""
    response = _preflight(client, "DELETE")

    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]


@pytest.mark.unit
def test_a_method_this_cut_does_not_expose_is_still_refused(client: TestClient) -> None:
    """`PUT` is never exposed by this capability; the preflight must reject it.

    This is the negative control. Without it, an `allow_methods=["*"]` regression
    would leave every assertion above green. `DELETE` was this negative control
    before cut 3 (T306); it moved to `PUT` once `DELETE` became a real, exposed
    method — the negative control must name a method that is genuinely never
    exposed, not one merely not-yet-exposed at authoring time.
    """
    response = _preflight(client, "PUT")

    assert response.status_code == 400
    assert response.text == "Disallowed CORS method"
