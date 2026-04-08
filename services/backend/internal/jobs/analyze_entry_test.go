package jobs_test

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/jyablonski/lotus/internal/db"
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

	pq := db.New(testPgxPool)
	email := "analyze-entry-tx-" + t.Name() + "@test.example"
	op := "test"
	u, err := pq.CreateUserOauth(ctx, db.CreateUserOauthParams{Email: email, OauthProvider: &op})
	require.NoError(t, err)
	t.Cleanup(func() {
		_ = pq.DeleteUserById(ctx, u.ID)
	})

	tx, err := testPgxPool.Begin(ctx)
	require.NoError(t, err)
	defer tx.Rollback(ctx) //nolint:errcheck

	ms := int32(5)
	journal, err := db.New(tx).CreateJournal(ctx, db.CreateJournalParams{
		UserID:      u.ID,
		JournalText: "tx test entry",
		MoodScore:   &ms,
	})
	require.NoError(t, err)
	journalID := journal.ID
	t.Cleanup(func() {
		_, _ = pq.DeleteJournalForUser(ctx, db.DeleteJournalForUserParams{
			ID:     journalID,
			UserID: u.ID,
		})
	})

	result, err := client.InsertTx(ctx, tx, jobs.AnalyzeEntryArgs{
		EntryID: int64(journalID),
		UserID:  "00000000-0000-0000-0000-000000000001",
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
		http.DefaultClient, analyzerSrv.URL, "", testinfra.DiscardLogger(), false, nil,
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
		http.DefaultClient, failingSrv.URL, "", testinfra.DiscardLogger(), false, nil,
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

func TestAnalyzeEntryWorkerEnqueuesCommunityProjectionRefresh(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	requestPaths := make(chan string, 3)
	analyzerSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestPaths <- r.URL.Path
		w.WriteHeader(http.StatusOK)
	}))
	defer analyzerSrv.Close()

	producer := newInsertOnlyClient(t)

	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewAnalyzeEntryWorker(
		http.DefaultClient, analyzerSrv.URL, "", testinfra.DiscardLogger(), false, producer,
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
		EntryID: 3001,
		UserID:  "00000000-0000-0000-0000-000000000001",
	}, nil)
	require.NoError(t, err)

	select {
	case <-completedCh:
	case <-ctx.Done():
		t.Fatal("timed out waiting for analyze_entry completion")
	}

	paths := []string{<-requestPaths, <-requestPaths, <-requestPaths}
	assert.Contains(t, paths, "/v1/journals/3001/topics/internal")
	assert.Contains(t, paths, "/v1/journals/3001/sentiment/analyze")
	assert.Contains(t, paths, "/v1/journals/3001/embeddings")

	var queued int
	require.NoError(t, testPgxPool.QueryRow(ctx,
		`SELECT count(*) FROM river_job WHERE kind = $1`,
		"refresh_community_projection",
	).Scan(&queued))
	assert.GreaterOrEqual(t, queued, 1)
}
