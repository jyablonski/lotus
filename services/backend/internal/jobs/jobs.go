package jobs

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverpgxv5"
	"github.com/riverqueue/river/rivermigrate"
)

const (
	QueueAnalysis = "analysis"
	QueueCron     = "cron"
)

// RunMigrations applies River's internal schema migrations (river_job, river_leader, etc.)
// against the provided pool. Safe to call on every startup — already-applied versions are skipped.
func RunMigrations(ctx context.Context, pool *pgxpool.Pool, logger *slog.Logger) error {
	migrator, err := rivermigrate.New(riverpgxv5.New(pool), &rivermigrate.Config{
		Logger: logger,
	})
	if err != nil {
		return fmt.Errorf("create river migrator: %w", err)
	}

	res, err := migrator.Migrate(ctx, rivermigrate.DirectionUp, nil)
	if err != nil {
		return fmt.Errorf("run river migrations: %w", err)
	}

	if logger != nil {
		for _, v := range res.Versions {
			logger.Info("Applied River migration", "version", v.Version, "direction", "up")
		}
	}

	return nil
}

// NewClient creates a fully-configured River client with all workers and the
// hello_cron periodic job scheduled every 15 minutes.
// The caller is responsible for calling Start and Stop on the returned client.
func NewClient(
	pool *pgxpool.Pool,
	queries db.Querier,
	httpClient *http.Client,
	analyzerURL string,
	analyzerAPIKey string,
	logger *slog.Logger,
) (*river.Client[pgx.Tx], error) {
	return NewClientWithPeriodicInterval(pool, queries, httpClient, analyzerURL, analyzerAPIKey, logger, 15*time.Minute)
}

// NewClientWithPeriodicInterval is like NewClient but allows overriding the hello_cron
// schedule. Useful in tests where a 15-minute interval would be impractical.
func NewClientWithPeriodicInterval(
	pool *pgxpool.Pool,
	queries db.Querier,
	httpClient *http.Client,
	analyzerURL string,
	analyzerAPIKey string,
	logger *slog.Logger,
	cronInterval time.Duration,
) (*river.Client[pgx.Tx], error) {
	workers := river.NewWorkers()

	river.AddWorker(workers, &AnalyzeEntryWorker{
		httpClient:     httpClient,
		analyzerURL:    analyzerURL,
		analyzerAPIKey: analyzerAPIKey,
		logger:         logger,
	})

	river.AddWorker(workers, &HelloCronWorker{
		queries: queries,
		logger:  logger,
	})

	client, err := river.NewClient(riverpgxv5.New(pool), &river.Config{
		Queues: map[string]river.QueueConfig{
			river.QueueDefault: {MaxWorkers: 50},
			QueueAnalysis:      {MaxWorkers: 10},
			QueueCron:          {MaxWorkers: 5},
		},
		Workers: workers,
		PeriodicJobs: []*river.PeriodicJob{
			river.NewPeriodicJob(
				river.PeriodicInterval(cronInterval),
				func() (river.JobArgs, *river.InsertOpts) {
					return HelloCronArgs{}, nil
				},
				&river.PeriodicJobOpts{RunOnStart: true},
			),
		},
		Logger: logger,
	})
	if err != nil {
		return nil, fmt.Errorf("create river client: %w", err)
	}

	return client, nil
}

// NewInsertOnlyClient creates a River client suitable for enqueueing jobs without starting
// any workers. Useful in tests and for services that only produce jobs.
func NewInsertOnlyClient(pool *pgxpool.Pool) (*river.Client[pgx.Tx], error) {
	client, err := river.NewClient(riverpgxv5.New(pool), &river.Config{})
	if err != nil {
		return nil, fmt.Errorf("create river insert-only client: %w", err)
	}
	return client, nil
}
