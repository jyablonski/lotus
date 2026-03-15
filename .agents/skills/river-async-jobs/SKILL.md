---
name: river-async-jobs
description: Step-by-step workflow for adding a new River background job or periodic cron task to the Go backend service.
---

## Pattern

Every job needs two things, then one wiring step:

**1. New file in `services/backend/internal/jobs/`** — e.g. `send_email.go`:

- `Args` struct with `Kind() string` and optional `InsertOpts() river.InsertOpts` (set `Queue` and `MaxAttempts`)
- `Worker` struct embedding `river.WorkerDefaults[Args]` with deps as fields
- `Work(ctx, job)` method — return an error to trigger retry

**2. Register in `jobs.go` `NewClientWithPeriodicInterval`**:

- `river.AddWorker(workers, NewMyWorker(...))`
- For periodic jobs, add a `river.NewPeriodicJob(...)` entry with `&river.PeriodicJobOpts{RunOnStart: true}`

**3. Enqueue from any gRPC handler**:

- `riverClient.Insert(ctx, MyArgs{...}, nil)` — async, returns immediately
- `riverClient.InsertTx(ctx, tx, MyArgs{...}, nil)` — atomic with a DB write (use for CreateX handlers)

## Queues

- `river.QueueDefault` — general purpose (50 workers)
- `jobs.QueueAnalysis` — analyzer HTTP calls (10 workers)
- `jobs.QueueCron` — periodic jobs (5 workers)

## Rules

- Workers hold their own deps (httpClient, logger, queries) as struct fields — they run outside gRPC context
- `InsertTx` guarantees the job is rolled back if the transaction rolls back
- Tests: use `jobs.NewInsertOnlyClient(testPgxPool)` to enqueue without processing; use a full client with `Subscribe(EventKindJobCompleted)` to test worker execution
