package grpc

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
)

const searchCacheTTL = 4 * time.Hour

// searchRow holds a single result from either semantic or keyword search.
type searchRow struct {
	ID          int32
	JournalText string
	MoodScore   *int32
	CreatedAt   time.Time
	Score       float64
}

// hydrateTopics fetches topic names for the given journal IDs.
func hydrateTopics(ctx context.Context, dbq db.Querier, journalIDs []int32) map[int32][]string {
	topicsByJournal := make(map[int32][]string)
	if len(journalIDs) == 0 {
		return topicsByJournal
	}
	topicRows, err := dbq.GetTopicsByJournalIds(ctx, journalIDs)
	if err != nil {
		return topicsByJournal
	}
	for _, row := range topicRows {
		topicsByJournal[row.JournalID] = append(topicsByJournal[row.JournalID], row.TopicName)
	}
	return topicsByJournal
}

// buildJournalEntry creates a protobuf JournalEntry from search result fields.
func buildJournalEntry(userID string, r searchRow, topics []string) *pb.JournalEntry {
	mood := ""
	if r.MoodScore != nil {
		mood = strconv.Itoa(int(*r.MoodScore))
	}
	entry := &pb.JournalEntry{
		JournalId:   strconv.Itoa(int(r.ID)),
		UserId:      userID,
		JournalText: r.JournalText,
		UserMood:    mood,
		CreatedAt:   r.CreatedAt.Format(time.RFC3339),
	}
	if len(topics) > 0 {
		entry.TopicNames = topics
	}
	return entry
}

// searchCacheKey builds a deterministic Redis key for search result caching.
func searchCacheKey(prefix, userID, query string, limit int32) string {
	h := sha256.Sum256([]byte(query))
	return fmt.Sprintf("search:%s:%s:%s:%d", prefix, userID, hex.EncodeToString(h[:8]), limit)
}

// clampLimit normalises a user-supplied limit to [1, 100] with a given default.
func clampLimit(limit, defaultLimit int32) int32 {
	if limit <= 0 {
		return defaultLimit
	}
	if limit > 100 {
		return 100
	}
	return limit
}

