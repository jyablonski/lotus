# Backend Load Tests

Load tests for the Lotus backend service using [k6](https://grafana.com/docs/k6/latest/). These tests target both the HTTP gateway (`:8080`) and the gRPC server (`:50051`) to measure performance under various load profiles.

## Tools

- **k6** — JavaScript-based load testing framework with built-in gRPC support
- **Docker Compose** — runs k6 alongside the backend and Postgres in an isolated e2e stack
- **GitHub Actions** — runs the HTTP smoke test automatically on PRs that touch `services/backend/`

## CI Pipeline

The `k6-smoke` job in `.github/workflows/backend.yaml` runs automatically on PRs that modify `services/backend/**`. It uses the same Docker Compose setup as local development, running k6 inside the Docker network so it can reach the backend directly at `http://backend:8080`.

**Steps:**

1. Checks out the repo (sparse checkout: `services/backend/`, `docker/`, `Makefile`)
2. Starts Postgres and the backend via `docker compose --profile load-test up -d --build --wait`
3. Runs the HTTP gateway smoke test via `docker compose --profile load-test run k6 run /scripts/http-gateway-load.js`
4. Dumps backend logs on failure for debugging
5. Tears down the stack

k6's `waitForReady()` function in `setup()` polls the backend until it responds before starting the test. If any threshold fails (e.g. error rate > 1% or p95 latency > 500ms), k6 exits with a non-zero code and the PR check fails.

## Test Scripts

| Script                           | Protocol | Description                                                                                                                 |
| -------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| `scripts/http-gateway-load.js`   | HTTP     | Tests the grpc-gateway endpoints: CreateUser, CreateJournal, GetJournals, GenerateRandomString                              |
| `scripts/grpc-load.js`           | gRPC     | Tests gRPC services directly, including TriggerJournalAnalysis (gRPC-only, no HTTP mapping)                                 |
| `scripts/full-stack-scenario.js` | HTTP     | Weighted user journey scenarios: new user onboarding (10%), returning user (60%), read-heavy (25%), OAuth registration (5%) |

## Load Profiles

All scripts accept a `PROFILE` env var to select the load level:

| Profile           | Executor              | Rate        | Duration | Max VUs |
| ----------------- | --------------------- | ----------- | -------- | ------- |
| `smoke` (default) | constant-arrival-rate | 1 req/s     | 30s      | 5       |
| `average`         | constant-arrival-rate | 10 req/s    | 2m       | 50      |
| `stress`          | ramping-arrival-rate  | 1→100 req/s | 3m       | 200     |

## Running in Docker Compose

Docker Compose spins up Postgres, the backend, and k6 together. The backend is built from `services/backend/Dockerfile` (a `FROM scratch` image), so there are no shell tools available inside it — readiness checking is handled by k6's `setup()` function instead of Docker healthchecks.

**Start the stack first** (only needed once per session):

```bash
docker compose -f docker/docker-compose-e2e.yaml --profile load-test up -d --build --wait postgres backend
```

**Then run any test:**

```bash
# HTTP gateway
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run /scripts/http-gateway-load.js
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run -e PROFILE=average /scripts/http-gateway-load.js
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run -e PROFILE=stress /scripts/http-gateway-load.js

# gRPC direct
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run /scripts/grpc-load.js
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run -e PROFILE=average /scripts/grpc-load.js

# Full-stack scenarios
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run /scripts/full-stack-scenario.js
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run -e PROFILE=average /scripts/full-stack-scenario.js
docker compose -f docker/docker-compose-e2e.yaml --profile load-test run k6 run -e PROFILE=stress /scripts/full-stack-scenario.js
```

**Tear down when finished:**

```bash
docker compose -f docker/docker-compose-e2e.yaml --profile load-test down -v
```

## Architecture Notes

- The backend uses **grpc-gateway** to translate HTTP requests to gRPC, so the HTTP tests exercise the same code paths as the gRPC tests (plus the gateway translation layer)
- The `GetUserJournalSummary` analytics endpoint is excluded from all load tests because it queries `gold.user_journal_summary`, a dbt-materialized view that does not exist in the e2e database
- The `TriggerJournalAnalysis` endpoint is only testable via gRPC — it has no HTTP mapping in the proto definitions
- The `third_party/` directory contains vendored `google/api` proto files needed by k6's gRPC client to parse the service proto imports (buf resolves these automatically at code generation time, but k6 needs them on disk)

## Directory Structure

```
load-tests/
├── lib/
│   ├── config.js       # Shared config: URLs, thresholds, executor presets
│   └── helpers.js      # Data generators, response checks, readiness polling
├── scripts/
│   ├── http-gateway-load.js      # HTTP gateway load test
│   ├── grpc-load.js              # Direct gRPC load test
│   └── full-stack-scenario.js    # Weighted multi-scenario test
└── third_party/
    └── google/api/               # Vendored google/api protos for k6 gRPC
        ├── annotations.proto
        └── http.proto
```
