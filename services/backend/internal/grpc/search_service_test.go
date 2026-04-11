package grpc_test

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func semanticSearchCacheKey(userID, query string, limit int32) string {
	h := sha256.Sum256([]byte(query))
	return "search:semantic:" + userID + ":" + hex.EncodeToString(h[:8]) + ":" + strconv.Itoa(int(limit))
}

func keywordSearchCacheKey(userID, query string, limit int32) string {
	h := sha256.Sum256([]byte(query))
	return "search:keyword:" + userID + ":" + hex.EncodeToString(h[:8]) + ":" + strconv.Itoa(int(limit))
}

func vectorLiteral(values []float64) string {
	parts := make([]string, len(values))
	for i, value := range values {
		parts[i] = strconv.FormatFloat(value, 'f', -1, 64)
	}
	return "[" + strings.Join(parts, ",") + "]"
}

func TestKeywordSearchJournals_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	req := &pb.KeywordSearchJournalsRequest{
		UserId: "invalid-uuid",
		Query:  "test",
	}
	resp, err := server.KeywordSearchJournals(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestKeywordSearchJournals_EmptyQuery(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	ctx := journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient())
	ctx = withRiverDeps(ctx)

	req := &pb.KeywordSearchJournalsRequest{
		UserId: uuid.New().String(),
		Query:  "",
	}
	resp, err := server.KeywordSearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Empty(t, resp.Results)
}

func TestSearchJournals_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	req := &pb.SearchJournalsRequest{
		UserId: "invalid-uuid",
		Query:  "test",
	}
	resp, err := server.SearchJournals(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestSearchJournals_CacheHit(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	userID := uuid.New().String()
	req := &pb.SearchJournalsRequest{
		UserId: userID,
		Query:  "rest",
		Limit:  20,
	}

	ctx := journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient())
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	ctx = inject.WithAnalyzerAPIKey(ctx, "test-key")

	respPayload := &pb.SearchJournalsResponse{
		Results: []*pb.JournalSearchResult{
			{
				Journal: &pb.JournalEntry{
					JournalId:   "11",
					UserId:      userID,
					JournalText: "cached semantic result",
					UserMood:    "6",
					CreatedAt:   time.Now().UTC().Format(time.RFC3339),
				},
				SimilarityScore: 0.91,
			},
		},
	}
	encoded, err := json.Marshal(respPayload)
	require.NoError(t, err)

	cacheKey := semanticSearchCacheKey(userID, req.Query, req.Limit)
	require.NoError(t, testRedisClient.Set(context.Background(), cacheKey, encoded, time.Minute).Err())
	t.Cleanup(func() {
		_ = testRedisClient.Del(context.Background(), cacheKey).Err()
	})

	resp, err := server.SearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Len(t, resp.Results, 1)
	assert.Equal(t, "11", resp.Results[0].Journal.JournalId)
	assert.Equal(t, float32(0.91), resp.Results[0].SimilarityScore)
}

func TestKeywordSearchJournals_CacheHit(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	userID := uuid.New().String()
	req := &pb.KeywordSearchJournalsRequest{
		UserId: userID,
		Query:  "reset",
		Limit:  20,
	}

	ctx := journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient())
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)

	respPayload := &pb.KeywordSearchJournalsResponse{
		Results: []*pb.KeywordSearchResult{
			{
				Journal: &pb.JournalEntry{
					JournalId:   "12",
					UserId:      userID,
					JournalText: "cached keyword result",
					UserMood:    "8",
					CreatedAt:   time.Now().UTC().Format(time.RFC3339),
				},
				Rank: 0.77,
			},
		},
	}
	encoded, err := json.Marshal(respPayload)
	require.NoError(t, err)

	cacheKey := keywordSearchCacheKey(userID, req.Query, req.Limit)
	require.NoError(t, testRedisClient.Set(context.Background(), cacheKey, encoded, time.Minute).Err())
	t.Cleanup(func() {
		_ = testRedisClient.Del(context.Background(), cacheKey).Err()
	})

	resp, err := server.KeywordSearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Len(t, resp.Results, 1)
	assert.Equal(t, "12", resp.Results[0].Journal.JournalId)
	assert.Equal(t, float32(0.77), resp.Results[0].Rank)
}

func TestSearchJournals_EncodeRequestFailure(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	userID := uuid.New().String()

	httpMock := &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return nil, errors.New("network down")
		},
	}

	ctx := journalTestCtx(&mocks.QuerierMock{}, httpMock)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	ctx = inject.WithAnalyzerAPIKey(ctx, "test-key")

	resp, err := server.SearchJournals(ctx, &pb.SearchJournalsRequest{
		UserId: userID,
		Query:  "uncertainty",
		Limit:  20,
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "encode request failed")
}

