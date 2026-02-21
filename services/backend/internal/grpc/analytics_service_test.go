package grpc_test

import (
	"context"
	"database/sql"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// newAnalyticsTestLogger creates a logger that discards output for testing
func newAnalyticsTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

// analyticsTestCtx returns a context with DB and logger for analytics tests.
func analyticsTestCtx(mock db.Querier) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, mock)
	ctx = inject.WithLogger(ctx, newAnalyticsTestLogger())
	return ctx
}

func TestAnalyticsServer_GetUserJournalSummary_Success(t *testing.T) {
	// Arrange
	userID := uuid.New()
	now := time.Now()
	firstJournal := now.Add(-30 * 24 * time.Hour)
	lastJournal := now.Add(-1 * time.Hour)

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id uuid.UUID) (db.GoldUserJournalSummary, error) {
			assert.Equal(t, userID, id)
			return db.GoldUserJournalSummary{
				UserID:                         userID,
				UserEmail:                      sql.NullString{String: "test@example.com", Valid: true},
				UserRole:                       sql.NullString{String: "user", Valid: true},
				UserTimezone:                   sql.NullString{String: "America/New_York", Valid: true},
				UserCreatedAt:                  sql.NullTime{Time: firstJournal, Valid: true},
				TotalJournals:                  25,
				ActiveDays:                     20,
				AvgMoodScore:                   sql.NullString{String: "7.5", Valid: true},
				MinMoodScore:                   sql.NullInt32{Int32: 3, Valid: true},
				MaxMoodScore:                   sql.NullInt32{Int32: 10, Valid: true},
				MoodScoreStddev:                sql.NullString{String: "1.5", Valid: true},
				PositiveEntries:                15,
				NegativeEntries:                5,
				NeutralEntries:                 5,
				AvgSentimentScore:              sql.NullString{String: "0.65", Valid: true},
				AvgJournalLength:               sql.NullString{String: "250.5", Valid: true},
				FirstJournalAt:                 sql.NullTime{Time: firstJournal, Valid: true},
				LastJournalAt:                  sql.NullTime{Time: lastJournal, Valid: true},
				LastModifiedAt:                 sql.NullTime{Time: now, Valid: true},
				TotalJournals30d:               10,
				AvgMoodScore30d:                sql.NullString{String: "8.0", Valid: true},
				MinMoodScore30d:                sql.NullInt32{Int32: 5, Valid: true},
				MaxMoodScore30d:                sql.NullInt32{Int32: 10, Valid: true},
				DailyStreak:                    7,
				PositivePercentage:             sql.NullString{String: "60.0", Valid: true},
				DaysSinceLastJournal:           sql.NullInt32{Int32: 0, Valid: true},
				DaysBetweenFirstAndLastJournal: sql.NullInt32{Int32: 30, Valid: true},
				JournalsPerActiveDay:           sql.NullString{String: "1.25", Valid: true},
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.Summary)

	summary := resp.Summary
	assert.Equal(t, userID.String(), summary.UserId)
	assert.Equal(t, "test@example.com", summary.UserEmail)
	assert.Equal(t, "user", summary.UserRole)
	assert.Equal(t, "America/New_York", summary.UserTimezone)
	assert.Equal(t, int32(25), summary.TotalJournals)
	assert.Equal(t, int32(20), summary.ActiveDays)
	assert.Equal(t, int32(15), summary.PositiveEntries)
	assert.Equal(t, int32(5), summary.NegativeEntries)
	assert.Equal(t, int32(5), summary.NeutralEntries)
	assert.Equal(t, int32(10), summary.TotalJournals_30D)
	assert.Equal(t, int32(7), summary.DailyStreak)

	// Check nullable fields
	require.NotNil(t, summary.AvgMoodScore)
	assert.Equal(t, 7.5, *summary.AvgMoodScore)
	require.NotNil(t, summary.MinMoodScore)
	assert.Equal(t, int32(3), *summary.MinMoodScore)
	require.NotNil(t, summary.MaxMoodScore)
	assert.Equal(t, int32(10), *summary.MaxMoodScore)
	require.NotNil(t, summary.MoodScoreStddev)
	assert.Equal(t, 1.5, *summary.MoodScoreStddev)
	require.NotNil(t, summary.AvgSentimentScore)
	assert.Equal(t, 0.65, *summary.AvgSentimentScore)
	require.NotNil(t, summary.AvgJournalLength)
	assert.Equal(t, 250.5, *summary.AvgJournalLength)

	// 30-day metrics
	require.NotNil(t, summary.AvgMoodScore_30D)
	assert.Equal(t, 8.0, *summary.AvgMoodScore_30D)
	require.NotNil(t, summary.MinMoodScore_30D)
	assert.Equal(t, int32(5), *summary.MinMoodScore_30D)
	require.NotNil(t, summary.MaxMoodScore_30D)
	assert.Equal(t, int32(10), *summary.MaxMoodScore_30D)

	// Calculated fields
	require.NotNil(t, summary.PositivePercentage)
	assert.Equal(t, 60.0, *summary.PositivePercentage)
	require.NotNil(t, summary.DaysSinceLastJournal)
	assert.Equal(t, int32(0), *summary.DaysSinceLastJournal)
	require.NotNil(t, summary.DaysBetweenFirstAndLastJournal)
	assert.Equal(t, int32(30), *summary.DaysBetweenFirstAndLastJournal)
	require.NotNil(t, summary.JournalsPerActiveDay)
	assert.Equal(t, 1.25, *summary.JournalsPerActiveDay)

	// Verify mock was called
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 1)
}

