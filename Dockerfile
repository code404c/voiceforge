FROM nvidia/cuda:12.6.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3-pip \
    libsndfile1 ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv sync --no-dev

# Default voices directory
ENV VOICEFORGE_VOICES_DIR=/data/voices

ENTRYPOINT ["uv", "run", "voiceforge"]
CMD ["--help"]
