# API contracts

- `GET /api/health` — liveness, database readiness, and mock-mode disclosure.
- `POST /api/datasets`, `GET /api/datasets` — create and list datasets.
- `POST /api/datasets/{id}/versions` — append an immutable dataset version.
- `GET /api/dataset-versions/{id}/examples` — preview a version.
- `POST /api/experiments`, `GET /api/experiments` — validate and store experiment configurations.
- `POST /api/experiments/{id}/runs` — enqueue an evaluation.
- `GET /api/runs`, `GET /api/runs/{id}`, `POST /api/runs/{id}/cancel` — status and cancellation.
- `GET /api/runs/{id}/results` — response/metric exploration with optional model and metric filters.
- `POST /api/annotations` — independent human judgment.
- `POST /api/analyses` — thresholded automated-vs-human reliability statistics.
- `GET /api/runs/{id}/export.csv|json` — reproducible raw exports.
- `GET /api/metrics/catalog` — input requirements and limitations.

FastAPI publishes the machine-readable OpenAPI schema at `/openapi.json`.

