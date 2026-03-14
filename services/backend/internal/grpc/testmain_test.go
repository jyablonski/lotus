package grpc_test

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"
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
		postgres.WithInitScripts("testdata/schema.sql"),
	)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to start postgres container: %v\n", err)
		os.Exit(1)
	}

	connStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable", "search_path=source")
	if err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "failed to get container connection string: %v\n", err)
		os.Exit(1)
	}

	testDBConnStr = connStr

	// Wait until postgres is truly ready to accept connections (init scripts may
	// still be running after the module's built-in wait strategy fires).
	if err := waitForDB(connStr); err != nil {
		pgContainer.Terminate(ctx) //nolint:errcheck
		fmt.Fprintf(os.Stderr, "postgres never became ready: %v\n", err)
		os.Exit(1)
	}

	code := m.Run()

	if err := pgContainer.Terminate(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "failed to terminate postgres container: %v\n", err)
	}

	os.Exit(code)
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
