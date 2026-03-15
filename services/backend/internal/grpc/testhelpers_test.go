package grpc_test

import (
	"context"
	"database/sql"
	"net/http"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/testinfra"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/require"
)

// withRiverDeps adds a pgxpool and an insert-only River client to the context.
// Required for tests that call CreateJournal, which now uses pgx for the journal insert.
func withRiverDeps(ctx context.Context) context.Context {
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRiverClient(ctx, testRiverClient)
	return ctx
}

// newDirectQueries opens a direct (non-transaction) connection to the test DB.
// Use this to verify rows committed by CreateJournal (which commits its own pgx tx).
func newDirectQueries(t *testing.T) *db.Queries {
	t.Helper()
	conn, err := sql.Open("postgres", testDBConnStr)
	require.NoError(t, err)
	t.Cleanup(func() { conn.Close() })
	return db.New(conn)
}

// newTestCtx opens a transaction against the test container DB and registers
// t.Cleanup to roll it back and close the connection. Each test gets a clean
// snapshot without any truncation — rollback discards all writes on exit.
// testDBConnStr is set by TestMain in testmain_test.go.
func newTestCtx(t *testing.T) (context.Context, *db.Queries) {
	t.Helper()
	dbConn, err := sql.Open("postgres", testDBConnStr)
	require.NoError(t, err)

	tx, err := dbConn.BeginTx(context.Background(), nil)
	require.NoError(t, err)

	t.Cleanup(func() {
		tx.Rollback() //nolint:errcheck
		dbConn.Close()
	})

	queries := db.New(tx) // sqlc's New() accepts DBTX — both *sql.DB and *sql.Tx satisfy it
	logger := testinfra.DiscardLogger()
	ctx := inject.WithDB(context.Background(), queries)
	ctx = inject.WithLogger(ctx, logger)
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
	user, err := queries.CreateUserOauth(context.Background(), db.CreateUserOauthParams{
		Email:         email,
		OauthProvider: sql.NullString{String: "test", Valid: true},
	})
	require.NoError(t, err)
	return user.ID
}
