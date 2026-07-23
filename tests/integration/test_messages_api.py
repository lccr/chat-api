"""Integration tests for the message API endpoints.

These exercise the full stack through HTTP: routing, validation, error
handling, the service, the pipeline and a real (in-memory) database. They
verify the pieces fit together and the response envelope is honored.
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _valid_body(**overrides: object) -> dict[str, object]:
    """Build a valid request body, overriding only the fields under test."""
    body: dict[str, object] = {
        "message_id": "msg-1",
        "session_id": "sess-1",
        "content": "hello world",
        "timestamp": "2023-06-15T14:30:00Z",
        "sender": "user",
    }
    body.update(overrides)
    return body


class TestCreateMessageEndpoint:
    """POST /api/messages."""

    def test_creates_a_message_returning_201_and_envelope(self, client: TestClient) -> None:
        response = client.post("/api/messages", json=_valid_body())

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["message_id"] == "msg-1"
        assert body["data"]["metadata"]["word_count"] == 2

    def test_censors_banned_content(self, client: TestClient) -> None:
        response = client.post("/api/messages", json=_valid_body(content="hello badword"))
        assert response.status_code == 201
        assert response.json()["data"]["content"] == "hello *******"

    def test_duplicate_message_id_returns_409(self, client: TestClient) -> None:
        client.post("/api/messages", json=_valid_body(message_id="dup"))
        response = client.post("/api/messages", json=_valid_body(message_id="dup"))

        assert response.status_code == 409
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "DUPLICATE_MESSAGE"

    def test_invalid_sender_returns_422_with_error_envelope(self, client: TestClient) -> None:
        response = client.post("/api/messages", json=_valid_body(sender="robot"))

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "INVALID_FORMAT"

    def test_missing_field_returns_422(self, client: TestClient) -> None:
        body = _valid_body()
        del body["content"]
        response = client.post("/api/messages", json=body)
        assert response.status_code == 422

    def test_extra_field_is_rejected(self, client: TestClient) -> None:
        response = client.post("/api/messages", json=_valid_body(unexpected="x"))
        assert response.status_code == 422


class TestListMessagesEndpoint:
    """GET /api/messages/{session_id}."""

    def _seed(self, client: TestClient, count: int, session_id: str = "sess-1") -> None:
        for i in range(count):
            client.post(
                "/api/messages",
                json=_valid_body(message_id=f"m{i}", session_id=session_id),
            )

    def test_returns_paginated_envelope(self, client: TestClient) -> None:
        self._seed(client, 3)
        response = client.get("/api/messages/sess-1")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_respects_limit_and_offset(self, client: TestClient) -> None:
        self._seed(client, 5)
        response = client.get("/api/messages/sess-1?limit=2&offset=2")

        data = response.json()["data"]
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_filters_by_sender(self, client: TestClient) -> None:
        client.post("/api/messages", json=_valid_body(message_id="u", sender="user"))
        client.post("/api/messages", json=_valid_body(message_id="s", sender="system"))
        response = client.get("/api/messages/sess-1?sender=system")

        data = response.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["message_id"] == "s"

    def test_empty_session_returns_empty_page(self, client: TestClient) -> None:
        response = client.get("/api/messages/nonexistent")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    def test_limit_over_maximum_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/messages/sess-1?limit=500")
        assert response.status_code == 422

    def test_timestamp_survives_round_trip_as_utc(self, client: TestClient) -> None:
        """Regression test: the GET timestamp must keep its UTC marker."""
        client.post("/api/messages", json=_valid_body(message_id="tz"))
        response = client.get("/api/messages/sess-1")

        timestamp = response.json()["data"]["items"][0]["timestamp"]
        assert timestamp.endswith("Z") or timestamp.endswith("+00:00")
