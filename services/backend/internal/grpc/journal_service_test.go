package grpc_test

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func int32Ptr(v int32) *int32 { return &v }

func journalPgUUID(u uuid.UUID) pgtype.UUID { return pgtype.UUID{Bytes: u, Valid: true} }

func journalPgTS(t time.Time) pgtype.Timestamp { return pgtype.Timestamp{Time: t, Valid: true} }

// journalTestCtx returns a context with all deps needed by the journal service.
func journalTestCtx(dbMock db.Querier, httpMock inject.HTTPDoer) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, dbMock)
	ctx = inject.WithLogger(ctx, newTestLogger())
	ctx = inject.WithHTTPClient(ctx, httpMock)
	ctx = inject.WithAnalyzerURL(ctx, "http://localhost:8083")
	return ctx
}

// noopHTTPClient is a simple mock that returns 200 OK for all requests.
func noopHTTPClient() *mocks.HTTPDoerMock {
	return &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(bytes.NewBufferString(`{"success": true}`)),
			}, nil
		},
	}
}

func TestJournalServer_CreateJournal_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	req := &pb.CreateJournalRequest{
		UserId:      "invalid-uuid",
		JournalText: "Test journal",
		UserMood:    "5",
	}
	resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestJournalServer_CreateJournal_InvalidMoodScore(t *testing.T) {
	userID := uuid.New()
	server := &internalgrpc.JournalServer{}
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Test journal",
		UserMood:    "not-a-number",
	}
	resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidMoodScore)
}

func TestJournalServer_CreateJournal_MoodScoreOutOfRange(t *testing.T) {
	userID := uuid.New()
	server := &internalgrpc.JournalServer{}

	for _, mood := range []string{"0", "11", "-1", "99"} {
		req := &pb.CreateJournalRequest{
			UserId:      userID.String(),
			JournalText: "Test",
			UserMood:    mood,
		}
		resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
		require.Error(t, err, "mood %q should be rejected", mood)
		require.Nil(t, resp)
		assert.ErrorIs(t, err, internalgrpc.ErrInvalidMoodScore)
	}
}

func TestJournalServer_GetJournals_Success(t *testing.T) {
	// Arrange
	userID := uuid.New()
	now := time.Now()

	journals := []db.SourceJournal{
		{
			ID:          1,
			UserID:      journalPgUUID(userID),
			JournalText: "First journal entry",
			MoodScore:   int32Ptr(7),
			CreatedAt:   journalPgTS(now),
			ModifiedAt:  journalPgTS(now),
		},
		{
			ID:          2,
			UserID:      journalPgUUID(userID),
			JournalText: "Second journal entry",
			MoodScore:   int32Ptr(8),
			CreatedAt:   journalPgTS(now.Add(-time.Hour)),
			ModifiedAt:  journalPgTS(now.Add(-time.Hour)),
		},
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			assert.Equal(t, journalPgUUID(userID), uid)
			return 2, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, journalPgUUID(userID), arg.UserID)
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  10,
		Offset: 0,
	}

	// Act
	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(2), resp.TotalCount)
	assert.False(t, resp.HasMore)

	// Verify first journal
	assert.Equal(t, "1", resp.Journals[0].JournalId)
	assert.Equal(t, "First journal entry", resp.Journals[0].JournalText)
	assert.Equal(t, "7", resp.Journals[0].UserMood)
}

func TestJournalServer_GetJournals_WithTopics(t *testing.T) {
	userID := uuid.New()
	now := time.Now()
	journals := []db.SourceJournal{
		{ID: 1, UserID: journalPgUUID(userID), JournalText: "Entry one", MoodScore: int32Ptr(5), CreatedAt: journalPgTS(now), ModifiedAt: journalPgTS(now)},
		{ID: 2, UserID: journalPgUUID(userID), JournalText: "Entry two", MoodScore: int32Ptr(6), CreatedAt: journalPgTS(now), ModifiedAt: journalPgTS(now)},
	}
	topics := []db.GetTopicsByJournalIdsRow{
		{JournalID: 1, TopicName: "productivity"},
		{JournalID: 1, TopicName: "goals"},
		{JournalID: 2, TopicName: "reflection"},
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 2, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			assert.ElementsMatch(t, []int32{1, 2}, ids)
			return topics, nil
		},
	}

	resp, err := (&internalgrpc.JournalServer{}).GetJournals(
		journalTestCtx(mockQuerier, noopHTTPClient()),
		&pb.GetJournalsRequest{UserId: userID.String(), Limit: 10, Offset: 0},
	)
	require.NoError(t, err)
	require.Len(t, resp.Journals, 2)
	assert.Equal(t, []string{"productivity", "goals"}, resp.Journals[0].TopicNames)
	assert.Equal(t, []string{"reflection"}, resp.Journals[1].TopicNames)
}

