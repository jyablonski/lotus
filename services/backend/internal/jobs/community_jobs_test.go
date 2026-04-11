package jobs_test

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/jobs"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverpgxv5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestRefreshCommunityProjectionWorkerCreatesProjection(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	userID := createCommunityUser(t, ctx, "projection-worker@test.example", true, true, "America/Los_Angeles", "US", "US-CA")
	journalID := createJournal(t, ctx, userID, "Need a projection row", 8)
	insertSentiment(t, ctx, journalID, "positive", "sentiment_v1")
	insertTopic(t, ctx, journalID, "work and career", 0.91, "topics_v1")

	producer := newInsertOnlyClient(t)
	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewRefreshCommunityProjectionWorker(testQueries, testinfra.DiscardLogger(), producer))

	var rollupsBefore int
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT count(*) FROM river_job WHERE kind = 'refresh_community_rollups'
	`).Scan(&rollupsBefore))

	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{river.QueueDefault: {MaxWorkers: 2}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)
	_, err = client.Insert(ctx, jobs.RefreshCommunityProjectionArgs{JournalID: int64(journalID)}, nil)
	require.NoError(t, err)

	select {
	case <-completedCh:
	case <-ctx.Done():
		t.Fatal("timed out waiting for projection refresh")
	}

	projection, err := testQueries.GetJournalCommunityProjectionByJournalId(ctx, journalID)
	require.NoError(t, err)
	assert.True(t, projection.EligibleForCommunity)
	assert.Equal(t, []string{"work"}, projection.ThemeNames)
	assert.Equal(t, "hopeful", derefStr(projection.PrimaryMood))
	assert.Equal(t, "positive", derefStr(projection.PrimarySentiment))
	assert.Equal(t, "US-CA", derefStr(projection.RegionCode))

	var queuedRollups int
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT count(*) FROM river_job WHERE kind = 'refresh_community_rollups'
	`).Scan(&queuedRollups))
	assert.Equal(t, rollupsBefore, queuedRollups)
}

func TestRefreshCommunityProjectionWorkerHandlesMissingAnalysisRows(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	userID := createCommunityUser(t, ctx, "projection-worker-missing-analysis@test.example", true, true, "UTC", "US", "US-CA")
	journalID := createJournal(t, ctx, userID, "No analysis rows yet", 6)

	producer := newInsertOnlyClient(t)
	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewRefreshCommunityProjectionWorker(testQueries, testinfra.DiscardLogger(), producer))

	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{river.QueueDefault: {MaxWorkers: 2}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)
	_, err = client.Insert(ctx, jobs.RefreshCommunityProjectionArgs{JournalID: int64(journalID)}, nil)
	require.NoError(t, err)

	select {
	case <-completedCh:
	case <-ctx.Done():
		t.Fatal("timed out waiting for projection refresh without analysis rows")
	}

	projection, err := testQueries.GetJournalCommunityProjectionByJournalId(ctx, journalID)
	require.NoError(t, err)
	assert.False(t, projection.EligibleForCommunity)
	assert.Equal(t, "steady", derefStr(projection.PrimaryMood))
	assert.Nil(t, projection.PrimarySentiment)
	assert.Empty(t, projection.ThemeNames)
	assert.Equal(t, "v1", projection.AnalysisVersion)
}

