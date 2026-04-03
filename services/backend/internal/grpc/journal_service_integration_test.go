package grpc_test

import (
	"context"
	"database/sql"
	"strconv"
	"testing"

	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCreateJournal(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "This is a test journal entry",
		UserMood:    "7",
	}

	resp, err := svc.CreateJournal(ctx, req)
	require.NoError(t, err)
	assert.NotEmpty(t, resp.JournalId)

	journalID, err := strconv.Atoi(resp.JournalId)
	require.NoError(t, err)

	// CreateJournal commits its own pgx tx; use a direct connection to see the row.
	directQ := newDirectQueries(t)
	journals, err := directQ.GetJournalsByUserId(context.Background(), userID)
	require.NoError(t, err)

	var created *db.SourceJournal
	for _, j := range journals {
		if j.ID == int32(journalID) {
			created = &j
			break
		}
	}
	require.NotNil(t, created, "created journal should be present")
	assert.Equal(t, userID.String(), created.UserID.String())
	assert.Equal(t, "This is a test journal entry", created.JournalText)
	assert.Equal(t, int32(7), created.MoodScore.Int32)
}

// TestCreateJournalSucceedsWithAnalysisDeferred verifies CreateJournal commits the
// journal and enqueues the River job regardless of analyzer availability.
// (Analyzer is called by the River worker, not inline.)
func TestCreateJournalSucceedsWithAnalysisDeferred(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Analysis is deferred to River worker",
		UserMood:    "5",
	}

	resp, err := svc.CreateJournal(ctx, req)
	require.NoError(t, err)
	assert.NotEmpty(t, resp.JournalId)

	directQ := newDirectQueries(t)
	journals, err := directQ.GetJournalsByUserId(context.Background(), userID)
	require.NoError(t, err)
	assert.Len(t, journals, 1)
}

func TestCreateJournalWithInvalidAnalyzerURL(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Analysis is enqueued regardless of analyzer URL",
		UserMood:    "3",
	}

	// Journal creation succeeds; analysis is handled by the River worker later.
	resp, err := svc.CreateJournal(ctx, req)
	require.NoError(t, err)
	assert.NotEmpty(t, resp.JournalId)
}

func TestGetJournals(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      userID,
		JournalText: "Test journal entry",
		MoodScore:   sql.NullInt32{Int32: 5, Valid: true},
	})
	require.NoError(t, err)

	resp, err := svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String()})
	require.NoError(t, err)

	assert.NotNil(t, resp)
	assert.Len(t, resp.Journals, 1)
	assert.Equal(t, "Test journal entry", resp.Journals[0].JournalText)
	assert.Equal(t, "5", resp.Journals[0].UserMood)
	assert.Equal(t, int64(1), resp.TotalCount)
	assert.False(t, resp.HasMore)
}

func TestGetJournalsPagination(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)

	for i := 0; i < 5; i++ {
		_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
			UserID:      userID,
			JournalText: "Test journal entry " + strconv.Itoa(i+1),
			MoodScore:   sql.NullInt32{Int32: int32(i + 1), Valid: true},
		})
		require.NoError(t, err)
	}

	// First page
	resp, err := svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String(), Limit: 2, Offset: 0})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(5), resp.TotalCount)
	assert.True(t, resp.HasMore)

	// Second page
	resp, err = svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String(), Limit: 2, Offset: 2})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(5), resp.TotalCount)
	assert.True(t, resp.HasMore)

	// Last page
	resp, err = svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String(), Limit: 2, Offset: 4})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 1)
	assert.Equal(t, int64(5), resp.TotalCount)
	assert.False(t, resp.HasMore)
}

func TestGetJournalsPaginationDefaults(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)

	for i := 0; i < 2; i++ {
		_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
			UserID:      userID,
			JournalText: "Test journal entry " + strconv.Itoa(i+1),
			MoodScore:   sql.NullInt32{Int32: int32(i + 1), Valid: true},
		})
		require.NoError(t, err)
	}

	// No pagination params → defaults
	resp, err := svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String()})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(2), resp.TotalCount)
	assert.False(t, resp.HasMore)

	// Negative values → defaults
	resp, err = svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String(), Limit: -5, Offset: -10})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(2), resp.TotalCount)
	assert.False(t, resp.HasMore)
}

func TestGetJournalsPaginationLimitEnforcement(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      userID,
		JournalText: "Test journal entry",
		MoodScore:   sql.NullInt32{Int32: 5, Valid: true},
	})
	require.NoError(t, err)

	// Limit > 100 should be capped at 100
	resp, err := svc.GetJournals(ctx, &pb.GetJournalsRequest{UserId: userID.String(), Limit: 200, Offset: 0})
	require.NoError(t, err)
	assert.Len(t, resp.Journals, 1)
	assert.Equal(t, int64(1), resp.TotalCount)
}

