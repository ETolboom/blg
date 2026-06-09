# Stage 1: Build the Vue.js frontend with Bun
FROM oven/bun:alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY frontend/ .
RUN bun run build

# Stage 2: Final runtime image (FastAPI + Static Frontend)
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim
WORKDIR /app

ENV UV_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies (generating uv.lock if missing)
COPY backend/pyproject.toml backend/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Install the project into the virtual environment
COPY backend/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Download spacy model into the virtual environment AFTER all syncs so uv doesn't uninstall it
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run spacy download en_core_web_md

# Copy compiled frontend build to static directory so FastAPI serves it
COPY --from=frontend-builder /frontend/dist ./static

# Expose FastAPI port
EXPOSE 8000

# Using uv run automatically uses the .venv
CMD ["uv", "run", "main.py", "data"]