func TestAnalyticsServer_GetUserJournalSummary_InvalidUserID(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: "not-a-valid-uuid",
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)

	// Verify mock was NOT called (validation should fail first)
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 0)
}

func TestAnalyticsServer_GetUserJournalSummary_EmptyUserID(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: "",
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)

	// Verify mock was NOT called
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 0)
}

func TestAnalyticsServer_GetUserJournalSummary_DBError(t *testing.T) {
	// Arrange
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id uuid.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{}, errors.New("database connection failed")
		},
	}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to get user journal summary")

	// Verify mock was called
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 1)
}

func TestAnalyticsServer_GetUserJournalSummary_NotFound(t *testing.T) {
	// Arrange
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id uuid.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{}, sql.ErrNoRows
		},
	}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to get user journal summary")
}

func TestAnalyticsServer_GetUserJournalSummary_NullableFieldsAreNil(t *testing.T) {
	// Arrange - Test when nullable fields are null in DB
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id uuid.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{
				UserID:                         userID,
				UserEmail:                      sql.NullString{Valid: false},
				UserRole:                       sql.NullString{Valid: false},
				UserTimezone:                   sql.NullString{Valid: false},
				UserCreatedAt:                  sql.NullTime{Valid: false},
				TotalJournals:                  0,
				ActiveDays:                     0,
				AvgMoodScore:                   sql.NullString{Valid: false},
				MinMoodScore:                   sql.NullInt32{Valid: false},
				MaxMoodScore:                   sql.NullInt32{Valid: false},
				MoodScoreStddev:                sql.NullString{Valid: false},
				PositiveEntries:                0,
				NegativeEntries:                0,
				NeutralEntries:                 0,
				AvgSentimentScore:              sql.NullString{Valid: false},
				AvgJournalLength:               sql.NullString{Valid: false},
				FirstJournalAt:                 sql.NullTime{Valid: false},
				LastJournalAt:                  sql.NullTime{Valid: false},
				LastModifiedAt:                 sql.NullTime{Valid: false},
				TotalJournals30d:               0,
				AvgMoodScore30d:                sql.NullString{Valid: false},
				MinMoodScore30d:                sql.NullInt32{Valid: false},
				MaxMoodScore30d:                sql.NullInt32{Valid: false},
				DailyStreak:                    0,
				PositivePercentage:             sql.NullString{Valid: false},
				DaysSinceLastJournal:           sql.NullInt32{Valid: false},
				DaysBetweenFirstAndLastJournal: sql.NullInt32{Valid: false},
				JournalsPerActiveDay:           sql.NullString{Valid: false},
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.Summary)

	summary := resp.Summary
	assert.Equal(t, userID.String(), summary.UserId)
	// Nullable strings should be empty
	assert.Equal(t, "", summary.UserEmail)
	assert.Equal(t, "", summary.UserRole)
	assert.Equal(t, "", summary.UserTimezone)
	assert.Equal(t, "", summary.UserCreatedAt)
	// Required fields should be zero
	assert.Equal(t, int32(0), summary.TotalJournals)
	assert.Equal(t, int32(0), summary.ActiveDays)
	// Nullable fields should be nil
	assert.Nil(t, summary.AvgMoodScore)
	assert.Nil(t, summary.MinMoodScore)
	assert.Nil(t, summary.MaxMoodScore)
	assert.Nil(t, summary.MoodScoreStddev)
	assert.Nil(t, summary.AvgSentimentScore)
	assert.Nil(t, summary.AvgJournalLength)
	assert.Nil(t, summary.FirstJournalAt)
	assert.Nil(t, summary.LastJournalAt)
	assert.Nil(t, summary.LastModifiedAt)
	assert.Nil(t, summary.AvgMoodScore_30D)
	assert.Nil(t, summary.MinMoodScore_30D)
	assert.Nil(t, summary.MaxMoodScore_30D)
	assert.Nil(t, summary.PositivePercentage)
	assert.Nil(t, summary.DaysSinceLastJournal)
	assert.Nil(t, summary.DaysBetweenFirstAndLastJournal)
	assert.Nil(t, summary.JournalsPerActiveDay)
}

