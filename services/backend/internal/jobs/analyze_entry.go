package jobs

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"

	"github.com/riverqueue/river"
)

// AnalyzeEntryArgs holds the parameters for an analysis job.
type AnalyzeEntryArgs struct {
	EntryID int64  `json:"entry_id"`
	UserID  string `json:"user_id"` // UUID as string
	Content string `json:"content"`
}

func (a AnalyzeEntryArgs) Kind() string { return "analyze_entry" }

func (a AnalyzeEntryArgs) InsertOpts() river.InsertOpts {
	return river.InsertOpts{
		Queue:       QueueAnalysis,
		MaxAttempts: 5,
	}
}

// AnalyzeEntryWorker calls the Python analyzer service to run sentiment and topic
// analysis for a journal entry. On success River marks the job complete; on error
// River schedules a retry with exponential backoff (up to InsertOpts.MaxAttempts).
type AnalyzeEntryWorker struct {
	river.WorkerDefaults[AnalyzeEntryArgs]
	httpClient     *http.Client
	analyzerURL    string
	analyzerAPIKey string
	logger         *slog.Logger
}

// NewAnalyzeEntryWorker constructs an AnalyzeEntryWorker with the provided dependencies.
// Exposed so tests can create workers with custom HTTP servers.
func NewAnalyzeEntryWorker(httpClient *http.Client, analyzerURL, analyzerAPIKey string, logger *slog.Logger) *AnalyzeEntryWorker {
	return &AnalyzeEntryWorker{httpClient: httpClient, analyzerURL: analyzerURL, analyzerAPIKey: analyzerAPIKey, logger: logger}
}

func (w *AnalyzeEntryWorker) Work(ctx context.Context, job *river.Job[AnalyzeEntryArgs]) error {
	w.logger.Info("analyze_entry: starting",
		"entry_id", job.Args.EntryID,
		"user_id", job.Args.UserID,
		"attempt", job.Attempt,
	)

	if err := w.callEndpoint(ctx, job.Args.EntryID, "topics", http.MethodPost); err != nil {
		return fmt.Errorf("topic analysis failed: %w", err)
	}

	w.logger.Info("analyze_entry: finished",
		"entry_id", job.Args.EntryID,
		"attempt", job.Attempt,
	)

	return nil
}

type analysisRequest struct {
	ForceReanalyze bool `json:"force_reanalyze,omitempty"`
}

func (w *AnalyzeEntryWorker) callEndpoint(ctx context.Context, entryID int64, analysisType, method string) error {
	body, err := json.Marshal(analysisRequest{})
	if err != nil {
		return fmt.Errorf("marshal request: %w", err)
	}

	url := fmt.Sprintf("%s/v1/journals/%d/%s/internal", w.analyzerURL, entryID, analysisType)

	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+w.analyzerAPIKey)

	resp, err := w.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("http request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("analyzer returned status %d", resp.StatusCode)
	}

	return nil
}
