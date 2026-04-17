package grpc

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
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
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	moodScore, err := strconv.Atoi(req.UserMood)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidMoodScore, err)
	}
	if moodScore < 1 || moodScore > 10 {
		return nil, fmt.Errorf("%w: must be 1-10, got %d", ErrInvalidMoodScore, moodScore)
	}

	pgxPool := inject.PgxPoolFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	// Begin a pgx transaction so the journal row and the River job are either
	// both committed or both rolled back (transactional enqueue guarantee).
	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

	ms := int32(moodScore)
	journal, err := db.New(tx).CreateJournal(ctx, db.CreateJournalParams{
		UserID:      pgtype.UUID{Bytes: userID, Valid: true},
		JournalText: req.JournalText,
		MoodScore:   &ms,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create journal: %w", err)
	}
	journalID := journal.ID

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
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	dbq := inject.DBFrom(ctx)

	limit := req.Limit
	if limit <= 0 {
		limit = 50
	}
	if limit > 100 {
		limit = 100
	}

	offset := req.Offset
	if offset < 0 {
		offset = 0
	}

	pgUserID := pgtype.UUID{Bytes: userID, Valid: true}

	totalCount, err := dbq.GetJournalCountByUserId(ctx, pgUserID)
	if err != nil {
		return nil, fmt.Errorf("failed to get journal count: %w", err)
	}

	journals, err := dbq.GetJournalsByUserIdPaginated(ctx, db.GetJournalsByUserIdPaginatedParams{
		UserID: pgUserID,
		Limit:  limit,
		Offset: offset,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to fetch journals: %w", err)
	}

	// Topics are populated asynchronously by the analyzer and may be empty.
	journalIDs := make([]int32, 0, len(journals))
	for _, j := range journals {
		journalIDs = append(journalIDs, j.ID)
	}
	topicsByJournal := hydrateTopics(ctx, dbq, journalIDs)

	var journalEntries []*pb.JournalEntry
	for _, j := range journals {
		entry := sourceJournalToPB(j, topicsByJournal[j.ID])
		journalEntries = append(journalEntries, entry)
	}

	hasMore := int64(len(journalEntries)) == int64(limit) && (int64(offset)+int64(len(journalEntries))) < totalCount

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
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
		}
		return nil, fmt.Errorf("failed to load journal: %w", err)
	}
	if uuid.UUID(j.UserID.Bytes) != userID {
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
	pgxPool := inject.PgxPoolFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

	ms := int32(moodScore)
	n, err := db.New(tx).UpdateJournalForUser(ctx, db.UpdateJournalForUserParams{
		JournalText: req.JournalText,
		MoodScore:   &ms,
		ID:          int32(journalID),
		UserID:      pgtype.UUID{Bytes: userID, Valid: true},
	})
	if err != nil {
		return nil, fmt.Errorf("failed to update journal: %w", err)
	}
	if n == 0 {
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

	n, err := inject.DBFrom(ctx).DeleteJournalForUser(ctx, db.DeleteJournalForUserParams{
		ID:     int32(journalID),
		UserID: pgtype.UUID{Bytes: userID, Valid: true},
	})
	if err != nil {
		return nil, fmt.Errorf("failed to delete journal: %w", err)
	}
	if n == 0 {
		return nil, ErrJournalNotFound
	}

	return &pb.DeleteJournalResponse{Success: true}, nil
}

func (s *JournalServer) RequestJournalExport(ctx context.Context, req *pb.RequestJournalExportRequest) (*pb.RequestJournalExportResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	var format db.SourceExportFormat
	switch req.Format {
	case "markdown":
		format = db.SourceExportFormatMarkdown
	case "csv", "":
		format = db.SourceExportFormatCsv
	default:
		return nil, fmt.Errorf("unsupported export format: %s", req.Format)
	}

	pgxPool := inject.PgxPoolFrom(ctx)
	riverClient := inject.RiverClientFrom(ctx)

	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

	export, err := db.New(tx).CreateJournalExport(ctx, db.CreateJournalExportParams{
		UserID: pgtype.UUID{Bytes: userID, Valid: true},
		Format: format,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create export record: %w", err)
	}

	_, err = riverClient.InsertTx(ctx, tx, jobs.ExportJournalsArgs{
		ExportID: export.ID.String(),
		UserID:   userID.String(),
	}, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to enqueue export job: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("commit transaction: %w", err)
	}

	return &pb.RequestJournalExportResponse{
		ExportId: export.ID.String(),
		Status:   string(export.Status),
	}, nil
}

func (s *JournalServer) GetJournalExport(ctx context.Context, req *pb.GetJournalExportRequest) (*pb.GetJournalExportResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	exportID, err := uuid.Parse(req.ExportId)
	if err != nil {
		return nil, fmt.Errorf("invalid export_id: %w", err)
	}

	dbq := inject.DBFrom(ctx)
	export, err := dbq.GetJournalExport(ctx, db.GetJournalExportParams{
		ID:     pgtype.UUID{Bytes: exportID, Valid: true},
		UserID: pgtype.UUID{Bytes: userID, Valid: true},
	})
	if err != nil {
		return nil, fmt.Errorf("export not found: %w", err)
	}

	resp := &pb.GetJournalExportResponse{
		ExportId: export.ID.String(),
		Status:   string(export.Status),
	}

	if export.Status == db.SourceExportStatusComplete && export.Content != nil {
		resp.Content = *export.Content
		date := ""
		if export.CreatedAt.Valid {
			date = export.CreatedAt.Time.Format("2006-01-02")
		}
		switch export.Format {
		case db.SourceExportFormatMarkdown:
			resp.Filename = "lotus-journal-export-" + date + ".md"
			resp.MimeType = "text/markdown;charset=utf-8"
		default:
			resp.Filename = "lotus-journal-export-" + date + ".csv"
			resp.MimeType = "text/csv;charset=utf-8"
		}
	}

	return resp, nil
}

// sourceJournalToPB maps a DB row to a protobuf JournalEntry.
func sourceJournalToPB(j db.SourceJournal, topicNames []string) *pb.JournalEntry {
	mood := ""
	if j.MoodScore != nil {
		mood = int32ToString(*j.MoodScore)
	}
	createdAt := ""
	if j.CreatedAt.Valid {
		createdAt = j.CreatedAt.Time.Format(time.RFC3339)
	}
	entry := &pb.JournalEntry{
		JournalId:   strconv.Itoa(int(j.ID)),
		UserId:      j.UserID.String(),
		JournalText: j.JournalText,
		UserMood:    mood,
		CreatedAt:   createdAt,
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
