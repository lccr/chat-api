"""Integration tests for the centralized error handlers.

Verify that unexpected server errors and framework HTTP errors are both
rendered through the uniform error envelope.
"""

import pytest
from app.api.deps import get_message_service
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_unexpected_error_returns_500_envelope(app: FastAPI) -> None:
    """An unhandled exception is rendered as a 500 error envelope."""

    def boom() -> None:
        raise RuntimeError("unexpected failure")

    app.dependency_overrides[get_message_service] = boom
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/messages",
        json={
            "message_id": "m",
            "session_id": "s",
            "content": "hi",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user",
        },
    )

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INTERNAL_ERROR"
    # The internal message must not leak to the client.
    assert "unexpected failure" not in str(body)


def test_unknown_route_returns_404_envelope(client: TestClient) -> None:
    """A framework 404 is wrapped in the error envelope."""
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "HTTP_ERROR"


def test_method_not_allowed_returns_405_envelope(client: TestClient) -> None:
    """A framework 405 is wrapped in the error envelope."""
    response = client.put("/api/messages")

    assert response.status_code == 405
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "HTTP_ERROR"
