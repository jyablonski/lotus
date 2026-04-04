package grpc_test

import (
	"context"
	"fmt"
	"os"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/testinfra"
	goredis "github.com/redis/go-redis/v9"
	"github.com/riverqueue/river"
)

// testDBConnStr is set once by TestMain and used by newTestCtx in all integration tests.
var (
	testDBConnStr   string
	testPgxPool     *pgxpool.Pool
	testRiverClient *river.Client[pgx.Tx] // insert-only; not started
	testRedisClient *goredis.Client
)

func TestMain(m *testing.M) {
	ctx := context.Background()

	testDB, err := testinfra.Setup(ctx, "../sql/schema")
	if err != nil {
		fmt.Fprintf(os.Stderr, "testinfra setup: %v\n", err)
		os.Exit(1)
	}

	// testDBConnStr pins search_path=source so sqlc queries resolve table names correctly.
	testDBConnStr, err = testDB.ConnStrWith(ctx, "search_path=source")
	if err != nil {
		testDB.Close(ctx)
		fmt.Fprintf(os.Stderr, "get search_path connstr: %v\n", err)
		os.Exit(1)
	}

	// Apply extras not covered by goose (e.g. dbt-managed schemas).
	if err := testinfra.ApplyExtraSQL(testDB.ConnStr, "testdata/extras.sql"); err != nil {
		testDB.Close(ctx)
		fmt.Fprintf(os.Stderr, "apply extras.sql: %v\n", err)
		os.Exit(1)
	}

	testPgxPool = testDB.Pool
	testRiverClient = testDB.RiverClient
	testRedisClient = testDB.RedisClient

	code := m.Run()
	testDB.Close(ctx)
	os.Exit(code)
}
