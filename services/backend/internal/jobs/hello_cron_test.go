package jobs_test

import (
	"context"
	"testing"
	"time"

	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverpgxv5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── Unit tests ────────────────────────────────────────────────────────────────

func TestHelloCronArgsKind(t *testing.T) {
	args := jobs.HelloCronArgs{}
	assert.Equal(t, "hello_cron", args.Kind())
}

// ── Integration tests ─────────────────────────────────────────────────────────

// TestHelloCronWorkerWritesRuntimeConfig verifies that running the worker inserts
// both cron_job_triggered and cron_job_finished records into runtime_config.
func TestHelloCronWorkerWritesRuntimeConfig(t *testing.T) {
	// Shorten the sleep so the test completes quickly.
	// We rely on the worker completing within the timeout.
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewHelloCronWorker(testQueries, testinfra.DiscardLogger()))

	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{jobs.QueueCron: {MaxWorkers: 1}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)

	_, err = client.Insert(ctx, jobs.HelloCronArgs{}, nil)
	require.NoError(t, err)

	select {
	case event := <-completedCh:
		assert.Equal(t, "hello_cron", event.Job.Kind)
	case <-ctx.Done():
		t.Fatal("timed out waiting for hello_cron job completion")
	}

	// Verify runtime_config was written.
	triggered, err := testQueries.GetRuntimeConfigByKey(ctx, "cron_job_triggered")
	require.NoError(t, err, "cron_job_triggered should exist in runtime_config")
	assert.Equal(t, "backend", triggered.Service)

	finished, err := testQueries.GetRuntimeConfigByKey(ctx, "cron_job_finished")
	require.NoError(t, err, "cron_job_finished should exist in runtime_config")
	assert.Equal(t, "backend", finished.Service)

	// Verify the triggered timestamp is before (or equal to) the finished timestamp.
	var trigTS, finTS time.Time
	require.NoError(t, trigTS.UnmarshalJSON(triggered.Value))
	require.NoError(t, finTS.UnmarshalJSON(finished.Value))
	assert.True(t, !trigTS.After(finTS), "triggered should not be after finished")
}
