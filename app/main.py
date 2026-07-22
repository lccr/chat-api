"""Application factory.

Using a factory instead of a module-level singleton keeps the app easy to
instantiate with overridden dependencies in tests and avoids import-time
side effects.
"""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Build and wire the FastAPI application."""
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        description="RESTful API for chat message processing",
        version="0.1.0",
    )

    register_error_handlers(app)
    app.include_router(health_router)

    return app


app = create_app()
