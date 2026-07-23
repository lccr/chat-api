"""test health check endpoint"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_health_check(client: TestClient) -> None:
    """The health check endpoint returns a 200 response with the expected body."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": {"service": "chat-api", "status": "ok"}}
