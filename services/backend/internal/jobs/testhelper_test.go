package jobs_test

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/jyablonski/lotus/internal/testinfra"
	_ "github.com/lib/pq"
	"github.com/riverqueue/river"
)

// package-level test state set by TestMain.
var (
	testPgxPool     *pgxpool.Pool
	testSQLDB       *sql.DB
	testQueries     *db.Queries
	testRiverClient *river.Client[pgx.Tx]
)

func TestMain(m *testing.M) {
	ctx := context.Background()

	testDB, err := testinfra.Setup(ctx, "../sql/schema")
	if err != nil {
		fmt.Fprintf(os.Stderr, "testinfra setup: %v\n", err)
		os.Exit(1)
	}

	testPgxPool = testDB.Pool
	testRiverClient = testDB.RiverClient

	testSQLDB, err = sql.Open("postgres", testDB.ConnStr)
	if err != nil {
		testDB.Close(ctx)
		fmt.Fprintf(os.Stderr, "failed to open sql.DB: %v\n", err)
		os.Exit(1)
	}
	testQueries = db.New(testSQLDB)

	code := m.Run()
	testSQLDB.Close()
	testDB.Close(ctx)
	os.Exit(code)
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
