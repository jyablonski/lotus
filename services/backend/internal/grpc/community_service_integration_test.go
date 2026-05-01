package grpc_test

import (
	"context"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/community"
	"github.com/jyablonski/lotus/internal/testfixtures"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCommunityServer_GetCommunityPulse_Integration(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.CommunityServer{}

	userID := createTestCommunityUser(t, queries, strp("US"), strp("US-CA"))

	now := time.Now().UTC()
	bucketDate := pgtype.Date{Time: time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC), Valid: true}

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunityThemeRollup{
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

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunityMoodRollup{
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

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunitySummary{
		BucketDate:       bucketDate,
		TimeGrain:        "day",
		ScopeType:        "global",
		ScopeValue:       "global",
		SummaryText:      "People are slowing down together.",
		SourceThemeNames: []string{"rest"},
		SourceMoodNames:  []string{"steady"},
		GenerationMethod: "template",
	})

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

	userID := createTestCommunityUser(t, queries, nil, nil)

	now := time.Now().UTC()
	bucketDate := pgtype.Date{Time: time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC), Valid: true}

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunityThemeRollup{
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

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunityMoodRollup{
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

	testfixtures.CreateWithDefaults(t, context.Background(), queries, db.SourceCommunityPromptSet{
		BucketDate:       bucketDate,
		TimeGrain:        "day",
		ScopeType:        "global",
		ScopeValue:       "global",
		PromptSetJson:    []byte(`[{"prompt_id":"global_day_naming","prompt_text":"What needs a little more room today?","inspiration_tags":["rest"],"tone":"gentle","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"naming"}]`),
		SourceThemeNames: []string{"rest"},
		SourceMoodNames:  []string{"steady"},
		GenerationMethod: "template",
	})

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
