FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies required by TTS and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (needed for sudachipy via spacy[ja])
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies with CPU-only PyTorch (saves ~1.5GB)
RUN uv sync --frozen --no-dev --no-install-project \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy source code
COPY src ./src

# Install the project
RUN uv sync --frozen --no-dev \
    --extra-index-url https://download.pytorch.org/whl/cpu

FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for torchaudio, Coqui TTS, and audio conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (required by editable install .pth file)
COPY --from=builder /app/src /app/src

# Copy default config
COPY config.yaml ./config.yaml

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"
ENV CONFIG_PATH="/app/config.yaml"

EXPOSE 8000

ENTRYPOINT ["python", "-m", "app.main"]
