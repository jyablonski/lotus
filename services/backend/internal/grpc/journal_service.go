package grpc

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db" // your sqlc generated package
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
)

type JournalServer struct {
	pb.UnimplementedJournalServiceServer
	DB              *db.Queries
	Logger          *slog.Logger
	HTTPClient      *http.Client
	AnalyzerBaseURL string
}

// AnalysisRequest represents the request body for analysis endpoints
type AnalysisRequest struct {
	ForceReanalyze bool `json:"force_reanalyze,omitempty"`
}

func JournalService(q *db.Queries, logger *slog.Logger, analyzerBaseURL string) *JournalServer {
	return &JournalServer{
		DB:     q,
		Logger: logger,
		HTTPClient: &http.Client{
			Timeout: 10 * time.Second, // Set reasonable timeout
		},
		AnalyzerBaseURL: analyzerBaseURL, // e.g., "http://localhost:8083"
	}
}

func (s *JournalServer) CreateJournal(ctx context.Context, req *pb.CreateJournalRequest) (*pb.CreateJournalResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	// parse mood_score from string to integer
	moodScore, err := strconv.Atoi(req.UserMood)
	if err != nil {
		return nil, fmt.Errorf("invalid mood score: %w", err)
	}

	// prepare parameters for database insertion
	params := db.CreateJournalParams{
		UserID:      userID,                  // UUID type for user_id
		JournalText: req.JournalText,         // Text from the request
		MoodScore:   sqlNullInt32(moodScore), // Handle nullable mood score
	}

	journal, err := s.DB.CreateJournal(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to create journal: %w", err)
	}

	journalID := strconv.Itoa(int(journal.ID))

	// Trigger async sentiment + topic analysis after journal is created (don't wait for completion)
	go s.triggerAnalysis(int(journal.ID))

	return &pb.CreateJournalResponse{
		JournalId: journalID,
	}, nil
}

func (s *JournalServer) GetJournals(ctx context.Context, req *pb.GetJournalsRequest) (*pb.GetJournalsResponse, error) {
	// parse user_id from string to UUID
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID: %w", err)
	}

	// fetch journals from the database using the user_id (UUID)
	journals, err := s.DB.GetJournalsByUserId(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch journals: %w", err)
	}

	// prepare journal entries for response
	var journalEntries []*pb.JournalEntry
	for _, j := range journals {
		journalEntries = append(journalEntries, &pb.JournalEntry{
			JournalId:   strconv.Itoa(int(j.ID)),          // Integer journal_id as string
			UserId:      j.UserID.String(),                // UUID user_id as string
			JournalText: j.JournalText,                    // Journal text
			UserMood:    int32ToString(j.MoodScore.Int32), // Convert mood score to string
			CreatedAt:   j.CreatedAt.Format(time.RFC3339), // Convert to RFC3339 string
		})
	}

	// return the list of journal entries
	return &pb.GetJournalsResponse{
		Journals: journalEntries,
	}, nil
}

// triggerAnalysis sends async requests to the analyzer service
func (s *JournalServer) triggerAnalysis(journalID int) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Trigger sentiment analysis
	if err := s.callAnalysisEndpoint(ctx, journalID, "sentiment"); err != nil {
		s.Logger.Error("Failed to trigger sentiment analysis",
			"journal_id", journalID,
			"error", err,
		)
	} else {
		s.Logger.Info("Successfully triggered sentiment analysis",
			"journal_id", journalID,
		)
	}

	// Trigger topic classification
	if err := s.callAnalysisEndpoint(ctx, journalID, "topics"); err != nil {
		s.Logger.Error("Failed to trigger topic classification",
			"journal_id", journalID,
			"error", err,
		)
	} else {
		s.Logger.Info("Successfully triggered topic classification",
			"journal_id", journalID,
		)
	}
}

// callAnalysisEndpoint makes HTTP request to analysis service
func (s *JournalServer) callAnalysisEndpoint(ctx context.Context, journalID int, analysisType string) error {
	// Prepare request body
	requestBody := AnalysisRequest{
		ForceReanalyze: false, // Set to true if you want to force reanalysis
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request body: %w", err)
	}

	// Build URL
	url := fmt.Sprintf("%s/v1/journals/%d/openai/%s", s.AnalyzerBaseURL, journalID, analysisType)

	// Determine HTTP method based on analysis type
	var method string
	if analysisType == "sentiment" {
		method = "PUT" // sentiment uses PUT
	} else if analysisType == "topics" {
		method = "POST" // topics uses POST
	} else {
		return fmt.Errorf("unknown analysis type: %s", analysisType)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// Make the request
	resp, err := s.HTTPClient.Do(req)
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

// Optional: Add method to manually trigger analysis for existing journals
func (s *JournalServer) TriggerJournalAnalysis(ctx context.Context, req *pb.TriggerAnalysisRequest) (*pb.TriggerAnalysisResponse, error) {
	journalID, err := strconv.Atoi(req.JournalId)
	if err != nil {
		return nil, fmt.Errorf("invalid journal ID: %w", err)
	}

	// Verify journal exists
	journal, err := s.DB.GetJournalById(ctx, int32(journalID))
	if err != nil {
		return nil, fmt.Errorf("journal not found: %w", err)
	}

	// Trigger analysis in background
	go s.triggerAnalysis(int(journal.ID))

	return &pb.TriggerAnalysisResponse{
		Success: true,
		Message: "Analysis triggered successfully",
	}, nil
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
