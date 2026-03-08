package grpc

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
)

var (
	ErrInvalidMoodScore    = errors.New("invalid mood score")
	ErrInvalidJournalID    = errors.New("invalid journal ID")
	ErrJournalNotFound     = errors.New("journal not found")
	ErrUnknownAnalysisType = errors.New("unknown analysis type")
)

type JournalServer struct {
	pb.UnimplementedJournalServiceServer
}

// AnalysisRequest represents the request body for analysis endpoints
type AnalysisRequest struct {
	ForceReanalyze bool `json:"force_reanalyze,omitempty"`
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

	// Extract deps after input validation
	dbq := inject.DBFrom(ctx)
	logger := inject.LoggerFrom(ctx)
	httpClient := inject.HTTPClientFrom(ctx)
	analyzerURL := inject.AnalyzerURLFrom(ctx)

	// prepare parameters for database insertion
	params := db.CreateJournalParams{
		UserID:      userID,                  // UUID type for user_id
		JournalText: req.JournalText,         // Text from the request
		MoodScore:   sqlNullInt32(moodScore), // Handle nullable mood score
	}

	journal, err := dbq.CreateJournal(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to create journal: %w", err)
	}

	journalID := strconv.Itoa(int(journal.ID))

	// Trigger async sentiment + topic analysis after journal is created (don't wait for completion).
	// Capture deps into local variables before spawning the goroutine.
	go triggerAnalysis(httpClient, analyzerURL, logger, int(journal.ID))

	return &pb.CreateJournalResponse{
		JournalId: journalID,
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

	// set default pagination valuesba
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
	topicsByJournal := make(map[int32][]string)
	if len(journalIDs) > 0 {
		topicRows, topicErr := dbq.GetTopicsByJournalIds(ctx, journalIDs)
		if topicErr == nil {
			for _, row := range topicRows {
				topicsByJournal[row.JournalID] = append(topicsByJournal[row.JournalID], row.TopicName)
			}
		}
	}

	// prepare journal entries for response
	var journalEntries []*pb.JournalEntry
	for _, j := range journals {
		entry := &pb.JournalEntry{
			JournalId:   strconv.Itoa(int(j.ID)),          // Integer journal_id as string
			UserId:      j.UserID.String(),                // UUID user_id as string
			JournalText: j.JournalText,                    // Journal text
			UserMood:    int32ToString(j.MoodScore.Int32), // Convert mood score to string
			CreatedAt:   j.CreatedAt.Format(time.RFC3339), // Convert to RFC3339 string
		}
		if names := topicsByJournal[j.ID]; len(names) > 0 {
			entry.TopicNames = names
		}
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

// TriggerJournalAnalysis manually triggers analysis for an existing journal.
func (s *JournalServer) TriggerJournalAnalysis(ctx context.Context, req *pb.TriggerAnalysisRequest) (*pb.TriggerAnalysisResponse, error) {
	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidJournalID, err)
	}

	// Extract deps after input validation
	dbq := inject.DBFrom(ctx)
	logger := inject.LoggerFrom(ctx)
	httpClient := inject.HTTPClientFrom(ctx)
	analyzerURL := inject.AnalyzerURLFrom(ctx)

	// Verify journal exists
	journal, err := dbq.GetJournalById(ctx, int32(journalID))
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrJournalNotFound, err)
	}

	// Trigger analysis in background
	go triggerAnalysis(httpClient, analyzerURL, logger, int(journal.ID))

	return &pb.TriggerAnalysisResponse{
		Success: true,
		Message: "Analysis triggered successfully",
	}, nil
}

// triggerAnalysis sends async requests to the analyzer service.
// It is a standalone function that receives all dependencies as arguments
// so it can safely run in a goroutine after the request context is gone.
func triggerAnalysis(client inject.HTTPDoer, analyzerURL string, logger *slog.Logger, journalID int) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Trigger sentiment analysis
	if err := callAnalysisEndpoint(ctx, client, analyzerURL, journalID, "sentiment"); err != nil {
		logger.Error("Failed to trigger sentiment analysis",
			"journal_id", journalID,
			"error", err,
		)
	} else {
		logger.Info("Successfully triggered sentiment analysis",
			"journal_id", journalID,
		)
	}

	// Trigger topic classification
	if err := callAnalysisEndpoint(ctx, client, analyzerURL, journalID, "topics"); err != nil {
		logger.Error("Failed to trigger topic classification",
			"journal_id", journalID,
			"error", err,
		)
	} else {
		logger.Info("Successfully triggered topic classification",
			"journal_id", journalID,
		)
	}
}

// callAnalysisEndpoint makes HTTP request to analysis service.
func callAnalysisEndpoint(ctx context.Context, client inject.HTTPDoer, analyzerBaseURL string, journalID int, analysisType string) error {
	// Prepare request body
	requestBody := AnalysisRequest{
		ForceReanalyze: false, // Set to true if you want to force reanalysis
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request body: %w", err)
	}

	// Build URL
	url := fmt.Sprintf("%s/v1/journals/%d/openai/%s", analyzerBaseURL, journalID, analysisType)

	// Determine HTTP method based on analysis type
	var method string
	if analysisType == "sentiment" {
		// adjust URL for sentiment endpoint
		url = strings.TrimSuffix(url, "/openai/sentiment") + "/sentiment"
		method = "PUT" // sentiment uses PUT
	} else if analysisType == "topics" {
		method = "POST" // topics uses POST
	} else {
		return fmt.Errorf("%w: %s", ErrUnknownAnalysisType, analysisType)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// Make the request
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("analysis request failed with status %d", resp.StatusCode)
	}

	return nil
}

// Helper functions

func int32ToString(val int32) string {
	return strconv.Itoa(int(val))
}

func sqlNullInt32(val int) sql.NullInt32 {
	return sql.NullInt32{
		Int32: int32(val),
		Valid: true,
	}
}
