package grpc

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
)

type AnalyticsServer struct {
	pb.UnimplementedAnalyticsServiceServer
	DB     *db.Queries
	Logger *slog.Logger
}

func AnalyticsService(q *db.Queries, logger *slog.Logger) *AnalyticsServer {
	return &AnalyticsServer{
		DB:     q,
		Logger: logger,
	}
}

func (s *AnalyticsServer) GetUserJournalSummary(ctx context.Context, req *pb.GetUserJournalSummaryRequest) (*pb.GetUserJournalSummaryResponse, error) {
	// Parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	// Fetch the user journal summary from the database
	summary, err := s.DB.GetUserJournalSummaryByUserId(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user journal summary: %w", err)
	}

	// Convert database model to protobuf response
	pbSummary := &pb.UserJournalSummary{
		UserId:            summary.UserID.String(),
		UserEmail:         nullStringToString(summary.UserEmail),
		UserRole:          nullStringToString(summary.UserRole),
		UserTimezone:      nullStringToString(summary.UserTimezone),
		UserCreatedAt:     nullTimeToString(summary.UserCreatedAt),
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
		val := parseNumericToFloat64(summary.AvgMoodScore.String)
		pbSummary.AvgMoodScore = &val
	}
	if summary.MinMoodScore.Valid {
		val := summary.MinMoodScore.Int32
		pbSummary.MinMoodScore = &val
	}
	if summary.MaxMoodScore.Valid {
		val := summary.MaxMoodScore.Int32
		pbSummary.MaxMoodScore = &val
	}
	if summary.MoodScoreStddev.Valid {
		val := parseNumericToFloat64(summary.MoodScoreStddev.String)
		pbSummary.MoodScoreStddev = &val
	}
	if summary.AvgSentimentScore.Valid {
		val := parseNumericToFloat64(summary.AvgSentimentScore.String)
		pbSummary.AvgSentimentScore = &val
	}
	if summary.AvgJournalLength.Valid {
		val := parseNumericToFloat64(summary.AvgJournalLength.String)
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
		val := parseNumericToFloat64(summary.AvgMoodScore30d.String)
		pbSummary.AvgMoodScore_30D = &val
	}
	if summary.MinMoodScore30d.Valid {
		val := summary.MinMoodScore30d.Int32
		pbSummary.MinMoodScore_30D = &val
	}
	if summary.MaxMoodScore30d.Valid {
		val := summary.MaxMoodScore30d.Int32
		pbSummary.MaxMoodScore_30D = &val
	}

	// Handle calculated fields
	if summary.PositivePercentage.Valid {
		val := parseNumericToFloat64(summary.PositivePercentage.String)
		pbSummary.PositivePercentage = &val
	}
	if summary.DaysSinceLastJournal.Valid {
		val := summary.DaysSinceLastJournal.Int32
		pbSummary.DaysSinceLastJournal = &val
	}
	if summary.DaysBetweenFirstAndLastJournal.Valid {
		val := summary.DaysBetweenFirstAndLastJournal.Int32
		pbSummary.DaysBetweenFirstAndLastJournal = &val
	}
	if summary.JournalsPerActiveDay.Valid {
		val := parseNumericToFloat64(summary.JournalsPerActiveDay.String)
		pbSummary.JournalsPerActiveDay = &val
	}

	return &pb.GetUserJournalSummaryResponse{
		Summary: pbSummary,
	}, nil
}

// Helper function to parse numeric string to float64
func parseNumericToFloat64(s string) float64 {
	val, err := strconv.ParseFloat(s, 64)
	if err != nil {
		return 0
	}
	return val
}

// Helper function to convert sql.NullString to string
func nullStringToString(ns sql.NullString) string {
	if ns.Valid {
		return ns.String
	}
	return ""
}

// Helper function to convert sql.NullTime to RFC3339 string
func nullTimeToString(nt sql.NullTime) string {
	if nt.Valid {
		return nt.Time.Format(time.RFC3339)
	}
	return ""
}
