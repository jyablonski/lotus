package grpc_test

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func anaUUID(u uuid.UUID) pgtype.UUID {
	return pgtype.UUID{Bytes: u, Valid: true}
}

func anaTS(tm time.Time) pgtype.Timestamp {
	return pgtype.Timestamp{Time: tm, Valid: true}
}

func anaNum(s string) pgtype.Numeric {
	var n pgtype.Numeric
	if err := n.Scan(s); err != nil {
		panic(err)
	}
	return n
}

func strp(s string) *string { return &s }

func i32p(v int32) *int32 { return &v }

func newAnalyticsTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func analyticsTestCtx(mock db.Querier) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, mock)
	ctx = inject.WithLogger(ctx, newAnalyticsTestLogger())
	return ctx
}

func TestAnalyticsServer_GetUserJournalSummary_Success(t *testing.T) {
	userID := uuid.New()
	now := time.Now()
	firstJournal := now.Add(-30 * 24 * time.Hour)
	lastJournal := now.Add(-1 * time.Hour)

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GoldUserJournalSummary, error) {
			assert.Equal(t, anaUUID(userID), id)
			return db.GoldUserJournalSummary{
				UserID:                         anaUUID(userID),
				UserEmail:                      strp("test@example.com"),
				UserRole:                       strp("user"),
				UserTimezone:                   strp("America/New_York"),
				UserCreatedAt:                  anaTS(firstJournal),
				TotalJournals:                  25,
				ActiveDays:                     20,
				AvgMoodScore:                   anaNum("7.5"),
				MinMoodScore:                   i32p(3),
				MaxMoodScore:                   i32p(10),
				MoodScoreStddev:                anaNum("1.5"),
				PositiveEntries:                15,
				NegativeEntries:                5,
				NeutralEntries:                 5,
				AvgSentimentScore:              anaNum("0.65"),
				AvgJournalLength:               anaNum("250.5"),
				FirstJournalAt:                 anaTS(firstJournal),
				LastJournalAt:                  anaTS(lastJournal),
				LastModifiedAt:                 anaTS(now),
				TotalJournals30d:               10,
				AvgMoodScore30d:                anaNum("8.0"),
				MinMoodScore30d:                i32p(5),
				MaxMoodScore30d:                i32p(10),
				DailyStreak:                    7,
				PositivePercentage:             anaNum("60.0"),
				DaysSinceLastJournal:           i32p(0),
				DaysBetweenFirstAndLastJournal: i32p(30),
				JournalsPerActiveDay:           anaNum("1.25"),
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: userID.String()}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

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

	require.NotNil(t, summary.AvgMoodScore_30D)
	assert.Equal(t, 8.0, *summary.AvgMoodScore_30D)
	require.NotNil(t, summary.MinMoodScore_30D)
	assert.Equal(t, int32(5), *summary.MinMoodScore_30D)
	require.NotNil(t, summary.MaxMoodScore_30D)
	assert.Equal(t, int32(10), *summary.MaxMoodScore_30D)

	require.NotNil(t, summary.PositivePercentage)
	assert.Equal(t, 60.0, *summary.PositivePercentage)
	require.NotNil(t, summary.DaysSinceLastJournal)
	assert.Equal(t, int32(0), *summary.DaysSinceLastJournal)
	require.NotNil(t, summary.DaysBetweenFirstAndLastJournal)
	assert.Equal(t, int32(30), *summary.DaysBetweenFirstAndLastJournal)
	require.NotNil(t, summary.JournalsPerActiveDay)
	assert.Equal(t, 1.25, *summary.JournalsPerActiveDay)

	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 1)
}

func TestAnalyticsServer_GetUserJournalSummary_InvalidUserID(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{}
	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: "not-a-valid-uuid"}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 0)
}

func TestAnalyticsServer_GetUserJournalSummary_EmptyUserID(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{}
	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: ""}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 0)
}

func TestAnalyticsServer_GetUserJournalSummary_DBError(t *testing.T) {
	userID := uuid.New()
	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{}, errors.New("database connection failed")
		},
	}

	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: userID.String()}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to get user journal summary")
	assert.Len(t, mockQuerier.GetUserJournalSummaryByUserIdCalls(), 1)
}

func TestAnalyticsServer_GetUserJournalSummary_NotFound(t *testing.T) {
	userID := uuid.New()
	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{}, pgx.ErrNoRows
		},
	}

	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: userID.String()}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to get user journal summary")
}

