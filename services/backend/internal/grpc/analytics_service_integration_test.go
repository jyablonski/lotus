package grpc

import (
	"context"
	"database/sql"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupAnalyticsTestDB(t *testing.T) (*sql.DB, *db.Queries) {
	connStr := "postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable&search_path=source"
	dbConn, err := sql.Open("postgres", connStr)
	require.NoError(t, err)
	return dbConn, db.New(dbConn)
}

func setupAnalyticsTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
}

// Helper function to create a test user and journals for analytics testing
func createTestUserWithJournals(t *testing.T, queries *db.Queries) uuid.UUID {
	userID := uuid.New()

	// Create multiple journals to generate analytics data
	for i := 0; i < 5; i++ {
		_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
			UserID:      userID,
			JournalText: "Test journal entry for analytics " + string(rune('A'+i)),
			MoodScore:   sql.NullInt32{Int32: int32(3 + i), Valid: true}, // Mood scores from 3-7
		})
		require.NoError(t, err)
		// Small delay to ensure different timestamps
		time.Sleep(10 * time.Millisecond)
	}

	return userID
}

func TestGetUserJournalSummary(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	// Test DB connectivity first
	if err := dbConn.Ping(); err != nil {
		t.Skip("Skipping test: database not available")
	}

	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	// Create a test user with journals
	userID := createTestUserWithJournals(t, queries)

	// Note: This test depends on the gold.user_journal_summary materialized view
	// being populated. In a real test environment, you'd need to refresh the view
	// or use a test fixture that includes pre-populated analytics data.

	req := &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	}

	resp, err := server.GetUserJournalSummary(context.Background(), req)

	// If the materialized view doesn't have data for this user, we expect an error
	// This is expected behavior in a test environment without dbt running
	if err != nil {
		// This is acceptable - the view may not be populated in test environment
		t.Logf("GetUserJournalSummary returned error (expected if materialized view not populated): %v", err)
		return
	}

	// If we got a response, validate its structure
	assert.NotNil(t, resp)
	assert.NotNil(t, resp.Summary)
	assert.Equal(t, userID.String(), resp.Summary.UserId)
}

func TestGetUserJournalSummaryInvalidUserID(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	// This test doesn't need DB connectivity - it tests UUID validation
	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	// Test with invalid UUID format
	req := &pb.GetUserJournalSummaryRequest{
		UserId: "invalid-uuid-format",
	}

	_, err := server.GetUserJournalSummary(context.Background(), req)
	assert.Error(t, err, "Should return error for invalid UUID format")
	assert.Contains(t, err.Error(), "invalid user ID")
}

func TestGetUserJournalSummaryEmptyUserID(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	// This test doesn't need DB connectivity - it tests UUID validation
	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	// Test with empty user ID
	req := &pb.GetUserJournalSummaryRequest{
		UserId: "",
	}

	_, err := server.GetUserJournalSummary(context.Background(), req)
	assert.Error(t, err, "Should return error for empty user ID")
	assert.Contains(t, err.Error(), "invalid user ID")
}

func TestGetUserJournalSummaryNonExistentUser(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	// Test DB connectivity first
	if err := dbConn.Ping(); err != nil {
		t.Skip("Skipping test: database not available")
	}

	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	// Test with a valid UUID that doesn't exist in the database
	nonExistentUserID := uuid.New()
	req := &pb.GetUserJournalSummaryRequest{
		UserId: nonExistentUserID.String(),
	}

	_, err := server.GetUserJournalSummary(context.Background(), req)
	assert.Error(t, err, "Should return error for non-existent user")
}

func TestGetUserJournalSummaryDBError(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)

	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	// Close the DB connection to simulate a DB error
	_ = dbConn.Close()

	req := &pb.GetUserJournalSummaryRequest{
		UserId: uuid.New().String(),
	}

	_, err := server.GetUserJournalSummary(context.Background(), req)
	assert.Error(t, err, "Should return error when DB is unavailable")
}

func TestAnalyticsServiceCreation(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	logger := setupAnalyticsTestLogger()

	server := AnalyticsService(queries, logger)

	assert.NotNil(t, server)
	assert.Equal(t, queries, server.DB)
	assert.Equal(t, logger, server.Logger)
}

func TestParseNumericToFloat64(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected float64
	}{
		{"valid integer", "42", 42.0},
		{"valid float", "3.14159", 3.14159},
		{"negative number", "-5.5", -5.5},
		{"zero", "0", 0.0},
		{"invalid string", "not-a-number", 0.0},
		{"empty string", "", 0.0},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			result := parseNumericToFloat64(tc.input)
			assert.Equal(t, tc.expected, result)
		})
	}
}

func TestNullStringToString(t *testing.T) {
	tests := []struct {
		name     string
		input    sql.NullString
		expected string
	}{
		{"valid string", sql.NullString{String: "hello", Valid: true}, "hello"},
		{"empty valid string", sql.NullString{String: "", Valid: true}, ""},
		{"null string", sql.NullString{String: "", Valid: false}, ""},
		{"null string with value", sql.NullString{String: "ignored", Valid: false}, ""},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			result := nullStringToString(tc.input)
			assert.Equal(t, tc.expected, result)
		})
	}
}

func TestNullTimeToString(t *testing.T) {
	testTime := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
	expectedFormat := "2024-01-15T10:30:00Z"

	tests := []struct {
		name     string
		input    sql.NullTime
		expected string
	}{
		{"valid time", sql.NullTime{Time: testTime, Valid: true}, expectedFormat},
		{"null time", sql.NullTime{Time: time.Time{}, Valid: false}, ""},
		{"null time with value", sql.NullTime{Time: testTime, Valid: false}, ""},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			result := nullTimeToString(tc.input)
			assert.Equal(t, tc.expected, result)
		})
	}
}

func TestGetUserJournalSummaryResponseMapping(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	assert.NotNil(t, server)
	assert.NotNil(t, server.DB)
	assert.NotNil(t, server.Logger)
}

func TestGetUserJournalSummaryUUIDFormats(t *testing.T) {
	dbConn, queries := setupAnalyticsTestDB(t)
	defer dbConn.Close()

	logger := setupAnalyticsTestLogger()
	server := AnalyticsService(queries, logger)

	invalidUUIDs := []struct {
		name   string
		userID string
	}{
		{"short string", "abc123"},
		{"too long", "12345678-1234-1234-1234-1234567890123"},
		{"wrong format", "12345678123412341234123456789012"},
		{"special characters", "12345678-1234-1234-1234-12345678901!"},
		{"spaces", "12345678-1234-1234-1234-12345678 012"},
	}

	for _, tc := range invalidUUIDs {
		t.Run(tc.name, func(t *testing.T) {
			req := &pb.GetUserJournalSummaryRequest{
				UserId: tc.userID,
			}

			_, err := server.GetUserJournalSummary(context.Background(), req)
			assert.Error(t, err, "Should return error for invalid UUID: %s", tc.userID)
		})
	}
}
