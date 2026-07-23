"""Rate limiting setup.

Application-level rate limiting as defense in depth. In production this would
sit in front of the application (API gateway, load balancer or reverse proxy),
where abusive requests are rejected before consuming application resources.
"""

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.core.exceptions import RateLimitExceededError

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[get_settings().rate_limit] if get_settings().rate_limit else [],
    enabled=bool(get_settings().rate_limit),
)

def default_limit() -> str:
    """Return the configured rate limit, or an effectively unlimited value."""
    return get_settings().rate_limit or "1000/second"

async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> None:
    """Translate slowapi's exception into the project's domain error."""
    raise RateLimitExceededError(
        message="Rate limit exceeded",
        details=f"Limit: {exc.detail}",
    )


def register_rate_limiting(app: FastAPI) -> None:
    """Attach the limiter and its exception handler to the application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]


