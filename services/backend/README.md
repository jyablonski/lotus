# Backend Service

Go gRPC backend with a grpc-gateway HTTP surface, sqlc-generated PostgreSQL access, River background jobs, Redis-backed caching, and testcontainers-based integration tests.

## Development

Common commands from the repository root:

```bash
make sqlc-generate
make buf-generate
make moq-generate
```

Or from this directory:

```bash
go test ./...
go test -v ./internal/grpc
go test -v ./internal/jobs
```

Generated files live under `internal/db`, `internal/pb`, and `internal/mocks`. Do not edit generated files directly.

## Test Infrastructure

Shared integration test infrastructure lives in `internal/testinfra`.

`testinfra.Setup(ctx, schemaDir)` starts:

- PostgreSQL via `pgvector/pgvector:pg16`
- goose migrations from `internal/sql/schema`
- River migrations and an insert-only River client
- Redis via `redis:7-alpine`

It returns a `*testinfra.TestDB` with:

- `Pool *pgxpool.Pool`
- `ConnStr string`
- `RiverClient *river.Client[pgx.Tx]`
- `RedisClient *redis.Client`

Most gRPC integration tests use the package-level `TestMain` in `internal/grpc/testmain_test.go`, then call `newTestCtx(t)` from `internal/grpc/testhelpers_test.go`. `newTestCtx(t)` opens a fresh pgx transaction, wraps it with `db.New(tx)`, injects the query object into context, and rolls the transaction back in `t.Cleanup`.

Use `newDirectQueries(t)` only when the code under test commits outside the test transaction and the test needs to observe committed rows.

## Test Fixtures

Database fixture helpers live in `internal/testfixtures`.

Use them for DB setup in integration tests instead of hand-writing `Create*Params`, upsert params, or raw inserts for supported models:

```go
user := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUser{})
journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{
    UserID:      user.ID,
    JournalText: "A test journal entry",
    MoodScore:   testfixtures.Int32Ptr(7),
})
```

Supported models:

- `db.SourceUser`
- `db.SourceJournal`
- `db.SourceUserGameBalance`
- `db.SourceUserGameBet`
- `db.SourceJournalExport`
- `db.SourceJournalCommunityProjection`
- `db.SourceCommunityThemeRollup`
- `db.SourceCommunityMoodRollup`
- `db.SourceCommunitySummary`
- `db.SourceCommunityPromptSet`
- `db.SourceRuntimeConfig`

The main helpers are:

- `BuildDefaultModel(t, model)` - returns a valid default model without persisting it
- `Create(t, ctx, queries, model)` - persists an already-populated supported model
- `CreateWithDefaults(t, ctx, queries, model, fieldsToEmpty...)` - fills defaults, merges non-zero fields, resolves supported foreign keys, then persists

`fieldsToEmpty` uses Go struct field names and is validated. Use it when a default is normally non-zero but the test needs the zero value:

```go
journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{}, "MoodScore")
```

Foreign key behavior:

- `SourceJournal`, game records, journal exports, and journal community projections create a parent user or journal when required IDs are omitted.
- If an FK is supplied, the helper respects it and does not create an extra parent.

Value conventions:

- Unique fields use UUID suffixes for parallel-test safety.
- Community rollup `DeltaVsPrevious` defaults to invalid/NULL. Pass `testfixtures.Numeric(t, "0")` when a test needs a real numeric zero.
- Do not add faker/randomness to deterministic assertions. Prefer explicit values for ordering, ranking, embeddings, rollups, and enum-like fields.

Unsupported models should fail at compile time where possible because the helper API is constrained to supported fixture models. Add sqlc insert/upsert queries before adding fixture support for new persisted models.

## Test Style

- Unit tests should use moq mocks and explicit generated params when those params are part of the behavior being asserted.
- Integration tests should use `testfixtures` for supported setup rows.
- Raw SQL in tests is acceptable for unsupported models or specialized database types, such as `journal_sentiments`, `journal_topics`, and pgvector embeddings.
- Validation-only tests should use `context.Background()` and avoid DB setup.
- Tests that need River dependencies should use `withRiverDeps(ctx)`.
- Tests that need analyzer HTTP behavior should use `testinfra.MockAnalyzerServer(t)` or `testinfra.FailingAnalyzerServer(t)`.
