# Modules

Each module is isolated by domain boundary and follows the same internal structure:

- `application/`: use cases and orchestration
- `domain/`: entities, value objects, invariants
- `infrastructure/`: technical adapters
- `interfaces/`: input/output contracts for the rest of the monolith

The goal is to keep dependencies directional and make future extraction into services feasible without forcing microservice complexity into the MVP.
