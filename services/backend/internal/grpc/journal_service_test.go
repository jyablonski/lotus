package grpc_test

import (
	"bytes"
	"context"
	"database/sql"
	"errors"
	"io"
	"net/http"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

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
func noopHTTPClient() *mocks.HTTPClientMock {
	return &mocks.HTTPClientMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(bytes.NewBufferString(`{"success": true}`)),
			}, nil
		},
	}
}

func TestJournalServer_CreateJournal_Success(t *testing.T) {
	// Arrange
	userID := uuid.New()
	expectedJournalID := int32(123)
	journalText := "Today was a great day!"
	moodScore := "8"

	mockQuerier := &mocks.QuerierMock{
		CreateJournalFunc: func(ctx context.Context, arg db.CreateJournalParams) (db.SourceJournal, error) {
			assert.Equal(t, userID, arg.UserID)
			assert.Equal(t, journalText, arg.JournalText)
			assert.True(t, arg.MoodScore.Valid)
			assert.Equal(t, int32(8), arg.MoodScore.Int32)

			return db.SourceJournal{
				ID:          expectedJournalID,
				UserID:      userID,
				JournalText: journalText,
				MoodScore:   sql.NullInt32{Int32: 8, Valid: true},
				CreatedAt:   time.Now(),
				ModifiedAt:  time.Now(),
			}, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: journalText,
		UserMood:    moodScore,
	}

	// Act
	resp, err := server.CreateJournal(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, "123", resp.JournalId)

	// Verify CreateJournal was called exactly once
	assert.Len(t, mockQuerier.CreateJournalCalls(), 1)
}

func TestJournalServer_CreateJournal_InvalidUserID(t *testing.T) {
	// Arrange — validation fails before deps are extracted, but context still
	// needs deps because the service extracts them after this particular check
	// passes. For invalid-uuid the error is before dep extraction.
	mockQuerier := &mocks.QuerierMock{}
	mockHTTPClient := noopHTTPClient()

	server := &internalgrpc.JournalServer{}

	req := &pb.CreateJournalRequest{
		UserId:      "invalid-uuid",
		JournalText: "Test journal",
		UserMood:    "5",
	}

	// Act
	resp, err := server.CreateJournal(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)

	// Verify DB was NOT called
	assert.Len(t, mockQuerier.CreateJournalCalls(), 0)
}

func TestJournalServer_CreateJournal_InvalidMoodScore(t *testing.T) {
	// Arrange
	userID := uuid.New()
	mockQuerier := &mocks.QuerierMock{}
	mockHTTPClient := noopHTTPClient()

	server := &internalgrpc.JournalServer{}

	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Test journal",
		UserMood:    "not-a-number",
	}

	// Act
	resp, err := server.CreateJournal(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidMoodScore)

	// Verify DB was NOT called
	assert.Len(t, mockQuerier.CreateJournalCalls(), 0)
}

func TestJournalServer_CreateJournal_DBError(t *testing.T) {
	// Arrange
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		CreateJournalFunc: func(ctx context.Context, arg db.CreateJournalParams) (db.SourceJournal, error) {
			return db.SourceJournal{}, errors.New("database error")
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Test journal",
		UserMood:    "5",
	}

	// Act
	resp, err := server.CreateJournal(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to create journal")
}

func TestJournalServer_GetJournals_Success(t *testing.T) {
	// Arrange
	userID := uuid.New()
	now := time.Now()

	journals := []db.SourceJournal{
		{
			ID:          1,
			UserID:      userID,
			JournalText: "First journal entry",
			MoodScore:   sql.NullInt32{Int32: 7, Valid: true},
			CreatedAt:   now,
			ModifiedAt:  now,
		},
		{
			ID:          2,
			UserID:      userID,
			JournalText: "Second journal entry",
			MoodScore:   sql.NullInt32{Int32: 8, Valid: true},
			CreatedAt:   now.Add(-time.Hour),
			ModifiedAt:  now.Add(-time.Hour),
		},
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid uuid.UUID) (int64, error) {
			assert.Equal(t, userID, uid)
			return 2, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, userID, arg.UserID)
			return journals, nil
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

func TestJournalServer_GetJournals_WithPagination(t *testing.T) {
	// Arrange
	userID := uuid.New()
	now := time.Now()

	// Return exactly 10 journals (the limit) to trigger hasMore
	journals := make([]db.SourceJournal, 10)
	for i := 0; i < 10; i++ {
		journals[i] = db.SourceJournal{
			ID:          int32(i + 1),
			UserID:      userID,
			JournalText: "Journal entry",
			MoodScore:   sql.NullInt32{Int32: 5, Valid: true},
			CreatedAt:   now,
			ModifiedAt:  now,
		}
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid uuid.UUID) (int64, error) {
			return 25, nil // Total of 25 journals
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, int32(10), arg.Limit)
			assert.Equal(t, int32(0), arg.Offset)
			return journals, nil
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
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid uuid.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			// Verify default limit is applied (50)
			assert.Equal(t, int32(50), arg.Limit)
			return []db.SourceJournal{}, nil
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
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid uuid.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			// Verify max limit is capped at 100
			assert.Equal(t, int32(100), arg.Limit)
			return []db.SourceJournal{}, nil
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
	// Arrange
	userID := uuid.New()
	journalID := int32(123)

	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			assert.Equal(t, journalID, id)
			return db.SourceJournal{
				ID:          journalID,
				UserID:      userID,
				JournalText: "Test journal",
				CreatedAt:   time.Now(),
				ModifiedAt:  time.Now(),
			}, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.TriggerAnalysisRequest{
		JournalId: "123",
	}

	// Act
	resp, err := server.TriggerJournalAnalysis(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.True(t, resp.Success)
	assert.Equal(t, "Analysis triggered successfully", resp.Message)

	// Verify GetJournalById was called
	assert.Len(t, mockQuerier.GetJournalByIdCalls(), 1)
}

func TestJournalServer_TriggerJournalAnalysis_JournalNotFound(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return db.SourceJournal{}, sql.ErrNoRows
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.TriggerAnalysisRequest{
		JournalId: "999",
	}

	// Act
	resp, err := server.TriggerJournalAnalysis(journalTestCtx(mockQuerier, mockHTTPClient), req)

	// Assert
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
