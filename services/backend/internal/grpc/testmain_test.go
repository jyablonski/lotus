package grpc_test

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"
	"github.com/pressly/goose/v3"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
)

// testDBConnStr is set once by TestMain and used by newTestCtx in all integration tests.
var testDBConnStr string

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

	// plainConnStr has no search_path override — used for goose and schema bootstrapping
	// so that DDL runs in the default search path before source schema exists.
	plainConnStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to get container connection string: %v\n", err)
		os.Exit(1)
	}

	// testDBConnStr pins search_path=source so sqlc queries resolve table names correctly.
	testDBConnStr, err = pgContainer.ConnectionString(ctx, "sslmode=disable", "search_path=source")
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

	code := m.Run()

	if err := pgContainer.Terminate(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "failed to terminate postgres container: %v\n", err)
	}

	os.Exit(code)
}

// applySchema runs goose migrations then applies any extras not covered by goose.
func applySchema(connStr string) error {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("open db: %w", err)
	}
	defer db.Close()

	goose.SetLogger(goose.NopLogger())
	if err := goose.SetDialect("postgres"); err != nil {
		return fmt.Errorf("set goose dialect: %w", err)
	}
	// ../sql/schema is relative to the test package directory (internal/grpc/).
	if err := goose.Up(db, "../sql/schema"); err != nil {
		return fmt.Errorf("goose up: %w", err)
	}

	// Apply extras not covered by goose (e.g. dbt-managed schemas).
	extras, err := os.ReadFile("testdata/extras.sql")
	if err != nil {
		return fmt.Errorf("read extras.sql: %w", err)
	}
	if _, err := db.Exec(string(extras)); err != nil {
		return fmt.Errorf("apply extras.sql: %w", err)
	}

	return nil
}

// waitForDB pings the database up to 20 times with 500ms gaps.
func waitForDB(connStr string) error {
	db, err := sql.Open("postgres", connStr)
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
