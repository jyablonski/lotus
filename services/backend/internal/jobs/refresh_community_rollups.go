package jobs

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/community"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
)

type RefreshCommunityRollupsArgs struct {
	AnchorDate string `json:"anchor_date"`
}

func (a RefreshCommunityRollupsArgs) Kind() string { return "refresh_community_rollups" }

func (a RefreshCommunityRollupsArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue:       river.QueueDefault,
		MaxAttempts: 5,
	}
}

type RefreshCommunityRollupsWorker struct {
	river.WorkerDefaults[RefreshCommunityRollupsArgs]
	queries *db.Queries
	logger  *slog.Logger
}

func NewRefreshCommunityRollupsWorker(queries *db.Queries, logger *slog.Logger) *RefreshCommunityRollupsWorker {
	return &RefreshCommunityRollupsWorker{queries: queries, logger: logger}
}

func (w *RefreshCommunityRollupsWorker) Work(ctx context.Context, job *river.Job[RefreshCommunityRollupsArgs]) error {
	anchorDate, err := time.Parse("2006-01-02", job.Args.AnchorDate)
	if err != nil {
		return fmt.Errorf("parse anchor date: %w", err)
	}

	for _, grain := range []string{community.TimeGrainDay, community.TimeGrainWeek, community.TimeGrainMonth} {
		bucketDate := community.BucketForDate(anchorDate, grain)
		windowStart, windowEnd := community.WindowForBucket(bucketDate, grain)
		prevStart, prevEnd := community.PreviousWindowForBucket(bucketDate, grain)

		current, err := community.LoadProjectionsForWindow(ctx, w.queries, windowStart, windowEnd)
		if err != nil {
			return fmt.Errorf("load current projections for %s: %w", grain, err)
		}
		previous, err := community.LoadProjectionsForWindow(ctx, w.queries, prevStart, prevEnd)
		if err != nil {
			return fmt.Errorf("load previous projections for %s: %w", grain, err)
		}

		if err := w.persistRefresh(ctx, bucketDate, grain, current, previous); err != nil {
			return err
		}
	}

	return nil
}

func (w *RefreshCommunityRollupsWorker) persistRefresh(ctx context.Context, bucketDate time.Time, grain string, current, previous []db.SourceJournalCommunityProjection) error {
	if err := w.queries.DeleteCommunityThemeRollupsForBucket(ctx, db.DeleteCommunityThemeRollupsForBucketParams{
		BucketDate: community.PgDate(bucketDate),
		TimeGrain:  grain,
	}); err != nil {
		return fmt.Errorf("delete theme rollups for %s: %w", grain, err)
	}
	if err := w.queries.DeleteCommunityMoodRollupsForBucket(ctx, db.DeleteCommunityMoodRollupsForBucketParams{
		BucketDate: community.PgDate(bucketDate),
		TimeGrain:  grain,
	}); err != nil {
		return fmt.Errorf("delete mood rollups for %s: %w", grain, err)
	}
	if err := w.queries.DeleteCommunitySummariesForBucket(ctx, db.DeleteCommunitySummariesForBucketParams{
		BucketDate: community.PgDate(bucketDate),
		TimeGrain:  grain,
	}); err != nil {
		return fmt.Errorf("delete summaries for %s: %w", grain, err)
	}
	if err := w.queries.DeleteCommunityPromptSetsForBucket(ctx, db.DeleteCommunityPromptSetsForBucketParams{
		BucketDate: community.PgDate(bucketDate),
		TimeGrain:  grain,
	}); err != nil {
		return fmt.Errorf("delete prompt sets for %s: %w", grain, err)
	}

	refresh := community.BuildRollupForGrain(bucketDate, grain, current, previous)
	for _, scope := range refresh.Scopes {
		for _, metric := range scope.ThemeMetrics {
			if _, err := w.queries.UpsertCommunityThemeRollup(ctx, db.UpsertCommunityThemeRollupParams{
				BucketDate:      community.PgDate(refresh.BucketDate),
				TimeGrain:       refresh.TimeGrain,
				ScopeType:       scope.ScopeType,
				ScopeValue:      scope.ScopeValue,
				ThemeName:       metric.Name,
				EntryCount:      int32(metric.EntryCount),
				UniqueUserCount: int32(metric.UniqueUserCount),
				Rank:            int32(metric.Rank),
				DeltaVsPrevious: numericFromDelta(metric.DeltaVsPrevious),
			}); err != nil {
				return fmt.Errorf("upsert theme rollup %s/%s: %w", scope.ScopeType, metric.Name, err)
			}
		}

		for _, metric := range scope.MoodMetrics {
			if _, err := w.queries.UpsertCommunityMoodRollup(ctx, db.UpsertCommunityMoodRollupParams{
				BucketDate:      community.PgDate(refresh.BucketDate),
				TimeGrain:       refresh.TimeGrain,
				ScopeType:       scope.ScopeType,
				ScopeValue:      scope.ScopeValue,
				MoodName:        metric.Name,
				EntryCount:      int32(metric.EntryCount),
				UniqueUserCount: int32(metric.UniqueUserCount),
				Rank:            int32(metric.Rank),
				DeltaVsPrevious: numericFromDelta(metric.DeltaVsPrevious),
			}); err != nil {
				return fmt.Errorf("upsert mood rollup %s/%s: %w", scope.ScopeType, metric.Name, err)
			}
		}

		if scope.SummaryText != "" {
			if _, err := w.queries.UpsertCommunitySummary(ctx, db.UpsertCommunitySummaryParams{
				BucketDate:       community.PgDate(refresh.BucketDate),
				TimeGrain:        refresh.TimeGrain,
				ScopeType:        scope.ScopeType,
				ScopeValue:       scope.ScopeValue,
				SummaryText:      scope.SummaryText,
				SourceThemeNames: scope.SourceThemes,
				SourceMoodNames:  scope.SourceMoods,
				GenerationMethod: community.GenerationMethodTemplate,
			}); err != nil {
				return fmt.Errorf("upsert summary %s/%s: %w", scope.ScopeType, scope.ScopeValue, err)
			}
		}

		if len(scope.PromptSet) > 0 {
			if _, err := w.queries.UpsertCommunityPromptSet(ctx, db.UpsertCommunityPromptSetParams{
				BucketDate:       community.PgDate(refresh.BucketDate),
				TimeGrain:        refresh.TimeGrain,
				ScopeType:        scope.ScopeType,
				ScopeValue:       scope.ScopeValue,
				PromptSetJson:    db.MustJSON(scope.PromptSet),
				SourceThemeNames: scope.SourceThemes,
				SourceMoodNames:  scope.SourceMoods,
				GenerationMethod: community.GenerationMethodTemplate,
			}); err != nil {
				return fmt.Errorf("upsert prompt set %s/%s: %w", scope.ScopeType, scope.ScopeValue, err)
			}
		}
	}

	return nil
}

func numericFromDelta(delta *float64) pgtype.Numeric {
	if delta == nil {
		return pgtype.Numeric{}
	}
	var value pgtype.Numeric
	_ = value.Scan(fmt.Sprintf("%.4f", *delta))
	return value
}
