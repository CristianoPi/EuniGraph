FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    python3 \
    python3-dev \
    python3-graph-tool \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --break-system-packages uv

WORKDIR /app

COPY backend /app/backend

RUN python3 -m venv /opt/venv
RUN uv pip install --python /opt/venv/bin/python -e /app/backend

WORKDIR /app/backend

EXPOSE 8000
