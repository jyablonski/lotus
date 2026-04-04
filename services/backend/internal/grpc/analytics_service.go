package grpc

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
)

type AnalyticsServer struct {
	pb.UnimplementedAnalyticsServiceServer
}

func (s *AnalyticsServer) GetUserJournalSummary(ctx context.Context, req *pb.GetUserJournalSummaryRequest) (*pb.GetUserJournalSummaryResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	dbq := inject.DBFrom(ctx)

	summary, err := dbq.GetUserJournalSummaryByUserId(ctx, pgtype.UUID{Bytes: userID, Valid: true})
	if err != nil {
		return nil, fmt.Errorf("failed to get user journal summary: %w", err)
	}

	pbSummary := &pb.UserJournalSummary{
		UserId:            uuid.UUID(summary.UserID.Bytes).String(),
		UserEmail:         derefString(summary.UserEmail),
		UserRole:          derefString(summary.UserRole),
		UserTimezone:      derefString(summary.UserTimezone),
		UserCreatedAt:     pgTimestampToString(summary.UserCreatedAt),
		TotalJournals:     summary.TotalJournals,
		ActiveDays:        summary.ActiveDays,
		PositiveEntries:   summary.PositiveEntries,
		NegativeEntries:   summary.NegativeEntries,
		NeutralEntries:    summary.NeutralEntries,
		TotalJournals_30D: summary.TotalJournals30d,
		DailyStreak:       summary.DailyStreak,
	}

	// Handle nullable numeric fields
	if summary.AvgMoodScore.Valid {
		val := numericToFloat64(summary.AvgMoodScore)
		pbSummary.AvgMoodScore = &val
	}
	if summary.MinMoodScore != nil {
		pbSummary.MinMoodScore = summary.MinMoodScore
	}
	if summary.MaxMoodScore != nil {
		pbSummary.MaxMoodScore = summary.MaxMoodScore
	}
	if summary.MoodScoreStddev.Valid {
		val := numericToFloat64(summary.MoodScoreStddev)
		pbSummary.MoodScoreStddev = &val
	}
	if summary.AvgSentimentScore.Valid {
		val := numericToFloat64(summary.AvgSentimentScore)
		pbSummary.AvgSentimentScore = &val
	}
	if summary.AvgJournalLength.Valid {
		val := numericToFloat64(summary.AvgJournalLength)
		pbSummary.AvgJournalLength = &val
	}

	// Handle nullable timestamp fields
	if summary.FirstJournalAt.Valid {
		val := summary.FirstJournalAt.Time.Format(time.RFC3339)
		pbSummary.FirstJournalAt = &val
	}
	if summary.LastJournalAt.Valid {
		val := summary.LastJournalAt.Time.Format(time.RFC3339)
		pbSummary.LastJournalAt = &val
	}
	if summary.LastModifiedAt.Valid {
		val := summary.LastModifiedAt.Time.Format(time.RFC3339)
		pbSummary.LastModifiedAt = &val
	}

	// Handle 30-day metrics
	if summary.AvgMoodScore30d.Valid {
		val := numericToFloat64(summary.AvgMoodScore30d)
		pbSummary.AvgMoodScore_30D = &val
	}
	if summary.MinMoodScore30d != nil {
		pbSummary.MinMoodScore_30D = summary.MinMoodScore30d
	}
	if summary.MaxMoodScore30d != nil {
		pbSummary.MaxMoodScore_30D = summary.MaxMoodScore30d
	}

	// Handle calculated fields
	if summary.PositivePercentage.Valid {
		val := numericToFloat64(summary.PositivePercentage)
		pbSummary.PositivePercentage = &val
	}
	if summary.DaysSinceLastJournal != nil {
		pbSummary.DaysSinceLastJournal = summary.DaysSinceLastJournal
	}
	if summary.DaysBetweenFirstAndLastJournal != nil {
		pbSummary.DaysBetweenFirstAndLastJournal = summary.DaysBetweenFirstAndLastJournal
	}
	if summary.JournalsPerActiveDay.Valid {
		val := numericToFloat64(summary.JournalsPerActiveDay)
		pbSummary.JournalsPerActiveDay = &val
	}

	return &pb.GetUserJournalSummaryResponse{
		Summary: pbSummary,
	}, nil
}

// numericToFloat64 converts a pgtype.Numeric to float64, returning 0 if invalid.
func numericToFloat64(n pgtype.Numeric) float64 {
	if !n.Valid {
		return 0
	}
	v, err := n.Value()
	if err != nil || v == nil {
		return 0
	}
	str, ok := v.(string)
	if !ok {
		return 0
	}
	val, _ := strconv.ParseFloat(str, 64)
	return val
}

// derefString returns the string value of a pointer, or "" if nil.
func derefString(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// pgTimestampToString formats a pgtype.Timestamp as RFC3339, or "" if invalid.
func pgTimestampToString(ts pgtype.Timestamp) string {
	if !ts.Valid {
		return ""
	}
	return ts.Time.Format(time.RFC3339)
}
