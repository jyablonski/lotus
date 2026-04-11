package jobs

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/jackc/pgx/v5"
	"github.com/jyablonski/lotus/internal/community"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
)

type RefreshCommunityProjectionArgs struct {
	JournalID int64 `json:"journal_id"`
}

func (a RefreshCommunityProjectionArgs) Kind() string { return "refresh_community_projection" }

func (a RefreshCommunityProjectionArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue:       river.QueueDefault,
		MaxAttempts: 5,
	}
}

type RefreshCommunityProjectionWorker struct {
	river.WorkerDefaults[RefreshCommunityProjectionArgs]
	queries  *db.Queries
	logger   *slog.Logger
	producer *river.Client[pgx.Tx]
}

func NewRefreshCommunityProjectionWorker(queries *db.Queries, logger *slog.Logger, producer *river.Client[pgx.Tx]) *RefreshCommunityProjectionWorker {
	return &RefreshCommunityProjectionWorker{
		queries:  queries,
		logger:   logger,
		producer: producer,
	}
}

func (w *RefreshCommunityProjectionWorker) Work(ctx context.Context, job *river.Job[RefreshCommunityProjectionArgs]) error {
	journalID := int32(job.Args.JournalID)

	source, err := w.queries.GetCommunityProjectionSourceByJournalId(ctx, journalID)
	if err != nil {
		return fmt.Errorf("load community projection source: %w", err)
	}

	projection := community.BuildProjection(source)
	_, err = w.queries.UpsertJournalCommunityProjection(ctx, db.UpsertJournalCommunityProjectionParams{
		JournalID:            projection.JournalID,
		UserID:               projection.UserID,
		EligibleForCommunity: projection.EligibleForCommunity,
		EntryLocalDate:       community.NullablePgDate(projection.EntryLocalDate, projection.HasEntryLocalDate),
		PrimaryMood:          projection.PrimaryMood,
		PrimarySentiment:     projection.PrimarySentiment,
		ThemeNames:           projection.ThemeNames,
		CountryCode:          projection.CountryCode,
		RegionCode:           projection.RegionCode,
		AnalysisVersion:      projection.AnalysisVersion,
	})
	if err != nil {
		return fmt.Errorf("upsert community projection: %w", err)
	}

	return nil
}
