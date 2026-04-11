PROJECT_NAME := EuniGraph

.PHONY: help bootstrap up down logs backend-install backend-run backend-test backend-lint backend-format backend-typecheck

help:
	@echo "Available targets:"
	@echo "  bootstrap         Copy .env.example to .env if missing"
	@echo "  up                Start local services with Docker Compose"
	@echo "  down              Stop local services"
	@echo "  logs              Tail Docker Compose logs"
	@echo "  backend-install   Install backend dependencies with uv"
	@echo "  backend-run       Run the FastAPI app locally"
	@echo "  backend-test      Run backend tests"
	@echo "  backend-lint      Run Ruff checks"
	@echo "  backend-format    Run Ruff formatter"
	@echo "  backend-typecheck Run mypy"

bootstrap:
	./scripts/bootstrap.sh

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-install:
	cd backend && uv sync --group dev

backend-run:
	cd backend && uv run uvicorn eunigraph.main:app --host 0.0.0.0 --port 8000 --reload

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check src tests

backend-format:
	cd backend && uv run ruff format src tests

backend-typecheck:
	cd backend && uv run mypy src
