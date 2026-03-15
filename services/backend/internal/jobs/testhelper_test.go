package jobs_test

import (
	"context"
	"database/sql"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/pressly/goose/v3"
	"github.com/riverqueue/river"
	"github.com/testcontainers/testcontainers-go/modules/postgres"

	_ "github.com/lib/pq"
)

// package-level test state set by TestMain.
var (
	testPgxPool *pgxpool.Pool
	testSQLDB   *sql.DB
	testQueries *db.Queries
)

func TestMain(m *testing.M) {
	ctx := context.Background()

	pgContainer, err := postgres.Run(ctx,
		"postgres:16-alpine",
		postgres.WithDatabase("postgres"),
		postgres.WithUsername("postgres"),
		postgres.WithPassword("postgres"),
	)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to start postgres container: %v\n", err)
		os.Exit(1)
	}

	plainConnStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to get container connection string: %v\n", err)
		os.Exit(1)
	}

	if err := waitForDB(plainConnStr); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "postgres never became ready: %v\n", err)
		os.Exit(1)
	}

	if err := applySchema(plainConnStr); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to apply schema: %v\n", err)
		os.Exit(1)
	}

	// pgxpool for River
	testPgxPool, err = pgxpool.New(ctx, plainConnStr)
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to create pgxpool: %v\n", err)
		os.Exit(1)
	}

	// Run River migrations using a discard logger so test output stays clean.
	if err := jobs.RunMigrations(ctx, testPgxPool, discardLogger()); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to run River migrations: %v\n", err)
		os.Exit(1)
	}

	// sql.DB + Queries for workers that use sqlc
	testSQLDB, err = sql.Open("postgres", plainConnStr)
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to open sql.DB: %v\n", err)
		os.Exit(1)
	}
	testQueries = db.New(testSQLDB)

	code := m.Run()

	testPgxPool.Close()
	testSQLDB.Close()
	if err := pgContainer.Terminate(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "failed to terminate postgres container: %v\n", err)
	}

	os.Exit(code)
}

// applySchema runs goose migrations against the test database.
// No extras.sql needed — jobs tests only use source.* tables and River's own tables.
func applySchema(connStr string) error {
	sqlDB, err := sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("open db: %w", err)
	}
	defer sqlDB.Close()

	goose.SetLogger(goose.NopLogger())
	if err := goose.SetDialect("postgres"); err != nil {
		return fmt.Errorf("set goose dialect: %w", err)
	}
	if err := goose.Up(sqlDB, "../sql/schema"); err != nil {
		return fmt.Errorf("goose up: %w", err)
	}

	return nil
}

func waitForDB(connStr string) error {
	sqlDB, err := sql.Open("postgres", connStr)
	if err != nil {
		return err
	}
	defer sqlDB.Close()

	for i := 0; i < 20; i++ {
		if err := sqlDB.Ping(); err == nil {
			return nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return fmt.Errorf("postgres did not become ready after 10s")
}

// newInsertOnlyClient returns a River client that can enqueue jobs but does not process them.
func newInsertOnlyClient(t *testing.T) *river.Client[pgx.Tx] {
	t.Helper()
	client, err := jobs.NewInsertOnlyClient(testPgxPool)
	if err != nil {
		t.Fatalf("NewInsertOnlyClient: %v", err)
	}
	return client
}

// newAnalyzerServer returns a test HTTP server that always responds 200.
func newAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	t.Cleanup(srv.Close)
	return srv
}

// newFailingAnalyzerServer returns a test HTTP server that always responds 500.
func newFailingAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	t.Cleanup(srv.Close)
	return srv
}

// discardLogger returns a logger that discards all output.
func discardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}
