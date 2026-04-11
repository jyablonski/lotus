package jobs

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
)

type RepairCommunityDataArgs struct {
	DaysBack int `json:"days_back"`
}

func (a RepairCommunityDataArgs) Kind() string { return "repair_community_data" }

func (a RepairCommunityDataArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue:       QueueCron,
		MaxAttempts: 3,
	}
}

type RepairCommunityDataWorker struct {
	river.WorkerDefaults[RepairCommunityDataArgs]
	queries  *db.Queries
	logger   *slog.Logger
	producer *river.Client[pgx.Tx]
}

func NewRepairCommunityDataWorker(queries *db.Queries, logger *slog.Logger, producer *river.Client[pgx.Tx]) *RepairCommunityDataWorker {
	return &RepairCommunityDataWorker{queries: queries, logger: logger, producer: producer}
}

func (w *RepairCommunityDataWorker) Work(ctx context.Context, job *river.Job[RepairCommunityDataArgs]) error {
	daysBack := job.Args.DaysBack
	if daysBack <= 0 {
		daysBack = 35
	}

	since := time.Now().UTC().AddDate(0, 0, -daysBack)
	journalIDs, err := w.queries.ListCommunityRepairJournalIds(ctx, pgtype.Timestamp{Time: since, Valid: true})
	if err != nil {
		return fmt.Errorf("list community repair journal ids: %w", err)
	}

	for _, journalID := range journalIDs {
		if _, err := w.producer.Insert(ctx, RefreshCommunityProjectionArgs{JournalID: int64(journalID)}, nil); err != nil {
			return fmt.Errorf("enqueue projection repair for %d: %w", journalID, err)
		}
	}

	return nil
}
