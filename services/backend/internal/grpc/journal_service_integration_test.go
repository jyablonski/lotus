package grpc

import (
	"context"
	"database/sql"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"strconv"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db" // your sqlc generated package
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupTestDB(t *testing.T) (*sql.DB, *db.Queries) {
	connStr := "postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable&search_path=source"
	dbConn, err := sql.Open("postgres", connStr)
	require.NoError(t, err)
	return dbConn, db.New(dbConn)
}

func setupMockAnalyzerServer() *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check for correct HTTP methods based on endpoint
		if r.URL.Path == "/v1/journals/1/sentiment" && r.Method != "PUT" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Path == "/v1/journals/1/topics" && r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		// Mock successful response for both sentiment and topic analysis
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"success": true, "message": "Analysis completed"}`))
	}))
}

func setupFailingAnalyzerServer() *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check methods but still return error
		if r.URL.Path == "/v1/journals/1/sentiment" && r.Method != "PUT" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Path == "/v1/journals/1/topics" && r.Method != "POST" {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		// Mock failing response
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"error": "Analysis failed"}`))
	}))
}

func TestCreateJournal(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	server := JournalService(queries, logger, mockServer.URL)

	userID := uuid.New()
	userIDString := userID.String()
	req := &pb.CreateJournalRequest{
		UserId:      userIDString,
		JournalText: "This is a test journal entry",
		UserMood:    "7",
	}

	// call CreateJournal
	resp, err := server.CreateJournal(context.Background(), req)
	require.NoError(t, err)

	// Validate the response
	assert.NotEmpty(t, resp.JournalId, "Journal ID should not be empty")

	// Convert resp.JournalId (string) to int32
	journalID, err := strconv.Atoi(resp.JournalId) // Convert string to int
	require.NoError(t, err)

	// verify the journal is created in the database
	journals, err := queries.GetJournalsByUserId(context.Background(), userID)
	require.NoError(t, err)

	// find the journal we just created in the list of journals
	var createdJournal *db.SourceJournal
	for _, j := range journals {
		if j.ID == int32(journalID) { // Compare as int32
			createdJournal = &j
			break
		}
	}

	// ensure we found the created journal
	require.NotNil(t, createdJournal, "The created journal should be present in the fetched journals")

	// verify the created journal matches the input data
	assert.Equal(t, userID.String(), createdJournal.UserID.String(), "User ID should match")
	assert.Equal(t, "This is a test journal entry", createdJournal.JournalText, "Journal text should match")
	assert.Equal(t, int32(7), createdJournal.MoodScore.Int32, "Mood score should match")

	// Give async analysis a moment to complete (optional - tests the logging)
	time.Sleep(100 * time.Millisecond)
}

func TestCreateJournalWithFailingAnalyzer(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupFailingAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	server := JournalService(queries, logger, mockServer.URL)

	userID := uuid.New()
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "This journal will have failed analysis",
		UserMood:    "5",
	}

	// Journal creation should still succeed even if analysis fails
	resp, err := server.CreateJournal(context.Background(), req)
	require.NoError(t, err)
	assert.NotEmpty(t, resp.JournalId)

	// Verify journal was created despite analysis failure
	journals, err := queries.GetJournalsByUserId(context.Background(), userID)
	require.NoError(t, err)
	assert.Len(t, journals, 1)

	// Give async analysis time to fail
	time.Sleep(100 * time.Millisecond)
}

func TestCreateJournalWithInvalidAnalyzerURL(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	// Use invalid analyzer URL
	server := JournalService(queries, logger, "http://invalid-url:9999")

	userID := uuid.New()
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "This journal will have unreachable analyzer",
		UserMood:    "3",
	}

	// Journal creation should still succeed
	resp, err := server.CreateJournal(context.Background(), req)
	require.NoError(t, err)
	assert.NotEmpty(t, resp.JournalId)

	// Give async analysis time to fail
	time.Sleep(100 * time.Millisecond)
}