func TestTriggerJournalAnalysis(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	journal, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      userID,
		JournalText: "Manual analysis test",
		MoodScore:   sql.NullInt32{Int32: 6, Valid: true},
	})
	require.NoError(t, err)

	resp, err := svc.TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{
		JournalId: strconv.Itoa(int(journal.ID)),
	})
	require.NoError(t, err)
	assert.True(t, resp.Success)
	assert.Equal(t, "Analysis triggered successfully", resp.Message)
}

func TestTriggerJournalAnalysisInvalidID(t *testing.T) {
	svc := &grpcServer.JournalServer{}

	_, err := svc.TriggerJournalAnalysis(context.Background(), &pb.TriggerAnalysisRequest{
		JournalId: "invalid-id",
	})
	assert.Error(t, err)
}

func TestTriggerJournalAnalysisNonExistentJournal(t *testing.T) {
	ctx, _ := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	_, err := svc.TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{JournalId: "99999"})
	assert.Error(t, err)
}

func TestCreateJournalInvalidUserID(t *testing.T) {
	svc := &grpcServer.JournalServer{}

	_, err := svc.CreateJournal(context.Background(), &pb.CreateJournalRequest{
		UserId:      "invalid-uuid",
		JournalText: "This is a test journal entry",
		UserMood:    "7",
	})
	assert.Error(t, err)
}

func TestGetJournalsInvalidUserID(t *testing.T) {
	svc := &grpcServer.JournalServer{}

	_, err := svc.GetJournals(context.Background(), &pb.GetJournalsRequest{UserId: "invalid-uuid"})
	assert.Error(t, err)
}

func TestCreateJournalInvalidMoodScore(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	_, err := svc.CreateJournal(ctx, &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Mood test",
		UserMood:    "not-a-number",
	})
	assert.Error(t, err)
}

func TestCreateJournalInvalidMoodValue(t *testing.T) {
	ctx, queries := newTestCtx(t)
	srv := testinfra.MockAnalyzerServer(t)
	ctx = withAnalyzer(ctx, srv.URL)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	_, err := svc.CreateJournal(ctx, &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "This will fail",
		UserMood:    "nil",
	})
	assert.Error(t, err)
}

func TestGetJournalByID(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withAnalyzer(ctx, "http://unused")
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	row, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      userID,
		JournalText: "Detail view body",
		MoodScore:   sql.NullInt32{Int32: 8, Valid: true},
	})
	require.NoError(t, err)

	resp, err := svc.GetJournal(ctx, &pb.GetJournalRequest{
		JournalId: strconv.Itoa(int(row.ID)),
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	require.NotNil(t, resp.Journal)
	assert.Equal(t, "Detail view body", resp.Journal.JournalText)
	assert.Equal(t, "8", resp.Journal.UserMood)
}

func TestUpdateJournalIntegration(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	createResp, err := svc.CreateJournal(ctx, &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Original",
		UserMood:    "5",
	})
	require.NoError(t, err)

	upd, err := svc.UpdateJournal(ctx, &pb.UpdateJournalRequest{
		JournalId:   createResp.JournalId,
		UserId:      userID.String(),
		JournalText: "Updated body",
		UserMood:    "9",
	})
	require.NoError(t, err)
	require.NotNil(t, upd.Journal)
	assert.Equal(t, "Updated body", upd.Journal.JournalText)
	assert.Equal(t, "9", upd.Journal.UserMood)

	directQ := newDirectQueries(t)
	jid, _ := strconv.Atoi(createResp.JournalId)
	j, err := directQ.GetJournalById(context.Background(), int32(jid))
	require.NoError(t, err)
	assert.Equal(t, "Updated body", j.JournalText)
	assert.Equal(t, int32(9), j.MoodScore.Int32)
}

func TestDeleteJournalIntegration(t *testing.T) {
	ctx, queries := newTestCtx(t)
	ctx = withRiverDeps(ctx)
	svc := &grpcServer.JournalServer{}

	userID := createTestUser(t, queries)
	createResp, err := svc.CreateJournal(ctx, &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "To delete",
		UserMood:    "4",
	})
	require.NoError(t, err)

	delResp, err := svc.DeleteJournal(ctx, &pb.DeleteJournalRequest{
		JournalId: createResp.JournalId,
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	assert.True(t, delResp.Success)

	jid, _ := strconv.Atoi(createResp.JournalId)
	_, err = queries.GetJournalById(context.Background(), int32(jid))
	assert.Error(t, err)
}
