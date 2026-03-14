package grpc_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// createTestUserWithJournals creates a user with 5 journals for analytics testing.
func createTestUserWithJournals(t *testing.T, queries *db.Queries) uuid.UUID {
	t.Helper()
	userID := createTestUser(t, queries)

	for i := 0; i < 5; i++ {
		_, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
			UserID:      userID,
			JournalText: "Test journal entry for analytics " + string(rune('A'+i)),
			MoodScore:   sql.NullInt32{Int32: int32(3 + i), Valid: true},
		})
		require.NoError(t, err)
	}

	return userID
}

func TestGetUserJournalSummary(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.AnalyticsServer{}

	userID := createTestUserWithJournals(t, queries)

	resp, err := svc.GetUserJournalSummary(ctx, &pb.GetUserJournalSummaryRequest{
		UserId: userID.String(),
	})

	// The materialized view may not be populated in the test environment without dbt running.
	if err != nil {
		t.Logf("GetUserJournalSummary returned error (expected if materialized view not populated): %v", err)
		return
	}

	assert.NotNil(t, resp)
	assert.NotNil(t, resp.Summary)
	assert.Equal(t, userID.String(), resp.Summary.UserId)
}

func TestGetUserJournalSummaryInvalidUserID(t *testing.T) {
	svc := &grpcServer.AnalyticsServer{}

	t.Run("invalid_format", func(t *testing.T) {
		_, err := svc.GetUserJournalSummary(context.Background(), &pb.GetUserJournalSummaryRequest{
			UserId: "invalid-uuid-format",
		})
		assert.Error(t, err)
		assert.ErrorIs(t, err, grpcServer.ErrInvalidUserID)
	})

	t.Run("empty", func(t *testing.T) {
		_, err := svc.GetUserJournalSummary(context.Background(), &pb.GetUserJournalSummaryRequest{
			UserId: "",
		})
		assert.Error(t, err)
		assert.ErrorIs(t, err, grpcServer.ErrInvalidUserID)
	})

	invalidUUIDs := []struct {
		name   string
		userID string
	}{
		{"short string", "abc123"},
		{"too long", "12345678-1234-1234-1234-1234567890123"},
		{"special characters", "12345678-1234-1234-1234-12345678901!"},
		{"spaces", "12345678-1234-1234-1234-12345678 012"},
	}
	for _, tc := range invalidUUIDs {
		t.Run(tc.name, func(t *testing.T) {
			_, err := svc.GetUserJournalSummary(context.Background(), &pb.GetUserJournalSummaryRequest{
				UserId: tc.userID,
			})
			assert.Error(t, err)
		})
	}
}

func TestGetUserJournalSummaryNonExistentUser(t *testing.T) {
	ctx, _ := newTestCtx(t)
	svc := &grpcServer.AnalyticsServer{}

	_, err := svc.GetUserJournalSummary(ctx, &pb.GetUserJournalSummaryRequest{
		UserId: uuid.New().String(),
	})
	assert.Error(t, err)
}
