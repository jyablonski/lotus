// Package testinfra provides shared test infrastructure for integration tests
// across the backend service. It is not a _test package so any test package
// can import it directly.
package testinfra

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
	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/pressly/goose/v3"
	goredis "github.com/redis/go-redis/v9"
	"github.com/riverqueue/river"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
	"github.com/testcontainers/testcontainers-go/modules/redis"
)

// TestDB holds all resources provisioned by Setup. Call Close when done.
type TestDB struct {
	Pool        *pgxpool.Pool
	ConnStr     string // plain connstr: sslmode=disable, no search_path
	RiverClient *river.Client[pgx.Tx]
	RedisClient *goredis.Client
	container   *postgres.PostgresContainer
	redisC      *redis.RedisContainer
}

// ConnStrWith returns a connection string with additional DSN options appended
// alongside sslmode=disable. Useful when a package needs e.g. search_path=source.
func (db *TestDB) ConnStrWith(ctx context.Context, opts ...string) (string, error) {
	return db.container.ConnectionString(ctx, append([]string{"sslmode=disable"}, opts...)...)
}

// Close shuts down the pgxpool, Redis client, and terminates containers.
func (db *TestDB) Close(ctx context.Context) {
	db.Pool.Close()
	if db.RedisClient != nil {
		db.RedisClient.Close()
	}
	db.container.Terminate(ctx) //nolint:errcheck
	if db.redisC != nil {
		db.redisC.Terminate(ctx) //nolint:errcheck
	}
}

// Setup starts a postgres:16-alpine container, waits for it, runs goose
// migrations from schemaDir, runs River migrations, and returns a TestDB
// with a pgxpool and insert-only River client ready for use.
func Setup(ctx context.Context, schemaDir string) (*TestDB, error) {
	pgContainer, err := postgres.Run(ctx,
		"pgvector/pgvector:pg16",
		postgres.WithDatabase("postgres"),
		postgres.WithUsername("postgres"),
		postgres.WithPassword("postgres"),
	)
	if err != nil {
		return nil, fmt.Errorf("start postgres container: %w", err)
	}

	connStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("get connection string: %w", err)
	}

	if err := waitForDB(connStr); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("wait for db: %w", err)
	}

	if err := applyGooseMigrations(connStr, schemaDir); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("apply schema: %w", err)
	}

	pool, err := pgxpool.New(ctx, connStr)
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("create pgxpool: %w", err)
	}

	if err := jobs.RunMigrations(ctx, pool, DiscardLogger()); err != nil {
		pool.Close()
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("run River migrations: %w", err)
	}

	riverClient, err := jobs.NewInsertOnlyClient(pool)
	if err != nil {
		pool.Close()
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("create River insert-only client: %w", err)
	}

	// ── Redis container ─────────────────────────────────────────────
	redisC, err := redis.Run(ctx, "redis:7-alpine")
	if err != nil {
		pool.Close()
		pgContainer.Terminate(ctx) //nolint:errcheck
		return nil, fmt.Errorf("start redis container: %w", err)
	}

	redisConnStr, err := redisC.ConnectionString(ctx)
	if err != nil {
		pool.Close()
		pgContainer.Terminate(ctx) //nolint:errcheck
		redisC.Terminate(ctx)      //nolint:errcheck
		return nil, fmt.Errorf("get redis connection string: %w", err)
	}

	redisOpts, err := goredis.ParseURL(redisConnStr)
	if err != nil {
		pool.Close()
		pgContainer.Terminate(ctx) //nolint:errcheck
		redisC.Terminate(ctx)      //nolint:errcheck
		return nil, fmt.Errorf("parse redis URL: %w", err)
	}

	redisClient := goredis.NewClient(redisOpts)

	return &TestDB{
		Pool:        pool,
		ConnStr:     connStr,
		RiverClient: riverClient,
		RedisClient: redisClient,
		container:   pgContainer,
		redisC:      redisC,
	}, nil
}

// ApplyExtraSQL reads a SQL file and executes it against the database.
// Used for test fixtures not covered by goose (e.g. dbt-managed schemas).
func ApplyExtraSQL(connStr, filePath string) error {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("read %s: %w", filePath, err)
	}
	db, err := sql.Open("pgx", connStr)
	if err != nil {
		return fmt.Errorf("open db: %w", err)
	}
	defer db.Close()
	if _, err := db.Exec(string(content)); err != nil {
		return fmt.Errorf("exec %s: %w", filePath, err)
	}
	return nil
}

// DiscardLogger returns a slog.Logger that discards all output.
// Use it in tests to suppress River and service log noise.
func DiscardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

// MockAnalyzerServer returns a test HTTP server that always responds 200 OK.
// The server is automatically closed via t.Cleanup.
func MockAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	t.Cleanup(srv.Close)
	return srv
}

// FailingAnalyzerServer returns a test HTTP server that always responds 500.
// The server is automatically closed via t.Cleanup.
func FailingAnalyzerServer(t *testing.T) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	t.Cleanup(srv.Close)
	return srv
}

func applyGooseMigrations(connStr, schemaDir string) error {
	db, err := sql.Open("pgx", connStr)
	if err != nil {
		return fmt.Errorf("open db: %w", err)
	}
	defer db.Close()

	goose.SetLogger(goose.NopLogger())
	if err := goose.SetDialect("postgres"); err != nil {
		return fmt.Errorf("set goose dialect: %w", err)
	}
	if err := goose.Up(db, schemaDir); err != nil {
		return fmt.Errorf("goose up: %w", err)
	}
	return nil
}

func waitForDB(connStr string) error {
	db, err := sql.Open("pgx", connStr)
	if err != nil {
		return err
	}
	defer db.Close()

	for i := 0; i < 20; i++ {
		if err := db.Ping(); err == nil {
			return nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return fmt.Errorf("postgres did not become ready after 10s")
}
