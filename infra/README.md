# Infrastructure Baseline (Phase 0)

This folder contains **infrastructure and deployment** artifacts for the backend/ML monorepo.

## Environments

Environment templates live in `env/`:

- `env/local.env.example`
- `env/staging.env.example`
- `env/production.env.example`

**No secrets are committed**. For each environment, copy the appropriate example and inject values via your deployment system (CI/CD, container orchestrator, secret manager).

## Services

Each service is independently deployable and contains:

- `pyproject.toml` + `poetry.lock` (dependency lock per service)
- `Dockerfile` (multi-stage; no dev dependencies in final image)
- `src/<service_package>/...`

Services (top-level):

- `ingestion/`
- `processing/`
- `ml/`
- `agents/`
- `api/`




