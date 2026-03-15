package jobs

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/riverqueue/river"
)

// HelloCronArgs is the job args type for the hello-cron job.
type HelloCronArgs struct{}

func (h HelloCronArgs) Kind() string { return "hello_cron" }

func (h HelloCronArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue: QueueCron,
	}
}

// HelloCronWorker is a demonstration periodic job that writes timestamps to runtime_config.
type HelloCronWorker struct {
	river.WorkerDefaults[HelloCronArgs]
	queries db.Querier
	logger  *slog.Logger
}

// NewHelloCronWorker constructs a HelloCronWorker with the provided dependencies.
// Exposed so tests can create workers directly.
func NewHelloCronWorker(queries db.Querier, logger *slog.Logger) *HelloCronWorker {
	return &HelloCronWorker{queries: queries, logger: logger}
}

func (w *HelloCronWorker) Work(ctx context.Context, job *river.Job[HelloCronArgs]) error {
	w.logger.Info("hello cron: starting")

	if err := w.upsertTimestamp(ctx, "cron_job_triggered"); err != nil {
		return fmt.Errorf("upsert cron_job_triggered: %w", err)
	}

	if err := w.upsertTimestamp(ctx, "cron_job_finished"); err != nil {
		return fmt.Errorf("upsert cron_job_finished: %w", err)
	}

	w.logger.Info("hello cron: finished")

	return nil
}

func (w *HelloCronWorker) upsertTimestamp(ctx context.Context, key string) error {
	ts := time.Now().UTC().Format(time.RFC3339)
	val, err := json.Marshal(ts)
	if err != nil {
		return fmt.Errorf("marshal timestamp: %w", err)
	}

	_, err = w.queries.UpsertRuntimeConfigValue(ctx, db.UpsertRuntimeConfigValueParams{
		Key:         key,
		Value:       val,
		Service:     "backend",
		Description: "set by hello_cron worker",
	})
	return err
}
