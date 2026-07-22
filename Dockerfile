# syntax=docker/dockerfile:1

# --- Build stage: install dependencies into a virtual environment ---------
FROM python:3.12-slim AS builder

WORKDIR /app

# Create an isolated virtualenv we can copy wholesale into the final image.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only production dependencies (dev tools stay out of the image).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Runtime stage: minimal image with just the app and its venv ----------
FROM python:3.12-slim AS runtime

# Run as a non-root user: a container process should never be root.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Bring the ready-made virtualenv from the builder; no build tools here.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the application package, nothing else.
COPY --chown=appuser:appuser app ./app

# Data directory owned by the non-root user, for the SQLite file.
# Note: this lives in the container's ephemeral filesystem — see ADR-0004.
# A persistent deployment would mount a volume here or use a managed database.
RUN mkdir -p /data && chown appuser:appuser /data
ENV APP_DATABASE_URL="sqlite:////data/chat_data.db"

USER appuser

EXPOSE 8000

# Liveness check the orchestrator can use.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]