package grpc

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/jobs"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
)

var (
	ErrInvalidMoodScore = errors.New("invalid mood score")
	ErrInvalidJournalID = errors.New("invalid journal ID")
	ErrJournalNotFound  = errors.New("journal not found")
)

type JournalServer struct {
	pb.UnimplementedJournalServiceServer
}

func (s *JournalServer) CreateJournal(ctx context.Context, req *pb.CreateJournalRequest) (*pb.CreateJournalResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	// parse mood_score from string to integer (1-10 scale)
	moodScore, err := strconv.Atoi(req.UserMood)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidMoodScore, err)
	}
	if moodScore < 1 || moodScore > 10 {
		return nil, fmt.Errorf("%w: must be 1-10, got %d", ErrInvalidMoodScore, moodScore)
	}

	// Extract deps after input validation.
	pgxPool := inject.PgxPoolFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	// Begin a pgx transaction so the journal row and the River job are either
	// both committed or both rolled back (transactional enqueue guarantee).
	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck — rollback is a no-op after commit

	// Insert the journal row directly via pgx (same SQL as the sqlc-generated query).
	var journalID int32
	err = tx.QueryRow(ctx,
		`INSERT INTO source.journals(user_id, journal_text, mood_score)
		 VALUES ($1, $2, $3)
		 RETURNING id`,
		userID, req.JournalText, moodScore,
	).Scan(&journalID)
	if err != nil {
		return nil, fmt.Errorf("failed to create journal: %w", err)
	}

	// Enqueue the analysis job in the same transaction.
	_, err = riverClient.InsertTx(ctx, tx, jobs.AnalyzeEntryArgs{
		EntryID: int64(journalID),
		UserID:  userID.String(),
		Content: req.JournalText,
	}, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to enqueue analysis job: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("commit transaction: %w", err)
	}

	return &pb.CreateJournalResponse{
		JournalId: strconv.Itoa(int(journalID)),
	}, nil
}

func (s *JournalServer) GetJournals(ctx context.Context, req *pb.GetJournalsRequest) (*pb.GetJournalsResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	// Extract deps after input validation
	dbq := inject.DBFrom(ctx)

	// set default pagination valuesba
	limit := req.Limit
	if limit <= 0 {
		limit = 50 // reasonable default
	}
	// optionally set max limit to prevent abuse
	if limit > 100 {
		limit = 100
	}

	offset := req.Offset
	if offset < 0 {
		offset = 0
	}

	// fetch total count and paginated journals (separate calls)
	totalCount, err := dbq.GetJournalCountByUserId(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get journal count: %w", err)
	}

	// Use the generated params struct
	journals, err := dbq.GetJournalsByUserIdPaginated(ctx, db.GetJournalsByUserIdPaginatedParams{
		UserID: userID,
		Limit:  limit,
		Offset: offset,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to fetch journals: %w", err)
	}

	// Fetch topics for these journals (async-populated by analyzer; may be empty)
	journalIDs := make([]int32, 0, len(journals))
	for _, j := range journals {
		journalIDs = append(journalIDs, j.ID)
	}
	topicsByJournal := hydrateTopics(ctx, dbq, journalIDs)

	// prepare journal entries for response
	var journalEntries []*pb.JournalEntry
	for _, j := range journals {
		entry := &pb.JournalEntry{
			JournalId:   strconv.Itoa(int(j.ID)),          // Integer journal_id as string
			UserId:      j.UserID.String(),                // UUID user_id as string
			JournalText: j.JournalText,                    // Journal text
			UserMood:    int32ToString(j.MoodScore.Int32), // Convert mood score to string
			CreatedAt:   j.CreatedAt.Format(time.RFC3339), // Convert to RFC3339 string
		}
		if names := topicsByJournal[j.ID]; len(names) > 0 {
			entry.TopicNames = names
		}
		journalEntries = append(journalEntries, entry)
	}

	// calculate if there are more results
	hasMore := int64(len(journalEntries)) == int64(limit) && (int64(offset)+int64(len(journalEntries))) < totalCount

	// return the paginated response
	return &pb.GetJournalsResponse{
		Journals:   journalEntries,
		TotalCount: totalCount,
		HasMore:    hasMore,
	}, nil
}

// TriggerJournalAnalysis manually re-enqueues an analysis job for an existing journal.
// Returns 200 immediately; River handles the async execution and retries.
func (s *JournalServer) TriggerJournalAnalysis(ctx context.Context, req *pb.TriggerAnalysisRequest) (*pb.TriggerAnalysisResponse, error) {
	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidJournalID, err)
	}

	dbq := inject.DBFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	journal, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
	}

	_, err = riverClient.Insert(ctx, jobs.AnalyzeEntryArgs{
		EntryID: int64(journal.ID),
		UserID:  journal.UserID.String(),
		Content: journal.JournalText,
	}, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to enqueue analysis job: %w", err)
	}

	return &pb.TriggerAnalysisResponse{
		Success: true,
		Message: "Analysis triggered successfully",
	}, nil
}

// formatVector converts a float64 slice to a pgvector-compatible string "[0.1,0.2,...]".
func formatVector(v []float64) string {
	parts := make([]string, len(v))
	for i, f := range v {
		parts[i] = strconv.FormatFloat(f, 'f', -1, 64)
	}
	return "[" + joinStrings(parts, ",") + "]"
}

func joinStrings(s []string, sep string) string {
	if len(s) == 0 {
		return ""
	}
	result := s[0]
	for _, v := range s[1:] {
		result += sep + v
	}
	return result
}

func int32ToString(val int32) string {
	return strconv.Itoa(int(val))
}
