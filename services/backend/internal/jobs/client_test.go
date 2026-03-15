package jobs_test

import (
	"context"
	"net/http"
	"testing"
	"time"

	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/riverqueue/river"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewClientStartStop verifies the River client starts and stops cleanly.
func TestNewClientStartStop(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	analyzerSrv := testinfra.MockAnalyzerServer(t)

	client, err := jobs.NewClient(
		testPgxPool,
		testQueries,
		http.DefaultClient,
		analyzerSrv.URL,
		testinfra.DiscardLogger(),
	)
	require.NoError(t, err)
	require.NotNil(t, client)

	require.NoError(t, client.Start(ctx))

	stopCtx, stopCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer stopCancel()
	require.NoError(t, client.Stop(stopCtx))
}

// TestNewClientWorkersRegistered verifies inserting each known job kind succeeds.
func TestNewClientWorkersRegistered(t *testing.T) {
	ctx := context.Background()
	analyzerSrv := testinfra.MockAnalyzerServer(t)

	client, err := jobs.NewClient(
		testPgxPool,
		testQueries,
		http.DefaultClient,
		analyzerSrv.URL,
		testinfra.DiscardLogger(),
	)
	require.NoError(t, err)

	_, err = client.Insert(ctx, jobs.AnalyzeEntryArgs{
		EntryID: 300,
		UserID:  "00000000-0000-0000-0000-000000000001",
		Content: "client test",
	}, nil)
	require.NoError(t, err, "should be able to insert AnalyzeEntryArgs")

	_, err = client.Insert(ctx, jobs.HelloCronArgs{}, nil)
	require.NoError(t, err, "should be able to insert HelloCronArgs")
}

// TestNewInsertOnlyClient verifies the insert-only client can enqueue jobs.
func TestNewInsertOnlyClient(t *testing.T) {
	ctx := context.Background()

	client, err := jobs.NewInsertOnlyClient(testPgxPool)
	require.NoError(t, err)
	require.NotNil(t, client)

	result, err := client.Insert(ctx, jobs.AnalyzeEntryArgs{
		EntryID: 400,
		UserID:  "00000000-0000-0000-0000-000000000001",
		Content: "insert only test",
	}, nil)
	require.NoError(t, err)
	assert.NotNil(t, result.Job)
}

// TestPeriodicJobConfigured verifies hello_cron fires when configured with a short interval.
func TestPeriodicJobConfigured(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	analyzerSrv := testinfra.MockAnalyzerServer(t)

	// 2-second interval so we don't wait 15 minutes in CI.
	client, err := jobs.NewClientWithPeriodicInterval(
		testPgxPool,
		testQueries,
		http.DefaultClient,
		analyzerSrv.URL,
		testinfra.DiscardLogger(),
		2*time.Second,
	)
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)

	deadline := time.After(45 * time.Second)
	for {
		select {
		case event := <-completedCh:
			if event.Job.Kind == "hello_cron" {
				return
			}
		case <-deadline:
			t.Fatal("timed out waiting for periodic hello_cron job")
		}
	}
}
