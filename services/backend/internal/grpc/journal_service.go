package grpc

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
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
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

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

	// set default pagination values
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
		entry := sourceJournalToPB(j, topicsByJournal[j.ID])
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

func (s *JournalServer) GetJournal(ctx context.Context, req *pb.GetJournalRequest) (*pb.GetJournalResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidJournalID, err)
	}

	dbq := inject.DBFrom(ctx)
	j, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
		}
		return nil, fmt.Errorf("failed to load journal: %w", err)
	}
	if j.UserID != userID {
		return nil, ErrJournalForbidden
	}

	topicsByJournal := hydrateTopics(ctx, dbq, []int32{j.ID})
	return &pb.GetJournalResponse{
		Journal: sourceJournalToPB(j, topicsByJournal[j.ID]),
	}, nil
}

func (s *JournalServer) UpdateJournal(ctx context.Context, req *pb.UpdateJournalRequest) (*pb.UpdateJournalResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidJournalID, err)
	}

	if strings.TrimSpace(req.JournalText) == "" {
		return nil, ErrEmptyJournalText
	}

	moodScore, err := strconv.Atoi(req.UserMood)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidMoodScore, err)
	}
	if moodScore < 1 || moodScore > 10 {
		return nil, fmt.Errorf("%w: must be 1-10, got %d", ErrInvalidMoodScore, moodScore)
	}

	dbq := inject.DBFrom(ctx)
	existing, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
		}
		return nil, fmt.Errorf("failed to load journal: %w", err)
	}
	if existing.UserID != userID {
		return nil, ErrJournalForbidden
	}

	pgxPool := inject.PgxPoolFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

	cmdTag, err := tx.Exec(ctx,
		`UPDATE source.journals SET journal_text = $1, mood_score = $2, modified_at = NOW()
		 WHERE id = $3 AND user_id = $4`,
		req.JournalText, moodScore, int32(journalID), userID,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to update journal: %w", err)
	}
	if cmdTag.RowsAffected() == 0 {
		return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, pgx.ErrNoRows)
	}

	_, err = riverClient.InsertTx(ctx, tx, jobs.AnalyzeEntryArgs{
		EntryID: int64(journalID),
		UserID:  userID.String(),
	}, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to enqueue analysis job: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("commit transaction: %w", err)
	}

	j, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		return nil, fmt.Errorf("failed to reload journal: %w", err)
	}
	topicsByJournal := hydrateTopics(ctx, dbq, []int32{j.ID})
	return &pb.UpdateJournalResponse{
		Journal: sourceJournalToPB(j, topicsByJournal[j.ID]),
	}, nil
}

func (s *JournalServer) DeleteJournal(ctx context.Context, req *pb.DeleteJournalRequest) (*pb.DeleteJournalResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidJournalID, err)
	}

	dbq := inject.DBFrom(ctx)
	j, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
		}
		return nil, fmt.Errorf("failed to load journal: %w", err)
	}
	if j.UserID != userID {
		return nil, ErrJournalForbidden
	}

	n, err := dbq.DeleteJournalForUser(ctx, db.DeleteJournalForUserParams{
		ID:     int32(journalID),
		UserID: userID,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to delete journal: %w", err)
	}
	if n == 0 {
		return nil, ErrJournalNotFound
	}

	return &pb.DeleteJournalResponse{Success: true}, nil
}

// sourceJournalToPB maps a DB row to a protobuf JournalEntry.
func sourceJournalToPB(j db.SourceJournal, topicNames []string) *pb.JournalEntry {
	mood := ""
	if j.MoodScore.Valid {
		mood = int32ToString(j.MoodScore.Int32)
	}
	entry := &pb.JournalEntry{
		JournalId:   strconv.Itoa(int(j.ID)),
		UserId:      j.UserID.String(),
		JournalText: j.JournalText,
		UserMood:    mood,
		CreatedAt:   j.CreatedAt.Format(time.RFC3339),
	}
	if len(topicNames) > 0 {
		entry.TopicNames = topicNames
	}
	return entry
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
	return "[" + strings.Join(parts, ",") + "]"
}

func int32ToString(val int32) string {
	return strconv.Itoa(int(val))
}
