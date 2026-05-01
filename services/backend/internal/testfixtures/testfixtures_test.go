package testfixtures_test

import (
	"context"
	"fmt"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/testfixtures"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/stretchr/testify/require"
)

var testPool *pgxpool.Pool

func TestMain(m *testing.M) {
	ctx := context.Background()

	testDB, err := testinfra.Setup(ctx, "../sql/schema")
	if err != nil {
		fmt.Fprintf(os.Stderr, "testinfra setup: %v\n", err)
		os.Exit(1)
	}

	testPool = testDB.Pool
	code := m.Run()
	testDB.Close(ctx)
	os.Exit(code)
}

func TestCreateWithDefaultsUser(t *testing.T) {
	ctx, queries := newTestQueries(t)

	user := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUser{})

	require.True(t, user.ID.Valid)
	require.NotEmpty(t, user.Email)
	require.NotNil(t, user.OauthProvider)
	require.Equal(t, "test", *user.OauthProvider)
}

func TestCreateWithDefaultsJournalCreatesParentUser(t *testing.T) {
	ctx, queries := newTestQueries(t)

	journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{})

	require.NotZero(t, journal.ID)
	require.True(t, journal.UserID.Valid)
	require.NotEmpty(t, journal.JournalText)
	require.NotNil(t, journal.MoodScore)
	require.EqualValues(t, 3, *journal.MoodScore)
}

func TestCreateWithDefaultsPreservesInputFields(t *testing.T) {
	ctx, queries := newTestQueries(t)

	user := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUser{})
	journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{
		UserID:      user.ID,
		JournalText: "caller supplied text",
		MoodScore:   testfixtures.Int32Ptr(5),
	})

	require.Equal(t, user.ID, journal.UserID)
	require.Equal(t, "caller supplied text", journal.JournalText)
	require.NotNil(t, journal.MoodScore)
	require.EqualValues(t, 5, *journal.MoodScore)
}

func TestCreateWithDefaultsCanForceFieldToZero(t *testing.T) {
	ctx, queries := newTestQueries(t)

	journal := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournal{}, "MoodScore")

	require.Nil(t, journal.MoodScore)
}

func TestCreateWithDefaultsCreatesDependentRecords(t *testing.T) {
	ctx, queries := newTestQueries(t)

	balance := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUserGameBalance{})
	bet := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceUserGameBet{UserID: balance.UserID})
	export := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournalExport{UserID: balance.UserID})
	projection := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceJournalCommunityProjection{UserID: balance.UserID})

	require.True(t, balance.UserID.Valid)
	require.Equal(t, balance.UserID, bet.UserID)
	require.Equal(t, balance.UserID, export.UserID)
	require.Equal(t, balance.UserID, projection.UserID)
	require.NotZero(t, projection.JournalID)
}

func TestCreateWithDefaultsCommunityRollups(t *testing.T) {
	ctx, queries := newTestQueries(t)

	theme := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceCommunityThemeRollup{})
	mood := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceCommunityMoodRollup{})
	summary := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceCommunitySummary{})
	promptSet := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceCommunityPromptSet{})
	runtimeConfig := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceRuntimeConfig{})

	require.NotZero(t, theme.ID)
	require.False(t, theme.DeltaVsPrevious.Valid)
	require.NotZero(t, mood.ID)
	require.False(t, mood.DeltaVsPrevious.Valid)
	require.NotZero(t, summary.ID)
	require.NotZero(t, promptSet.ID)
	require.NotZero(t, runtimeConfig.ID)
}

func TestCreateWithDefaultsPreservesExplicitCommunityDelta(t *testing.T) {
	ctx, queries := newTestQueries(t)

	theme := testfixtures.CreateWithDefaults(t, ctx, queries, db.SourceCommunityThemeRollup{
		DeltaVsPrevious: testfixtures.Numeric(t, "0"),
	})

	require.True(t, theme.DeltaVsPrevious.Valid)
}

func newTestQueries(t *testing.T) (context.Context, *db.Queries) {
	t.Helper()

	tx, err := testPool.Begin(context.Background())
	require.NoError(t, err)

	t.Cleanup(func() {
		_ = tx.Rollback(context.Background())
	})

	return context.Background(), db.New(tx)
}