func TestRefreshCommunityRollupsWorkerPersistsRollupsSummaryAndPrompts(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	anchorDate := time.Date(2026, 4, 7, 0, 0, 0, 0, time.UTC)
	for i := 0; i < 20; i++ {
		userID := createCommunityUser(
			t,
			ctx,
			"rollup-user-"+time.Now().Format("150405")+"-"+string(rune('a'+i))+"@test.example",
			true,
			true,
			"UTC",
			"US",
			"US-CA",
		)
		journalID := createJournal(t, ctx, userID, "Rollup seed", 8)
		_, err := testQueries.UpsertJournalCommunityProjection(ctx, db.UpsertJournalCommunityProjectionParams{
			JournalID:            journalID,
			UserID:               userID,
			EligibleForCommunity: true,
			EntryLocalDate:       pgtype.Date{Time: anchorDate, Valid: true},
			PrimaryMood:          ptr("hopeful"),
			PrimarySentiment:     ptr("positive"),
			ThemeNames:           []string{"work", "stress"},
			CountryCode:          ptr("US"),
			RegionCode:           ptr("US-CA"),
			AnalysisVersion:      "v1",
		})
		require.NoError(t, err)
	}

	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewRefreshCommunityRollupsWorker(testQueries, testinfra.DiscardLogger()))
	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{river.QueueDefault: {MaxWorkers: 2}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)
	_, err = client.Insert(ctx, jobs.RefreshCommunityRollupsArgs{AnchorDate: "2026-04-07"}, nil)
	require.NoError(t, err)

	select {
	case <-completedCh:
	case <-ctx.Done():
		t.Fatal("timed out waiting for rollup refresh")
	}

	var themeCount int
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT count(*) FROM source.community_theme_rollups
		WHERE bucket_date = $1 AND time_grain = 'day' AND scope_type = 'global'
	`, anchorDate).Scan(&themeCount))
	assert.GreaterOrEqual(t, themeCount, 2)

	var summaryText string
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT summary_text FROM source.community_summaries
		WHERE bucket_date = $1 AND time_grain = 'day' AND scope_type = 'global' AND scope_value = 'global'
	`, anchorDate).Scan(&summaryText))
	assert.Contains(t, summaryText, "People are broadly feeling")

	var promptJSON []byte
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT prompt_set_json FROM source.community_prompt_sets
		WHERE bucket_date = $1 AND time_grain = 'day' AND scope_type = 'global' AND scope_value = 'global'
	`, anchorDate).Scan(&promptJSON))

	var prompts []map[string]any
	require.NoError(t, json.Unmarshal(promptJSON, &prompts))
	require.Len(t, prompts, 5)
	assert.Equal(t, "template", prompts[0]["generation_method"])
}

func TestRepairCommunityDataWorkerEnqueuesProjectionRefreshes(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	userID := createCommunityUser(t, ctx, "repair@test.example", true, true, "UTC", "US", "US-CA")
	_ = createJournal(t, ctx, userID, "Repair this journal", 6)

	producer := newInsertOnlyClient(t)
	workers := river.NewWorkers()
	river.AddWorker(workers, jobs.NewRepairCommunityDataWorker(testQueries, testinfra.DiscardLogger(), producer))
	client, err := river.NewClient(riverpgxv5.New(testPgxPool), &river.Config{
		Queues:  map[string]river.QueueConfig{jobs.QueueCron: {MaxWorkers: 1}},
		Workers: workers,
		Logger:  testinfra.DiscardLogger(),
	})
	require.NoError(t, err)
	require.NoError(t, client.Start(ctx))
	defer client.Stop(context.Background()) //nolint:errcheck

	completedCh, _ := client.Subscribe(river.EventKindJobCompleted)
	_, err = client.Insert(ctx, jobs.RepairCommunityDataArgs{DaysBack: 35}, nil)
	require.NoError(t, err)

	select {
	case <-completedCh:
	case <-ctx.Done():
		t.Fatal("timed out waiting for repair job")
	}

	var queued int
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		SELECT count(*) FROM river_job WHERE kind = 'refresh_community_projection'
	`).Scan(&queued))
	assert.GreaterOrEqual(t, queued, 1)
}

func createCommunityUser(t *testing.T, ctx context.Context, email string, insightsOptIn, locationOptIn bool, timezone, country, region string) pgtype.UUID {
	t.Helper()
	var userID pgtype.UUID
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		INSERT INTO source.users (
			email, oauth_provider, timezone, community_insights_opt_in, community_location_opt_in, community_country_code, community_region_code
		) VALUES ($1, 'test', $2, $3, $4, $5, $6)
		RETURNING id
	`, email, timezone, insightsOptIn, locationOptIn, country, region).Scan(&userID))
	return userID
}

func createJournal(t *testing.T, ctx context.Context, userID pgtype.UUID, text string, moodScore int32) int32 {
	t.Helper()
	var journalID int32
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		INSERT INTO source.journals (user_id, journal_text, mood_score)
		VALUES ($1, $2, $3)
		RETURNING id
	`, userID, text, moodScore).Scan(&journalID))
	return journalID
}

func insertSentiment(t *testing.T, ctx context.Context, journalID int32, sentiment, modelVersion string) {
	t.Helper()
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		INSERT INTO source.journal_sentiments (
			journal_id, sentiment, confidence, confidence_level, is_reliable, ml_model_version, all_scores
		) VALUES ($1, $2, 0.9500, 'high', TRUE, $3, '{"positive": 0.95}')
		RETURNING id
	`, journalID, sentiment, modelVersion).Scan(new(int32)))
}

func insertTopic(t *testing.T, ctx context.Context, journalID int32, topic string, confidence float64, modelVersion string) {
	t.Helper()
	require.NoError(t, testPgxPool.QueryRow(ctx, `
		INSERT INTO source.journal_topics (journal_id, topic_name, confidence, ml_model_version)
		VALUES ($1, $2, $3, $4)
		RETURNING id
	`, journalID, topic, confidence, modelVersion).Scan(new(int32)))
}

func ptr(value string) *string {
	return &value
}

func derefStr(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}