func TestAnalyticsServer_GetUserJournalSummary_PartialNullableFields(t *testing.T) {
	// Arrange - Test when some nullable fields are set and some are null
	userID := uuid.New()
	now := time.Now()

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id uuid.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{
				UserID:                         userID,
				UserEmail:                      sql.NullString{String: "partial@example.com", Valid: true},
				UserRole:                       sql.NullString{Valid: false}, // null
				UserTimezone:                   sql.NullString{String: "UTC", Valid: true},
				UserCreatedAt:                  sql.NullTime{Valid: false}, // null
				TotalJournals:                  5,
				ActiveDays:                     3,
				AvgMoodScore:                   sql.NullString{String: "6.5", Valid: true},
				MinMoodScore:                   sql.NullInt32{Valid: false}, // null
				MaxMoodScore:                   sql.NullInt32{Int32: 9, Valid: true},
				MoodScoreStddev:                sql.NullString{Valid: false}, // null
				PositiveEntries:                3,
				NegativeEntries:                1,
				NeutralEntries:                 1,
				AvgSentimentScore:              sql.NullString{Valid: false},
				AvgJournalLength:               sql.NullString{String: "100.0", Valid: true},
				FirstJournalAt:                 sql.NullTime{Time: now.Add(-7 * 24 * time.Hour), Valid: true},
				LastJournalAt:                  sql.NullTime{Valid: false}, // null
				LastModifiedAt:                 sql.NullTime{Time: now, Valid: true},
				TotalJournals30d:               5,
				AvgMoodScore30d:                sql.NullString{Valid: false},
				MinMoodScore30d:                sql.NullInt32{Valid: false},
				MaxMoodScore30d:                sql.NullInt32{Valid: false},
				DailyStreak:                    3,
				PositivePercentage:             sql.NullString{String: "60.0", Valid: true},
				DaysSinceLastJournal:           sql.NullInt32{Valid: false},
				DaysBetweenFirstAndLastJournal: sql.NullInt32{Int32: 7, Valid: true},
				JournalsPerActiveDay:           sql.NullString{Valid: false},
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	// Act
	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.Summary)

	summary := resp.Summary
	assert.Equal(t, userID.String(), summary.UserId)
	assert.Equal(t, "partial@example.com", summary.UserEmail)
	assert.Equal(t, "", summary.UserRole) // null -> empty string
	assert.Equal(t, "UTC", summary.UserTimezone)
	assert.Equal(t, "", summary.UserCreatedAt) // null -> empty string
	assert.Equal(t, int32(5), summary.TotalJournals)
	assert.Equal(t, int32(3), summary.ActiveDays)
	assert.Equal(t, int32(5), summary.TotalJournals_30D)
	assert.Equal(t, int32(3), summary.DailyStreak)

	// Check mixed nullable fields
	require.NotNil(t, summary.AvgMoodScore)
	assert.Equal(t, 6.5, *summary.AvgMoodScore)
	assert.Nil(t, summary.MinMoodScore)
	require.NotNil(t, summary.MaxMoodScore)
	assert.Equal(t, int32(9), *summary.MaxMoodScore)
	assert.Nil(t, summary.MoodScoreStddev)
	require.NotNil(t, summary.AvgJournalLength)
	assert.Equal(t, 100.0, *summary.AvgJournalLength)
	require.NotNil(t, summary.FirstJournalAt)
	assert.Nil(t, summary.LastJournalAt)
	require.NotNil(t, summary.LastModifiedAt)
	require.NotNil(t, summary.PositivePercentage)
	assert.Equal(t, 60.0, *summary.PositivePercentage)
	require.NotNil(t, summary.DaysBetweenFirstAndLastJournal)
	assert.Equal(t, int32(7), *summary.DaysBetweenFirstAndLastJournal)
	assert.Nil(t, summary.JournalsPerActiveDay)
}
