.PHONY: install run-backend run-frontend build-frontend docker-up docker-down

# -----------------------------------------------------------------------------
# Tool Discovery
# -----------------------------------------------------------------------------

PYTHON := $(shell command -v uv >/dev/null 2>&1 && echo "uv run" || echo "python")
PIP := $(shell command -v uv >/dev/null 2>&1 && echo "uv sync" || echo "pip install .")
NPM := $(shell command -v bun >/dev/null 2>&1 && echo "bun" || echo "npm")

# -----------------------------------------------------------------------------
# Local Development
# -----------------------------------------------------------------------------

install:
	@echo "Installing backend dependencies..."
	cd backend && $(PIP)
	@echo "Downloading SpaCy model..."
	cd backend && $(PYTHON) -m spacy download en_core_web_md
	@echo "Installing frontend dependencies..."
	cd frontend && $(NPM) install

DATA_DIR ?= data

run-backend:
	cd backend && $(PYTHON) main.py $(DATA_DIR)

run-frontend:
	cd frontend && $(NPM) run dev

build-frontend:
	@echo "Building frontend..."
	cd frontend && $(NPM) run build
	@echo "Copying to backend/static..."
	rm -rf backend/static
	cp -r frontend/dist backend/static

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------

docker-up:
	DOCKER_BUILDKIT=1 docker compose up --build -d

docker-down:
	docker compose down
