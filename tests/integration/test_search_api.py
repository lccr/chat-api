"""Integration tests for full-text message search."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _post(client: TestClient, message_id: str, content: str, session_id: str = "sess-a") -> None:
    """Store a message with the given content."""
    client.post(
        "/api/messages",
        json={
            "message_id": message_id,
            "session_id": session_id,
            "content": content,
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user",
        },
    )


@pytest.fixture()
def seeded(client: TestClient) -> TestClient:
    """A client with a small corpus of messages already stored."""
    _post(client, "m1", "necesito ayuda con mi pedido")
    _post(client, "m2", "el pedido llego incompleto")
    _post(client, "m3", "buenos dias como esta el clima", session_id="sess-b")
    return client


class TestSearchEndpoint:
    """GET /api/messages/search."""

    def test_finds_messages_containing_the_term(self, seeded: TestClient) -> None:
        response = seeded.get("/api/messages/search?q=pedido")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 2
        assert {item["message_id"] for item in data["items"]} == {"m1", "m2"}

    def test_returns_empty_page_for_unmatched_term(self, seeded: TestClient) -> None:
        response = seeded.get("/api/messages/search?q=inexistente")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_scopes_results_to_a_session(self, seeded: TestClient) -> None:
        response = seeded.get("/api/messages/search?q=pedido&session_id=sess-b")

        assert response.json()["data"]["total"] == 0

    def test_paginates_results(self, seeded: TestClient) -> None:
        response = seeded.get("/api/messages/search?q=pedido&limit=1&offset=0")

        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["total"] == 2

    def test_query_with_fts_syntax_does_not_break(self, seeded: TestClient) -> None:
        """User input is treated as a literal phrase, not FTS5 query syntax."""
        response = seeded.get("/api/messages/search?q=pedido AND")

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_empty_query_is_rejected(self, seeded: TestClient) -> None:
        response = seeded.get("/api/messages/search?q=")

        assert response.status_code == 422

    def test_search_route_is_not_shadowed_by_session_route(self, seeded: TestClient) -> None:
        """Regression: /search must not be captured by /{session_id}."""
        response = seeded.get("/api/messages/search?q=pedido")

        assert "items" in response.json()["data"]
        assert response.json()["data"]["total"] == 2