func TestGetJournals(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	server := JournalService(queries, logger, mockServer.URL)

	userID := uuid.New().String()
	_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      uuid.MustParse(userID),
		JournalText: "Test journal entry",
		MoodScore:   sql.NullInt32{Int32: 5, Valid: true},
	})
	require.NoError(t, err)

	// create request to get journals for the user
	req := &pb.GetJournalsRequest{
		UserId: userID,
	}

	// call GetJournals
	resp, err := server.GetJournals(context.Background(), req)
	require.NoError(t, err)

	// validate the response
	assert.NotNil(t, resp)
	assert.Len(t, resp.Journals, 1, "There should be 1 journal entry")
	assert.Equal(t, "Test journal entry", resp.Journals[0].JournalText, "Journal text should match")
	assert.Equal(t, "5", resp.Journals[0].UserMood, "Mood score should match")
}

func TestTriggerJournalAnalysis(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	server := JournalService(queries, logger, mockServer.URL)

	// First create a journal
	userID := uuid.New()
	journal, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      userID,
		JournalText: "Manual analysis test",
		MoodScore:   sql.NullInt32{Int32: 6, Valid: true},
	})
	require.NoError(t, err)

	// Test manual trigger
	req := &pb.TriggerAnalysisRequest{
		JournalId: strconv.Itoa(int(journal.ID)),
	}

	resp, err := server.TriggerJournalAnalysis(context.Background(), req)
	require.NoError(t, err)
	assert.True(t, resp.Success)
	assert.Equal(t, "Analysis triggered successfully", resp.Message)

	// Give async analysis time to complete
	time.Sleep(100 * time.Millisecond)
}

func TestTriggerJournalAnalysisInvalidID(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	server := JournalService(queries, logger, mockServer.URL)

	// Test with invalid journal ID
	req := &pb.TriggerAnalysisRequest{
		JournalId: "invalid-id",
	}

	_, err := server.TriggerJournalAnalysis(context.Background(), req)
	assert.Error(t, err, "Should return error for invalid journal ID")
}

func TestTriggerJournalAnalysisNonExistentJournal(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	server := JournalService(queries, logger, mockServer.URL)

	// Test with non-existent journal ID
	req := &pb.TriggerAnalysisRequest{
		JournalId: "99999", // Assuming this ID doesn't exist
	}

	_, err := server.TriggerJournalAnalysis(context.Background(), req)
	assert.Error(t, err, "Should return error for non-existent journal")
}

func TestCreateJournalInvalidUserID(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	server := JournalService(queries, logger, mockServer.URL)

	// invalid user ID (not a valid UUID)
	req := &pb.CreateJournalRequest{
		UserId:      "invalid-uuid",
		JournalText: "This is a test journal entry",
		UserMood:    "7",
	}

	// call CreateJournal
	_, err := server.CreateJournal(context.Background(), req)
	assert.Error(t, err, "Error should be returned for invalid user ID")
}

func TestGetJournalsInvalidUserID(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	server := JournalService(queries, logger, mockServer.URL)

	// invalid user ID (not a valid UUID)
	req := &pb.GetJournalsRequest{
		UserId: "invalid-uuid",
	}

	// call GetJournals
	_, err := server.GetJournals(context.Background(), req)
	assert.Error(t, err, "Error should be returned for invalid user ID")
}

func TestCreateJournalInvalidMoodScore(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	server := JournalService(queries, logger, mockServer.URL)

	req := &pb.CreateJournalRequest{
		UserId:      uuid.New().String(),
		JournalText: "Mood test",
		UserMood:    "not-a-number", // <-- invalid
	}

	_, err := server.CreateJournal(context.Background(), req)
	assert.Error(t, err, "Should return error for invalid mood score")
}

func TestCreateJournalDBError(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	server := JournalService(queries, logger, mockServer.URL)

	// put in a bad user mood score to trigger a DB error
	req := &pb.CreateJournalRequest{
		UserId:      uuid.New().String(),
		JournalText: "This will fail",
		UserMood:    "nil",
	}

	_, err := server.CreateJournal(context.Background(), req)
	assert.Error(t, err, "Should return error on DB failure")
}

func TestGetJournalsDBError(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	mockServer := setupMockAnalyzerServer()
	defer mockServer.Close()

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	server := JournalService(queries, logger, mockServer.URL)

	// Use a UUID with no journals (and trigger a query failure if possible)
	req := &pb.GetJournalsRequest{
		UserId: uuid.New().String(),
	}

	// Simulate DB error by closing the DB first (hacky)
	_ = dbConn.Close()

	_, err := server.GetJournals(context.Background(), req)
	assert.Error(t, err, "Should return error when DB is unavailable")
}
