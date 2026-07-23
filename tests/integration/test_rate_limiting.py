"""Integration tests for application-level rate limiting.

Rate limiting is opt-in: with no configured limit it is effectively disabled,
which is the default across the suite. This verifies the limiter does not
interfere when disabled;.
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_requests_are_allowed_when_limiting_is_disabled(client: TestClient) -> None:
    """With no configured limit, repeated requests are not throttled."""
    for _ in range(5):
        response = client.get("/api/messages/sess-a")
        assert response.status_code == 200