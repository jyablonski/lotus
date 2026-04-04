package jobs

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
)

// ExportJournalsArgs holds the parameters for a journal export job.
type ExportJournalsArgs struct {
	ExportID string `json:"export_id"` // UUID
	UserID   string `json:"user_id"`   // UUID as string
}

func (a ExportJournalsArgs) Kind() string { return "export_journals" }

func (a ExportJournalsArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue:       QueueExport,
		MaxAttempts: 3,
	}
}

// ExportJournalsWorker fetches all journals for a user, builds CSV or Markdown content,
// and stores the result in the journal_exports table.
type ExportJournalsWorker struct {
	river.WorkerDefaults[ExportJournalsArgs]
	queries db.Querier
	logger  *slog.Logger
}

func (w *ExportJournalsWorker) Work(ctx context.Context, job *river.Job[ExportJournalsArgs]) error {
	exportID, err := uuid.Parse(job.Args.ExportID)
	if err != nil {
		return fmt.Errorf("parse export_id: %w", err)
	}
	userID, err := uuid.Parse(job.Args.UserID)
	if err != nil {
		return fmt.Errorf("parse user_id: %w", err)
	}

	w.logger.Info("export_journals: starting",
		"export_id", exportID,
		"user_id", userID,
		"attempt", job.Attempt,
	)

	export, err := w.queries.UpdateJournalExportProcessing(ctx, exportID)
	if err != nil {
		return fmt.Errorf("mark processing: %w", err)
	}

	content, err := w.buildContent(ctx, userID, export.Format)
	if err != nil {
		w.logger.Error("export_journals: build failed",
			"export_id", exportID,
			"error", err,
		)
		if job.Attempt >= job.MaxAttempts {
			_, _ = w.queries.UpdateJournalExportFailed(ctx, db.UpdateJournalExportFailedParams{
				ID:       exportID,
				ErrorMsg: sql.NullString{String: err.Error(), Valid: true},
			})
		}
		return fmt.Errorf("build content: %w", err)
	}

	_, err = w.queries.UpdateJournalExportComplete(ctx, db.UpdateJournalExportCompleteParams{
		ID:      exportID,
		Content: sql.NullString{String: content, Valid: true},
	})
	if err != nil {
		return fmt.Errorf("mark complete: %w", err)
	}

	w.logger.Info("export_journals: finished",
		"export_id", exportID,
		"attempt", job.Attempt,
	)

	return nil
}

func (w *ExportJournalsWorker) buildContent(ctx context.Context, userID uuid.UUID, format db.SourceExportFormat) (string, error) {
	journals, err := w.queries.GetJournalsByUserId(ctx, userID)
	if err != nil {
		return "", fmt.Errorf("fetch journals: %w", err)
	}

	journalIDs := make([]int32, 0, len(journals))
	for _, j := range journals {
		journalIDs = append(journalIDs, j.ID)
	}

	topicsByJournal := make(map[int32][]string)
	if len(journalIDs) > 0 {
		topicRows, err := w.queries.GetTopicsByJournalIds(ctx, journalIDs)
		if err == nil {
			for _, row := range topicRows {
				topicsByJournal[row.JournalID] = append(topicsByJournal[row.JournalID], row.TopicName)
			}
		}
	}

	switch format {
	case db.SourceExportFormatMarkdown:
		return buildMarkdown(journals, topicsByJournal), nil
	default:
		return buildCSV(journals), nil
	}
}

func buildCSV(journals []db.SourceJournal) string {
	var sb strings.Builder
	sb.WriteString("id,created_at,mood,text\n")
	for _, j := range journals {
		mood := ""
		if j.MoodScore.Valid {
			mood = strconv.Itoa(int(j.MoodScore.Int32))
		}
		row := strings.Join([]string{
			strconv.Itoa(int(j.ID)),
			j.CreatedAt.Format(time.RFC3339),
			mood,
			escapeCsvField(j.JournalText),
		}, ",")
		sb.WriteString(row)
		sb.WriteByte('\n')
	}
	return sb.String()
}

func buildMarkdown(journals []db.SourceJournal, topicsByJournal map[int32][]string) string {
	var sb strings.Builder
	sb.WriteString("# Lotus journal export\n\n")
	fmt.Fprintf(&sb, "Exported at: %s\n\n---\n\n", time.Now().UTC().Format(time.RFC3339))

	for _, j := range journals {
		mood := ""
		if j.MoodScore.Valid {
			mood = strconv.Itoa(int(j.MoodScore.Int32))
		}
		fmt.Fprintf(&sb, "## %s — Mood %s\n", j.CreatedAt.Format(time.RFC3339), mood)
		if topics := topicsByJournal[j.ID]; len(topics) > 0 {
			fmt.Fprintf(&sb, "Topics: %s\n", strings.Join(topics, ", "))
		}
		sb.WriteByte('\n')
		sb.WriteString(j.JournalText)
		sb.WriteString("\n\n---\n\n")
	}

	return sb.String()
}

func escapeCsvField(s string) string {
	if strings.ContainsAny(s, "\",\n\r") {
		return `"` + strings.ReplaceAll(s, `"`, `""`) + `"`
	}
	return s
}
