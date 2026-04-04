package grpc_test

import (
	"context"
	"net/http"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/stretchr/testify/require"
)

// withRiverDeps adds a pgxpool and an insert-only River client to the context.
// Required for tests that call CreateJournal, which now uses pgx for the journal insert.
func withRiverDeps(ctx context.Context) context.Context {
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRiverClient(ctx, testRiverClient)
	return ctx
}

// newDirectQueries returns sqlc queries on the shared test pool (non-transactional).
// Use this to verify rows committed by CreateJournal (which commits its own pgx tx).
func newDirectQueries(t *testing.T) *db.Queries {
	t.Helper()
	return db.New(testPgxPool)
}

// newTestCtx begins a pgx transaction and registers t.Cleanup to roll it back.
// Each test gets a clean snapshot without truncation — rollback discards all writes on exit.
// testDBConnStr is set by TestMain in testmain_test.go.
func newTestCtx(t *testing.T) (context.Context, *db.Queries) {
	t.Helper()
	tx, err := testPgxPool.Begin(context.Background())
	require.NoError(t, err)

	t.Cleanup(func() {
		_ = tx.Rollback(context.Background())
	})

	queries := db.New(tx)
	logger := testinfra.DiscardLogger()
	ctx := inject.WithDB(context.Background(), queries)
	ctx = inject.WithLogger(ctx, logger)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	return ctx, queries
}

// withAnalyzer adds an HTTP client and analyzer URL to the context.
func withAnalyzer(ctx context.Context, url string) context.Context {
	ctx = inject.WithHTTPClient(ctx, http.DefaultClient)
	return inject.WithAnalyzerURL(ctx, url)
}

// createTestUser inserts a minimal OAuth user and returns its ID.
// The insert runs within the test's transaction and is rolled back on cleanup.
func createTestUser(t *testing.T, queries *db.Queries) uuid.UUID {
	t.Helper()
	email := "test-" + uuid.New().String() + "@test.example"
	provider := "test"
	user, err := queries.CreateUserOauth(context.Background(), db.CreateUserOauthParams{
		Email:         email,
		OauthProvider: &provider,
	})
	require.NoError(t, err)
	return uuid.UUID(user.ID.Bytes)
}
