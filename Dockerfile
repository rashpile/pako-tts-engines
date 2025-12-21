FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src

# Install the project
RUN uv sync --frozen --no-dev

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy default config
COPY config.yaml ./config.yaml

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV CONFIG_PATH="/app/config.yaml"

EXPOSE 8000

ENTRYPOINT ["python", "-m", "app.main"]
