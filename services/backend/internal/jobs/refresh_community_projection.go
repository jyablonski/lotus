package jobs

import (
	"context"
	"errors"
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

	var existing *db.SourceJournalCommunityProjection
	currentProjection, err := w.queries.GetJournalCommunityProjectionByJournalId(ctx, journalID)
	if err == nil {
		existing = &currentProjection
	} else if !errors.Is(err, pgx.ErrNoRows) {
		return fmt.Errorf("load existing community projection: %w", err)
	}

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

	if w.producer == nil {
		return nil
	}

	datesToRefresh := map[string]struct{}{}
	if existing != nil && existing.EntryLocalDate.Valid {
		datesToRefresh[existing.EntryLocalDate.Time.Format("2006-01-02")] = struct{}{}
	}
	if projection.HasEntryLocalDate {
		datesToRefresh[projection.EntryLocalDate.Format("2006-01-02")] = struct{}{}
	}

	for date := range datesToRefresh {
		if _, err := w.producer.Insert(ctx, RefreshCommunityRollupsArgs{
			AnchorDate: date,
		}, nil); err != nil {
			return fmt.Errorf("enqueue community rollup refresh for %s: %w", date, err)
		}
	}

	return nil
}