func TestAnalyticsServer_GetUserJournalSummary_NullableFieldsAreNil(t *testing.T) {
	userID := uuid.New()
	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{
				UserID:                         anaUUID(userID),
				UserEmail:                      nil,
				UserRole:                       nil,
				UserTimezone:                   nil,
				UserCreatedAt:                  pgtype.Timestamp{},
				TotalJournals:                  0,
				ActiveDays:                     0,
				AvgMoodScore:                   pgtype.Numeric{},
				MinMoodScore:                   nil,
				MaxMoodScore:                   nil,
				MoodScoreStddev:                pgtype.Numeric{},
				PositiveEntries:                0,
				NegativeEntries:                0,
				NeutralEntries:                 0,
				AvgSentimentScore:              pgtype.Numeric{},
				AvgJournalLength:               pgtype.Numeric{},
				FirstJournalAt:                 pgtype.Timestamp{},
				LastJournalAt:                  pgtype.Timestamp{},
				LastModifiedAt:                 pgtype.Timestamp{},
				TotalJournals30d:               0,
				AvgMoodScore30d:                pgtype.Numeric{},
				MinMoodScore30d:                nil,
				MaxMoodScore30d:                nil,
				DailyStreak:                    0,
				PositivePercentage:             pgtype.Numeric{},
				DaysSinceLastJournal:           nil,
				DaysBetweenFirstAndLastJournal: nil,
				JournalsPerActiveDay:           pgtype.Numeric{},
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: userID.String()}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.Summary)

	summary := resp.Summary
	assert.Equal(t, userID.String(), summary.UserId)
	assert.Equal(t, "", summary.UserEmail)
	assert.Equal(t, "", summary.UserRole)
	assert.Equal(t, "", summary.UserTimezone)
	assert.Equal(t, "", summary.UserCreatedAt)
	assert.Equal(t, int32(0), summary.TotalJournals)
	assert.Equal(t, int32(0), summary.ActiveDays)
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
	userID := uuid.New()
	now := time.Now()

	mockQuerier := &mocks.QuerierMock{
		GetUserJournalSummaryByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GoldUserJournalSummary, error) {
			return db.GoldUserJournalSummary{
				UserID:                         anaUUID(userID),
				UserEmail:                      strp("partial@example.com"),
				UserRole:                       nil,
				UserTimezone:                   strp("UTC"),
				UserCreatedAt:                  pgtype.Timestamp{},
				TotalJournals:                  5,
				ActiveDays:                     3,
				AvgMoodScore:                   anaNum("6.5"),
				MinMoodScore:                   nil,
				MaxMoodScore:                   i32p(9),
				MoodScoreStddev:                pgtype.Numeric{},
				PositiveEntries:                3,
				NegativeEntries:                1,
				NeutralEntries:                 1,
				AvgSentimentScore:              pgtype.Numeric{},
				AvgJournalLength:               anaNum("100.0"),
				FirstJournalAt:                 anaTS(now.Add(-7 * 24 * time.Hour)),
				LastJournalAt:                  pgtype.Timestamp{},
				LastModifiedAt:                 anaTS(now),
				TotalJournals30d:               5,
				AvgMoodScore30d:                pgtype.Numeric{},
				MinMoodScore30d:                nil,
				MaxMoodScore30d:                nil,
				DailyStreak:                    3,
				PositivePercentage:             anaNum("60.0"),
				DaysSinceLastJournal:           nil,
				DaysBetweenFirstAndLastJournal: i32p(7),
				JournalsPerActiveDay:           pgtype.Numeric{},
			}, nil
		},
	}

	server := &internalgrpc.AnalyticsServer{}
	req := &pb.GetUserJournalSummaryRequest{UserId: userID.String()}

	resp, err := server.GetUserJournalSummary(analyticsTestCtx(mockQuerier), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.Summary)

	summary := resp.Summary
	assert.Equal(t, userID.String(), summary.UserId)
	assert.Equal(t, "partial@example.com", summary.UserEmail)
	assert.Equal(t, "", summary.UserRole)
	assert.Equal(t, "UTC", summary.UserTimezone)
	assert.Equal(t, "", summary.UserCreatedAt)
	assert.Equal(t, int32(5), summary.TotalJournals)
	assert.Equal(t, int32(3), summary.ActiveDays)
	assert.Equal(t, int32(5), summary.TotalJournals_30D)
	assert.Equal(t, int32(3), summary.DailyStreak)

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
