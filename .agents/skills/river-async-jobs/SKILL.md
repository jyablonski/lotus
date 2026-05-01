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

## Testing

- Package tests use `testinfra.Setup(ctx, "../sql/schema")` from `services/backend/internal/testinfra` to start Postgres, apply goose migrations, run River migrations, and start Redis.
- Use `jobs.NewInsertOnlyClient(testPgxPool)` or the shared `newInsertOnlyClient(t)` helper to enqueue without processing.
- Use a full River client with `Subscribe(EventKindJobCompleted)` or `Subscribe(EventKindJobFailed)` to test worker execution.
- Use `internal/testfixtures` for supported setup rows instead of hand-writing sqlc params. For example:

```go
q := db.New(testPgxPool)
user := testfixtures.CreateWithDefaults(t, ctx, q, db.SourceUser{})
journal := testfixtures.CreateWithDefaults(t, ctx, q, db.SourceJournal{
    UserID:      user.ID,
    JournalText: "entry to analyze",
    MoodScore:   testfixtures.Int32Ptr(5),
})
```

- Raw SQL is still fine for unsupported analysis tables such as `source.journal_sentiments` and `source.journal_topics`.
- When verifying `InsertTx`, create the DB row and River job in the same pgx transaction, then assert both appear only after commit.
