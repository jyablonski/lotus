package jobs_test

import (
	"context"
	"net/http"
	"testing"
	"time"

	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverpgxv5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Unit tests

func TestAnalyzeEntryArgsKind(t *testing.T) {
	assert.Equal(t, "analyze_entry", jobs.AnalyzeEntryArgs{}.Kind())
}

func TestAnalyzeEntryArgsInsertOpts(t *testing.T) {
	opts := jobs.AnalyzeEntryArgs{}.InsertOpts()
	assert.Equal(t, jobs.QueueAnalysis, opts.Queue)
	assert.Equal(t, 5, opts.MaxAttempts)
}

// Integration tests

// TestAnalyzeEntryInsertTx verifies a journal row and job are committed together.
func TestAnalyzeEntryInsertTx(t *testing.T) {
	ctx := context.Background()
	client := newInsertOnlyClient(t)

	tx, err := testPgxPool.Begin(ctx)
	require.NoError(t, err)
	defer tx.Rollback(ctx) //nolint:errcheck

	var journalID int32
	require.NoError(t, tx.QueryRow(ctx,
		`INSERT INTO source.journals(user_id, journal_text, mood_score)
		 VALUES (gen_random_uuid(), $1, $2) RETURNING id`,
		"tx test entry", 5,
	).Scan(&journalID))

	result, err := client.InsertTx(ctx, tx, jobs.AnalyzeEntryArgs{
		EntryID: int64(journalID),
		UserID:  "00000000-0000-0000-0000-000000000001",
		Content: "tx test entry",
	}, nil)
	require.NoError(t, err)
	require.NotNil(t, result.Job)

	require.NoError(t, tx.Commit(ctx))

	var count int
	require.NoError(t, testPgxPool.QueryRow(ctx,
		`SELECT count(*) FROM river_job WHERE kind = $1 AND id = $2`,
		"analyze_entry", result.Job.ID,
	).Scan(&count))
	assert.Equal(t, 1, count)
}

// TestAnalyzeEntryTransactionRollback verifies rolling back also removes the job.
func TestAnalyzeEntryTransactionRollback(t *testing.T) {
	ctx := context.Background()
	client := newInsertOnlyClient(t)

	var before int
	require.NoError(t, testPgxPool.QueryRow(ctx,
		`SELECT count(*) FROM river_job WHERE kind = $1`, "analyze_entry",
	).Scan(&before))

	tx, err := testPgxPool.Begin(ctx)
	require.NoError(t, err)

	_, err = client.InsertTx(ctx, tx, jobs.AnalyzeEntryArgs{EntryID: 9999}, nil)
	require.NoError(t, err)

	require.NoError(t, tx.Rollback(ctx))

	var after int
	require.NoError(t, testPgxPool.QueryRow(ctx,
		`SELECT count(*) FROM river_job WHERE kind = $1`, "analyze_entry",
	).Scan(&after))
	assert.Equal(t, before, after, "job count unchanged after rollback")
}

// TestAnalyzeEntryWorkerSuccess verifies the worker calls the analyzer and completes.
func TestAnalyzeEntryWorkerSuccess(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	analyzerSrv := testinfra.MockAnalyzerServer(t)

	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewAnalyzeEntryWorker(
		http.DefaultClient, analyzerSrv.URL, "", testinfra.DiscardLogger(), false,
	))

	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{jobs.QueueAnalysis: {MaxWorkers: 2}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)

	_, err = client.Insert(ctx, jobs.AnalyzeEntryArgs{
		EntryID: 1001,
		UserID:  "00000000-0000-0000-0000-000000000001",
		Content: "success test",
	}, nil)
	require.NoError(t, err)

	select {
	case event := <-completedCh:
		assert.Equal(t, "analyze_entry", event.Job.Kind)
	case <-ctx.Done():
		t.Fatal("timed out waiting for job completion")
	}
}

// TestAnalyzeEntryWorkerRetry verifies a failing worker causes River to schedule a retry.
// MaxAttempts=2: first attempt fails, EventKindJobFailed fires (state retryable).
func TestAnalyzeEntryWorkerRetry(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	failingSrv := testinfra.FailingAnalyzerServer(t)

	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewAnalyzeEntryWorker(
		http.DefaultClient, failingSrv.URL, "", testinfra.DiscardLogger(), false,
	))

	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{jobs.QueueAnalysis: {MaxWorkers: 2}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	failCh, _ := client.Subscribe(river.EventKindJobFailed)

	_, err = client.Insert(ctx, jobs.AnalyzeEntryArgs{
		EntryID: 2001,
		UserID:  "00000000-0000-0000-0000-000000000001",
		Content: "will fail",
	}, &river.InsertOpts{MaxAttempts: 2, Queue: jobs.QueueAnalysis})
	require.NoError(t, err)

	select {
	case event := <-failCh:
		assert.Equal(t, "analyze_entry", event.Job.Kind)
		assert.GreaterOrEqual(t, event.Job.Attempt, 1)
	case <-ctx.Done():
		t.Fatal("timed out waiting for failure event")
	}
}
