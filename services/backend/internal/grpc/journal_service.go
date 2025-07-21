package grpc

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db" // your sqlc generated package
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
)

type JournalServer struct {
	pb.UnimplementedJournalServiceServer
	DB     *db.Queries
	Logger *slog.Logger
}

func JournalService(q *db.Queries, logger *slog.Logger) *JournalServer {
	return &JournalServer{
		DB:     q,
		Logger: logger,
	}
}

func (s *JournalServer) CreateJournal(ctx context.Context, req *pb.CreateJournalRequest) (*pb.CreateJournalResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	// parse mood_score from string to integer
	moodScore, err := strconv.Atoi(req.UserMood)
	if err != nil {
		return nil, fmt.Errorf("invalid mood score: %w", err)
	}

	// prepare parameters for database insertion
	params := db.CreateJournalParams{
		UserID:      userID,                  // UUID type for user_id
		JournalText: req.JournalText,         // Text from the request
		MoodScore:   sqlNullInt32(moodScore), // Handle nullable mood score
	}

	journal, err := s.DB.CreateJournal(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to create journal: %w", err)
	}

	return &pb.CreateJournalResponse{
		JournalId: strconv.Itoa(int(journal.ID)), // Convert integer ID to string
	}, nil
}

func (s *JournalServer) GetJournals(ctx context.Context, req *pb.GetJournalsRequest) (*pb.GetJournalsResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	// fetch journals from the database using the user_id (UUID)
	journals, err := s.DB.GetJournalsByUserId(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch journals: %w", err)
	}

	// prepare journal entries for response
	var journalEntries []*pb.JournalEntry
	for _, j := range journals {
		journalEntries = append(journalEntries, &pb.JournalEntry{
			JournalId:   strconv.Itoa(int(j.ID)),          // Integer journal_id as string
			UserId:      j.UserID.String(),                // UUID user_id as string
			JournalText: j.JournalText,                    // Journal text
			UserMood:    int32ToString(j.MoodScore.Int32), // Convert mood score to string
			CreatedAt:   j.CreatedAt.Format(time.RFC3339), // Convert to RFC3339 string
		})
	}

	// return the list of journal entries
	return &pb.GetJournalsResponse{
		Journals: journalEntries,
	}, nil
}

// Helper functions

func int32ToString(val int32) string {
	return strconv.Itoa(int(val))
}

func sqlNullInt32(val int) sql.NullInt32 {
	return sql.NullInt32{
		Int32: int32(val),
		Valid: true,
	}
}