func TestJournalServer_GetJournals_WithPagination(t *testing.T) {
	// Arrange
	userID := uuid.New()
	now := time.Now()

	// Return exactly 10 journals (the limit) to trigger hasMore
	journals := make([]db.SourceJournal, 10)
	for i := 0; i < 10; i++ {
		journals[i] = db.SourceJournal{
			ID:          int32(i + 1),
			UserID:      journalPgUUID(userID),
			JournalText: "Journal entry",
			MoodScore:   int32Ptr(5),
			CreatedAt:   journalPgTS(now),
			ModifiedAt:  journalPgTS(now),
		}
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 25, nil // Total of 25 journals
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, int32(10), arg.Limit)
			assert.Equal(t, int32(0), arg.Offset)
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  10,
		Offset: 0,
	}

	// Act
	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.Journals, 10)
	assert.Equal(t, int64(25), resp.TotalCount)
	assert.True(t, resp.HasMore) // Should have more results
}

func TestJournalServer_GetJournals_DefaultLimit(t *testing.T) {
	// Arrange
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			// Verify default limit is applied (50)
			assert.Equal(t, int32(50), arg.Limit)
			return []db.SourceJournal{}, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  0, // No limit specified
		Offset: 0,
	}

	// Act
	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
}

func TestJournalServer_GetJournals_MaxLimit(t *testing.T) {
	// Arrange
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			// Verify max limit is capped at 100
			assert.Equal(t, int32(100), arg.Limit)
			return []db.SourceJournal{}, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  500, // Exceeds max
		Offset: 0,
	}

	// Act
	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
}

func TestJournalServer_TriggerJournalAnalysis_Success(t *testing.T) {
	userID := uuid.New()
	journalID := int32(123)

	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			assert.Equal(t, journalID, id)
			return db.SourceJournal{
				ID:          journalID,
				UserID:      journalPgUUID(userID),
				JournalText: "Test journal",
				CreatedAt:   journalPgTS(time.Now()),
				ModifiedAt:  journalPgTS(time.Now()),
			}, nil
		},
	}

	ctx := withRiverDeps(journalTestCtx(mockQuerier, noopHTTPClient()))
	resp, err := (&internalgrpc.JournalServer{}).TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{JournalId: "123"})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.True(t, resp.Success)
	assert.Equal(t, "Analysis triggered successfully", resp.Message)
	assert.Len(t, mockQuerier.GetJournalByIdCalls(), 1)
}

func TestJournalServer_TriggerJournalAnalysis_JournalNotFound(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return db.SourceJournal{}, pgx.ErrNoRows
		},
	}

	ctx := withRiverDeps(journalTestCtx(mockQuerier, noopHTTPClient()))
	resp, err := (&internalgrpc.JournalServer{}).TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{JournalId: "999"})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrJournalNotFound)
}

func TestJournalServer_TriggerJournalAnalysis_InvalidJournalId(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}
	mockHTTPClient := noopHTTPClient()

	server := &internalgrpc.JournalServer{}

	req := &pb.TriggerAnalysisRequest{
		JournalId: "not-a-number",
	}

	// Act
	resp, err := server.TriggerJournalAnalysis(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidJournalID)
}

func TestJournalServer_DeleteJournal_Success(t *testing.T) {
	userID := uuid.New()
	j := db.SourceJournal{
		ID:          1,
		UserID:      journalPgUUID(userID),
		JournalText: "x",
		MoodScore:   int32Ptr(7),
		CreatedAt:   journalPgTS(time.Now()),
		ModifiedAt:  journalPgTS(time.Now()),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return j, nil
		},
		DeleteJournalForUserFunc: func(ctx context.Context, arg db.DeleteJournalForUserParams) (int64, error) {
			assert.Equal(t, int32(1), arg.ID)
			assert.Equal(t, journalPgUUID(userID), arg.UserID)
			return 1, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.DeleteJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.DeleteJournalRequest{
		JournalId: "1",
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.True(t, resp.Success)
}

func TestJournalServer_GetJournal_Success(t *testing.T) {
	userID := uuid.New()
	now := time.Now()
	j := db.SourceJournal{
		ID:          7,
		UserID:      journalPgUUID(userID),
		JournalText: "Full text",
		MoodScore:   int32Ptr(5),
		CreatedAt:   journalPgTS(now),
		ModifiedAt:  journalPgTS(now),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			assert.Equal(t, int32(7), id)
			return j, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return []db.GetTopicsByJournalIdsRow{{JournalID: 7, TopicName: "work"}}, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.GetJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.GetJournalRequest{
		JournalId: "7",
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	require.NotNil(t, resp.Journal)
	assert.Equal(t, "Full text", resp.Journal.JournalText)
	assert.Equal(t, "5", resp.Journal.UserMood)
	assert.Contains(t, resp.Journal.TopicNames, "work")
}

func TestJournalServer_GetJournal_Forbidden(t *testing.T) {
	owner := uuid.New()
	other := uuid.New()
	j := db.SourceJournal{
		ID:          1,
		UserID:      journalPgUUID(owner),
		JournalText: "x",
		MoodScore:   int32Ptr(7),
		CreatedAt:   journalPgTS(time.Now()),
		ModifiedAt:  journalPgTS(time.Now()),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return j, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.GetJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.GetJournalRequest{
		JournalId: "1",
		UserId:    other.String(),
	})
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrJournalForbidden)
}
