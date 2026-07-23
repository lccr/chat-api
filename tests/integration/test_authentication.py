"""Integration tests for API-key authentication.

Authentication is opt-in: with no configured key it is disabled (the default
in the rest of the suite). These tests override the settings dependency to
enable it and verify both the rejection and the success paths.
"""

import pytest
from app.core.config import Settings, get_settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

API_KEY = "test-key-123"


@pytest.fixture()
def secured_client(app: FastAPI) -> TestClient:
    """A client against an app with API-key authentication enabled."""

    def override_settings() -> Settings:
        return Settings(api_key=API_KEY)

    app.dependency_overrides[get_settings] = override_settings
    return TestClient(app, raise_server_exceptions=False)


class TestApiKeyAuthentication:
    """Protected endpoints require a valid X-API-Key header."""

    def test_request_without_key_is_rejected(self, secured_client: TestClient) -> None:
        response = secured_client.get("/api/messages/s1")

        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "UNAUTHORIZED"

    def test_request_with_wrong_key_is_rejected(self, secured_client: TestClient) -> None:
        response = secured_client.get(
            "/api/messages/s1", headers={"X-API-Key": "wrong-key"}
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

    def test_request_with_valid_key_succeeds(self, secured_client: TestClient) -> None:
        response = secured_client.get(
            "/api/messages/s1", headers={"X-API-Key": API_KEY}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_health_endpoint_is_not_protected(self, secured_client: TestClient) -> None:
        """Infrastructure probes must not require authentication."""
        response = secured_client.get("/health")

        assert response.status_code == 200

    def test_disabled_auth_allows_requests_without_key(self, client: TestClient) -> None:
        """With no key configured (default fixture), auth is bypassed."""
        response = client.get("/api/messages/s1")

        assert response.status_code == 200
