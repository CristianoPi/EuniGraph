# Backend

The backend is a FastAPI-based modular monolith.

## Module Strategy

Application modules are organized by domain boundary first, with internal layering second:
- `application/`: use cases and orchestration
- `domain/`: domain models and rules
- `infrastructure/`: adapters for databases, files, and external services
- `interfaces/`: module-facing interfaces such as DTOs or facades

This layout keeps modules independently evolvable while preserving a single deployable unit for the MVP.

## Local Commands

- Install dependencies: `uv sync --group dev`
- Run the API: `uv run uvicorn eunigraph.main:app --reload`
- Run tests: `uv run pytest`
