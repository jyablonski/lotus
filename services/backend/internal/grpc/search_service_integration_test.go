package grpc_test

import (
	"context"
	"testing"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// insertSearchJournal inserts a journal directly via pgxPool (committed, visible to search).
// Returns the journal ID.
func insertSearchJournal(t *testing.T, userID uuid.UUID, text string, mood int32) int32 {
	t.Helper()
	q := db.New(testPgxPool)
	ms := mood
	j, err := q.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      pgtype.UUID{Bytes: userID, Valid: true},
		JournalText: text,
		MoodScore:   &ms,
	})
	require.NoError(t, err)
	t.Cleanup(func() {
		_, _ = q.DeleteJournalForUser(context.Background(), db.DeleteJournalForUserParams{
			ID:     j.ID,
			UserID: pgtype.UUID{Bytes: userID, Valid: true},
		})
	})
	return j.ID
}

// insertSearchUser creates a user directly via pgxPool (committed) and returns the UUID.
func insertSearchUser(t *testing.T) uuid.UUID {
	t.Helper()
	q := db.New(testPgxPool)
	email := "search-test-" + uuid.New().String() + "@test.example"
	op := "test"
	u, err := q.CreateUserOauth(context.Background(), db.CreateUserOauthParams{
		Email: email, OauthProvider: &op,
	})
	require.NoError(t, err)
	uid := uuid.UUID(u.ID.Bytes)
	t.Cleanup(func() {
		_ = q.DeleteUserById(context.Background(), u.ID)
	})
	return uid
}

func TestKeywordSearchJournals_ReturnsMatchingEntries(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	userID := insertSearchUser(t)

	insertSearchJournal(t, userID, "Today I went hiking in the mountains and enjoyed the fresh air", 8)
	insertSearchJournal(t, userID, "Had a productive day coding a new feature for the application", 7)
	insertSearchJournal(t, userID, "Spent the evening reading a book about philosophy", 6)

	// Need to supply a DB querier for topic hydration. Reuse the test transaction's querier.
	_ = queries

	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "hiking",
		Limit:  10,
	})
	require.NoError(t, err)
	require.Len(t, resp.Results, 1)
	assert.Contains(t, resp.Results[0].Journal.JournalText, "hiking")
	assert.Greater(t, resp.Results[0].Rank, float32(0))
}

func TestKeywordSearchJournals_NoMatches(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	userID := insertSearchUser(t)
	insertSearchJournal(t, userID, "Today I went hiking in the mountains", 8)

	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "quantum",
		Limit:  10,
	})
	require.NoError(t, err)
	assert.Empty(t, resp.Results)
}

func TestKeywordSearchJournals_OnlyMatchesOwnEntries(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	user1 := insertSearchUser(t)
	user2 := insertSearchUser(t)

	insertSearchJournal(t, user1, "Went running in the park this morning", 7)
	insertSearchJournal(t, user2, "Running errands all afternoon was exhausting", 4)

	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: user1.String(),
		Query:  "running",
		Limit:  10,
	})
	require.NoError(t, err)
	require.Len(t, resp.Results, 1)
	assert.Equal(t, user1.String(), resp.Results[0].Journal.UserId)
}

func TestKeywordSearchJournals_RespectsLimit(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	userID := insertSearchUser(t)

	for i := 0; i < 5; i++ {
		insertSearchJournal(t, userID, "This is a journal entry about daily reflections and thoughts", 5)
	}

	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "journal",
		Limit:  2,
	})
	require.NoError(t, err)
	assert.Len(t, resp.Results, 2)
}

func TestKeywordSearchJournals_DefaultLimit(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	userID := insertSearchUser(t)
	insertSearchJournal(t, userID, "A simple test journal entry for default limit verification", 5)

	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "journal",
		Limit:  0,
	})
	require.NoError(t, err)
	assert.Len(t, resp.Results, 1)
}

func TestKeywordSearchJournals_MultipleWordQuery(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	svc := &grpcServer.JournalServer{}

	userID := insertSearchUser(t)

	insertSearchJournal(t, userID, "Learning about machine learning and artificial intelligence today", 9)
	insertSearchJournal(t, userID, "Went to the gym for some strength training", 7)

	// plainto_tsquery ANDs the terms: "machine learning" should match only the first entry.
	resp, err := svc.KeywordSearchJournals(ctx, &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "machine learning",
		Limit:  10,
	})
	require.NoError(t, err)
	require.Len(t, resp.Results, 1)
	assert.Contains(t, resp.Results[0].Journal.JournalText, "machine learning")
}