func TestSearchJournals_AnalyzerBadStatus(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	userID := uuid.New().String()

	httpMock := &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusBadGateway,
				Body:       io.NopCloser(bytes.NewBufferString("bad gateway")),
			}, nil
		},
	}

	ctx := journalTestCtx(&mocks.QuerierMock{}, httpMock)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	ctx = inject.WithAnalyzerAPIKey(ctx, "test-key")

	resp, err := server.SearchJournals(ctx, &pb.SearchJournalsRequest{
		UserId: userID,
		Query:  "uncertainty",
		Limit:  20,
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "analyzer returned status 502")
}

func TestSearchJournals_EncodeDecodeFailure(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	userID := uuid.New().String()

	httpMock := &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(bytes.NewBufferString(`{"embedding":`)),
			}, nil
		},
	}

	ctx := journalTestCtx(&mocks.QuerierMock{}, httpMock)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	ctx = inject.WithAnalyzerAPIKey(ctx, "test-key")

	resp, err := server.SearchJournals(ctx, &pb.SearchJournalsRequest{
		UserId: userID,
		Query:  "uncertainty",
		Limit:  20,
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "decode encode response")
}

func TestSearchJournals_Success(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	queries := newDirectQueries(t)
	userID := createTestUser(t, queries)
	mood := int32(7)

	journal, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      pgtype.UUID{Bytes: userID, Valid: true},
		JournalText: "I need a little more rest this week.",
		MoodScore:   &mood,
	})
	require.NoError(t, err)

	vector := make([]float64, 384)
	vector[0] = 0.25
	vector[1] = 0.5
	vector[2] = 0.75
	vectorSQL := vectorLiteral(vector)

	_, err = testPgxPool.Exec(context.Background(),
		`INSERT INTO source.journal_embeddings (journal_id, embedding, model_version) VALUES ($1, $2::public.vector, $3)`,
		journal.ID, vectorSQL, "all-MiniLM-L6-v2",
	)
	require.NoError(t, err)

	t.Cleanup(func() {
		_, _ = testPgxPool.Exec(context.Background(), `DELETE FROM source.journal_embeddings WHERE journal_id = $1`, journal.ID)
		_, _ = queries.DeleteJournalForUser(context.Background(), db.DeleteJournalForUserParams{
			ID:     journal.ID,
			UserID: pgtype.UUID{Bytes: userID, Valid: true},
		})
		_ = queries.DeleteUserById(context.Background(), pgtype.UUID{Bytes: userID, Valid: true})
	})

	httpMock := &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			body, err := json.Marshal(map[string][]float64{"embedding": vector})
			require.NoError(t, err)
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(bytes.NewBuffer(body)),
			}, nil
		},
	}

	ctx := journalTestCtx(queries, httpMock)
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	ctx = inject.WithAnalyzerAPIKey(ctx, "test-key")

	req := &pb.SearchJournalsRequest{
		UserId: userID.String(),
		Query:  "rest",
		Limit:  10,
	}
	cacheKey := semanticSearchCacheKey(req.UserId, req.Query, req.Limit)
	_ = testRedisClient.Del(context.Background(), cacheKey).Err()

	resp, err := server.SearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Len(t, resp.Results, 1)
	assert.Equal(t, strconv.Itoa(int(journal.ID)), resp.Results[0].Journal.JournalId)
	assert.Equal(t, "I need a little more rest this week.", resp.Results[0].Journal.JournalText)
	assert.Equal(t, "7", resp.Results[0].Journal.UserMood)
	assert.Greater(t, resp.Results[0].SimilarityScore, float32(0))
}

func TestKeywordSearchJournals_Success(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	queries := newDirectQueries(t)
	userID := createTestUser(t, queries)
	mood := int32(8)

	journal, err := queries.CreateJournal(context.Background(), db.CreateJournalParams{
		UserID:      pgtype.UUID{Bytes: userID, Valid: true},
		JournalText: "I want to reset and rest before the weekend.",
		MoodScore:   &mood,
	})
	require.NoError(t, err)

	t.Cleanup(func() {
		_, _ = queries.DeleteJournalForUser(context.Background(), db.DeleteJournalForUserParams{
			ID:     journal.ID,
			UserID: pgtype.UUID{Bytes: userID, Valid: true},
		})
		_ = queries.DeleteUserById(context.Background(), pgtype.UUID{Bytes: userID, Valid: true})
	})

	ctx := journalTestCtx(queries, noopHTTPClient())
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRedisClient(ctx, testRedisClient)

	req := &pb.KeywordSearchJournalsRequest{
		UserId: userID.String(),
		Query:  "rest",
		Limit:  10,
	}
	cacheKey := keywordSearchCacheKey(req.UserId, req.Query, req.Limit)
	_ = testRedisClient.Del(context.Background(), cacheKey).Err()

	resp, err := server.KeywordSearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Len(t, resp.Results, 1)
	assert.Equal(t, strconv.Itoa(int(journal.ID)), resp.Results[0].Journal.JournalId)
	assert.Equal(t, "I want to reset and rest before the weekend.", resp.Results[0].Journal.JournalText)
	assert.Equal(t, "8", resp.Results[0].Journal.UserMood)
	assert.Greater(t, resp.Results[0].Rank, float32(0))
}
