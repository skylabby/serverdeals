# ──────────────────────────────────────────────────────────────────────────────
# ServerDeals — Multi-stage Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
#  Stage 1: Builder  — installs Python dependencies into a venv.
#  Stage 2: Runtime  — copies the venv + application code, runs uvicorn.
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS builder

# Avoid writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install only build essentials needed to compile asyncpg (psycopg2 psutil, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create and activate a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Runtime stage ───────────────────────────────────────────────────────────

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Only the shared libraries needed by asyncpg at runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code and Alembic configuration
COPY backend/ ./backend/
COPY alembic.ini .

# Default port for uvicorn
EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
