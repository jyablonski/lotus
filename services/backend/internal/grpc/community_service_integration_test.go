package grpc_test

import (
	"context"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/community"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCommunityServer_GetCommunityPulse_Integration(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.CommunityServer{}

	userID := createTestUser(t, queries)
	_, err := queries.UpdateCommunitySettingsByUserId(context.Background(), db.UpdateCommunitySettingsByUserIdParams{
		ID:                     pgtype.UUID{Bytes: userID, Valid: true},
		CommunityInsightsOptIn: true,
		CommunityLocationOptIn: true,
		CommunityCountryCode:   strp("US"),
		CommunityRegionCode:    strp("US-CA"),
	})
	require.NoError(t, err)

	now := time.Now().UTC()
	bucketDate := pgtype.Date{Time: time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC), Valid: true}

	_, err = queries.UpsertCommunityThemeRollup(context.Background(), db.UpsertCommunityThemeRollupParams{
		BucketDate:      bucketDate,
		TimeGrain:       "day",
		ScopeType:       "global",
		ScopeValue:      "global",
		ThemeName:       "rest",
		EntryCount:      12,
		UniqueUserCount: 11,
		Rank:            1,
		DeltaVsPrevious: communityNumeric("0.1000"),
	})
	require.NoError(t, err)

	_, err = queries.UpsertCommunityMoodRollup(context.Background(), db.UpsertCommunityMoodRollupParams{
		BucketDate:      bucketDate,
		TimeGrain:       "day",
		ScopeType:       "global",
		ScopeValue:      "global",
		MoodName:        "steady",
		EntryCount:      12,
		UniqueUserCount: 11,
		Rank:            1,
		DeltaVsPrevious: pgtype.Numeric{},
	})
	require.NoError(t, err)

	_, err = queries.UpsertCommunitySummary(context.Background(), db.UpsertCommunitySummaryParams{
		BucketDate:       bucketDate,
		TimeGrain:        "day",
		ScopeType:        "global",
		ScopeValue:       "global",
		SummaryText:      "People are slowing down together.",
		SourceThemeNames: []string{"rest"},
		SourceMoodNames:  []string{"steady"},
		GenerationMethod: "template",
	})
	require.NoError(t, err)

	resp, err := svc.GetCommunityPulse(ctx, &pb.GetCommunityPulseRequest{
		ViewerUserId: userID.String(),
		TimeRange:    "today",
		ScopeType:    "global",
	})

	require.NoError(t, err)
	assert.NotNil(t, resp)
	assert.Equal(t, "today", resp.AppliedTimeRange)
	assert.Len(t, resp.TopThemes, 1)
	assert.Equal(t, "rest", resp.TopThemes[0].Name)
	assert.Equal(t, "People are slowing down together.", resp.CommunitySummary)
}

func TestCommunityServer_GetCommunityPrompts_Integration(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.CommunityServer{}

	userID := createTestUser(t, queries)
	_, err := queries.UpdateCommunitySettingsByUserId(context.Background(), db.UpdateCommunitySettingsByUserIdParams{
		ID:                     pgtype.UUID{Bytes: userID, Valid: true},
		CommunityInsightsOptIn: true,
		CommunityLocationOptIn: false,
	})
	require.NoError(t, err)

	now := time.Now().UTC()
	bucketDate := pgtype.Date{Time: time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC), Valid: true}

	_, err = queries.UpsertCommunityThemeRollup(context.Background(), db.UpsertCommunityThemeRollupParams{
		BucketDate:      bucketDate,
		TimeGrain:       "day",
		ScopeType:       "global",
		ScopeValue:      "global",
		ThemeName:       "rest",
		EntryCount:      12,
		UniqueUserCount: 11,
		Rank:            1,
		DeltaVsPrevious: pgtype.Numeric{},
	})
	require.NoError(t, err)

	_, err = queries.UpsertCommunityMoodRollup(context.Background(), db.UpsertCommunityMoodRollupParams{
		BucketDate:      bucketDate,
		TimeGrain:       "day",
		ScopeType:       "global",
		ScopeValue:      "global",
		MoodName:        "steady",
		EntryCount:      12,
		UniqueUserCount: 11,
		Rank:            1,
		DeltaVsPrevious: pgtype.Numeric{},
	})
	require.NoError(t, err)

	_, err = queries.UpsertCommunityPromptSet(context.Background(), db.UpsertCommunityPromptSetParams{
		BucketDate:       bucketDate,
		TimeGrain:        "day",
		ScopeType:        "global",
		ScopeValue:       "global",
		PromptSetJson:    []byte(`[{"prompt_id":"global_day_naming","prompt_text":"What needs a little more room today?","inspiration_tags":["rest"],"tone":"gentle","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"naming"}]`),
		SourceThemeNames: []string{"rest"},
		SourceMoodNames:  []string{"steady"},
		GenerationMethod: "template",
	})
	require.NoError(t, err)

	resp, err := svc.GetCommunityPrompts(ctx, &pb.GetCommunityPromptsRequest{
		ViewerUserId:    userID.String(),
		ScopePreference: "global",
		Surface:         "journal_create",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.FeaturedPrompt)
	assert.Equal(t, "global_day_naming", resp.FeaturedPrompt.PromptId)
}

func communityNumeric(value string) pgtype.Numeric {
	var n pgtype.Numeric
	if err := n.Scan(value); err != nil {
		panic(err)
	}
	return n
}
