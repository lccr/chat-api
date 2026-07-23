"""Application factory.

Using a factory instead of a module-level singleton keeps the app easy to
instantiate with overridden dependencies in tests and avoids import-time
side effects.
"""

from fastapi import FastAPI

from app.api.deps import get_engine
from app.api.error_handlers import register_error_handlers
from app.api.routes.health import router as health_router
from app.api.routes.messages import router as messages_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import register_rate_limiting
from app.models.base import Base
from app.models.fts import create_fts_schema


def create_app() -> FastAPI:
    """Build and wire the FastAPI application."""
    settings = get_settings()
    configure_logging(debug=settings.debug)

    # Schema is created on startup; migrations are out of scope here.
    Base.metadata.create_all(bind=get_engine())
    create_fts_schema(get_engine())

    app = FastAPI(
        title=settings.app_name,
        description="RESTful API for chat message processing",
        version="0.1.0",
    )

    register_error_handlers(app)
    register_rate_limiting(app)
    app.include_router(health_router)
    app.include_router(messages_router)

    return app


app = create_app()