// SearchJournals performs semantic search over a user's journal entries.
// It encodes the query text via the analyzer, then runs a pgvector cosine
// similarity search directly against the database.
func (s *JournalServer) SearchJournals(ctx context.Context, req *pb.SearchJournalsRequest) (*pb.SearchJournalsResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	httpClient := inject.HTTPClientFrom(ctx)
	analyzerURL := inject.AnalyzerURLFrom(ctx)
	analyzerAPIKey := inject.AnalyzerAPIKeyFrom(ctx)
	pgxPool := inject.PgxPoolFrom(ctx)
	dbq := inject.DBFrom(ctx)
	rdb := inject.RedisClientFrom(ctx)
	logger := inject.LoggerFrom(ctx)

	limit := clampLimit(req.Limit, 20)

	// Check Redis cache first.
	cacheKey := searchCacheKey("semantic", req.UserId, req.Query, limit)
	if cached, err := rdb.Get(ctx, cacheKey).Bytes(); err == nil {
		var resp pb.SearchJournalsResponse
		if err := json.Unmarshal(cached, &resp); err == nil {
			logger.Info("semantic search cache hit", "query", req.Query, "results", len(resp.Results))
			return &resp, nil
		}
	}

	logger.Info("semantic search cache miss, querying database", "query", req.Query)

	// Step 1: Encode the search query via the analyzer's embedding model.
	encodeReq := struct {
		Text string `json:"text"`
	}{Text: req.Query}

	body, err := json.Marshal(encodeReq)
	if err != nil {
		return nil, fmt.Errorf("marshal encode request: %w", err)
	}

	url := fmt.Sprintf("%s/v1/embeddings/encode", analyzerURL)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("create encode request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+analyzerAPIKey)

	resp, err := httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("encode request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("analyzer returned status %d for encode", resp.StatusCode)
	}

	var encodeResp struct {
		Embedding []float64 `json:"embedding"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&encodeResp); err != nil {
		return nil, fmt.Errorf("decode encode response: %w", err)
	}

	// Step 2: Run pgvector cosine similarity search directly via pgx.
	embeddingStr := formatVector(encodeResp.Embedding)

	rows, err := pgxPool.Query(ctx, `
		SELECT j.id, j.journal_text, j.mood_score, j.created_at,
		       1 - (je.embedding <=> $1::public.vector) AS similarity
		FROM source.journals j
		JOIN source.journal_embeddings je ON j.id = je.journal_id
		WHERE j.user_id = $2
		ORDER BY je.embedding <=> $1::public.vector ASC
		LIMIT $3
	`, embeddingStr, userID, limit)
	if err != nil {
		return nil, fmt.Errorf("semantic search query failed: %w", err)
	}
	defer rows.Close()

	var searchResults []searchRow
	for rows.Next() {
		var r searchRow
		if err := rows.Scan(&r.ID, &r.JournalText, &r.MoodScore, &r.CreatedAt, &r.Score); err != nil {
			return nil, fmt.Errorf("scan search row: %w", err)
		}
		searchResults = append(searchResults, r)
	}

	// Hydrate topic names for the returned journals.
	journalIDs := make([]int32, 0, len(searchResults))
	for _, r := range searchResults {
		journalIDs = append(journalIDs, r.ID)
	}
	topicsByJournal := hydrateTopics(ctx, dbq, journalIDs)

	// Build response.
	results := make([]*pb.JournalSearchResult, 0, len(searchResults))
	for _, r := range searchResults {
		entry := buildJournalEntry(req.UserId, r, topicsByJournal[r.ID])
		results = append(results, &pb.JournalSearchResult{
			Journal:         entry,
			SimilarityScore: float32(r.Score),
		})
	}

	out := &pb.SearchJournalsResponse{Results: results}

	// Cache the response in Redis (best-effort, don't fail the request).
	if encoded, err := json.Marshal(out); err == nil {
		_ = rdb.Set(ctx, cacheKey, encoded, searchCacheTTL).Err()
	}

	return out, nil
}

// KeywordSearchJournals performs full-text keyword search over a user's journal
// entries using PostgreSQL tsvector/tsquery.
func (s *JournalServer) KeywordSearchJournals(ctx context.Context, req *pb.KeywordSearchJournalsRequest) (*pb.KeywordSearchJournalsResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	pgxPool := inject.PgxPoolFrom(ctx)
	dbq := inject.DBFrom(ctx)
	logger := inject.LoggerFrom(ctx)

	limit := clampLimit(req.Limit, 20)

	query := req.Query
	if query == "" {
		return &pb.KeywordSearchJournalsResponse{Results: []*pb.KeywordSearchResult{}}, nil
	}

	rdb := inject.RedisClientFrom(ctx)

	// Check Redis cache first.
	cacheKey := searchCacheKey("keyword", req.UserId, query, limit)
	if cached, err := rdb.Get(ctx, cacheKey).Bytes(); err == nil {
		var resp pb.KeywordSearchJournalsResponse
		if err := json.Unmarshal(cached, &resp); err == nil {
			logger.Info("keyword search cache hit", "query", query, "results", len(resp.Results))
			return &resp, nil
		}
	}

	logger.Info("keyword search cache miss, querying database", "query", query)

	rows, err := pgxPool.Query(ctx, `
		SELECT j.id, j.journal_text, j.mood_score, j.created_at,
		       ts_rank(j.search_vector, plainto_tsquery('english', $1)) AS rank
		FROM source.journals j
		WHERE j.user_id = $2
		  AND j.search_vector @@ plainto_tsquery('english', $1)
		ORDER BY rank DESC
		LIMIT $3
	`, query, userID, limit)
	if err != nil {
		return nil, fmt.Errorf("keyword search query failed: %w", err)
	}
	defer rows.Close()

	var searchResults []searchRow
	for rows.Next() {
		var r searchRow
		if err := rows.Scan(&r.ID, &r.JournalText, &r.MoodScore, &r.CreatedAt, &r.Score); err != nil {
			return nil, fmt.Errorf("scan keyword search row: %w", err)
		}
		searchResults = append(searchResults, r)
	}

	// Hydrate topic names for the returned journals.
	journalIDs := make([]int32, 0, len(searchResults))
	for _, r := range searchResults {
		journalIDs = append(journalIDs, r.ID)
	}
	topicsByJournal := hydrateTopics(ctx, dbq, journalIDs)

	// Build response.
	results := make([]*pb.KeywordSearchResult, 0, len(searchResults))
	for _, r := range searchResults {
		entry := buildJournalEntry(req.UserId, r, topicsByJournal[r.ID])
		results = append(results, &pb.KeywordSearchResult{
			Journal: entry,
			Rank:    float32(r.Score),
		})
	}

	out := &pb.KeywordSearchJournalsResponse{Results: results}

	// Cache the response in Redis (best-effort, don't fail the request).
	if encoded, err := json.Marshal(out); err == nil {
		_ = rdb.Set(ctx, cacheKey, encoded, searchCacheTTL).Err()
	}

	return out, nil
}
