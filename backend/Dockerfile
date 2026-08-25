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

# Bake the sentence-transformer weights (~420 MB) into the image. Left to itself
# the app downloads them into ./cache on the first grading request, which needs
# both network access and a writable /app at runtime -- neither of which an
# unprivileged container has. Baking them also keeps the first request fast and
# stops a public deployment depending on the HuggingFace Hub being reachable.
RUN /app/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-mpnet-base-v2', cache_folder='./cache')"

# Copy compiled frontend build to static directory so FastAPI serves it
COPY --from=frontend-builder /frontend/dist ./static

# Run unprivileged. /app stays root-owned, so the app can read its code, venv and
# baked model but cannot modify any of them. UID/GID are build args so they can be
# matched to whoever owns a writable ./backend/data bind mount on the host; the
# demo deployment mounts that directory read-only and doesn't care.
ARG UID=1000
ARG GID=1000
RUN groupadd --gid "$GID" app \
    && useradd --uid "$UID" --gid "$GID" --create-home --shell /usr/sbin/nologin app

# Somewhere writable for the caches torch/transformers/matplotlib expect, none of
# which may live under the now read-only /app. HF_HUB_OFFLINE keeps the baked
# model from triggering any network lookup at all.
ENV HOME=/home/app \
    XDG_CACHE_HOME=/home/app/.cache \
    HF_HOME=/home/app/.cache/huggingface \
    TORCH_HOME=/home/app/.cache/torch \
    MPLCONFIGDIR=/home/app/.cache/matplotlib \
    HF_HUB_OFFLINE=1

USER app

# Expose FastAPI port
EXPOSE 8000

# Call the venv interpreter directly rather than `uv run`, which wants to write
# to the (root-owned) project directory to validate the environment.
CMD ["/app/.venv/bin/python", "main.py", "data"]
