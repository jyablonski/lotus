package grpc_test

import (
	"context"
	"database/sql"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/require"
)

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
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	ctx := inject.WithDB(context.Background(), queries)
	ctx = inject.WithLogger(ctx, logger)
	return ctx, queries
}

// withAnalyzer adds an HTTP client and analyzer URL to the context.
func withAnalyzer(ctx context.Context, url string) context.Context {
	ctx = inject.WithHTTPClient(ctx, http.DefaultClient)
	return inject.WithAnalyzerURL(ctx, url)
}

// mockAnalyzerServer returns a test server that always responds 200 OK.
// The server is automatically closed via t.Cleanup.
func mockAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"success": true, "message": "Analysis completed"}`))
	}))
	t.Cleanup(srv.Close)
	return srv
}

// failingAnalyzerServer returns a test server that always responds 500.
// The server is automatically closed via t.Cleanup.
func failingAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"error": "Analysis failed"}`))
	}))
	t.Cleanup(srv.Close)
	return srv
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
