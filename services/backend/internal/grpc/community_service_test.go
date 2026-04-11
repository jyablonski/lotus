package grpc_test

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/community"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newCommunityTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func communityTestCtx(mock db.Querier) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, mock)
	ctx = inject.WithLogger(ctx, newCommunityTestLogger())
	return ctx
}

func TestCommunityServer_GetCommunityPulse_InvalidViewerID(t *testing.T) {
	server := &internalgrpc.CommunityServer{}

	resp, err := server.GetCommunityPulse(context.Background(), &pb.GetCommunityPulseRequest{
		ViewerUserId: "not-a-uuid",
		TimeRange:    "today",
		ScopeType:    "global",
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestCommunityServer_GetCommunityPulse_RegionFallbackSuccess(t *testing.T) {
	viewerID := uuid.New()
	now := time.Now().UTC()
	mockQuerier := &mocks.QuerierMock{
		GetCommunitySettingsByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{
				ID:                     id,
				CommunityLocationOptIn: true,
				CommunityRegionCode:    strp("US-CA"),
			}, nil
		},
		GetThemeRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			if arg.ScopeType == "region" {
				return nil, nil
			}
			return []db.SourceCommunityThemeRollup{
				{ThemeName: "work", EntryCount: 15, UniqueUserCount: 12, Rank: 1, UpdatedAt: pgtype.Timestamp{Time: now, Valid: true}},
			}, nil
		},
		GetMoodRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			if arg.ScopeType == "region" {
				return nil, nil
			}
			return []db.SourceCommunityMoodRollup{
				{MoodName: "hopeful", EntryCount: 12, UniqueUserCount: 10, Rank: 1, UpdatedAt: pgtype.Timestamp{Time: now, Valid: true}},
			}, nil
		},
		GetCommunitySummaryByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			if arg.ScopeType == "region" {
				return db.SourceCommunitySummary{}, pgx.ErrNoRows
			}
			return db.SourceCommunitySummary{
				SummaryText: "People are broadly feeling hopeful.",
				UpdatedAt:   pgtype.Timestamp{Time: now, Valid: true},
			}, nil
		},
		GetCommunityPromptSetByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{}, pgx.ErrNoRows
		},
	}

	server := &internalgrpc.CommunityServer{}
	resp, err := server.GetCommunityPulse(communityTestCtx(mockQuerier), &pb.GetCommunityPulseRequest{
		ViewerUserId: viewerID.String(),
		TimeRange:    "today",
		ScopeType:    "region",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, "global", resp.AppliedScopeType)
	assert.True(t, resp.Privacy.ScopeFallbackApplied)
	assert.Len(t, resp.TopThemes, 1)
	assert.Equal(t, "work", resp.TopThemes[0].Name)
}

func TestCommunityServer_GetCommunityPrompts_Success(t *testing.T) {
	viewerID := uuid.New()
	now := time.Now().UTC()
	mockQuerier := &mocks.QuerierMock{
		GetCommunitySettingsByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{ID: id}, nil
		},
		GetThemeRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			return []db.SourceCommunityThemeRollup{
				{ThemeName: "rest", EntryCount: 11, UniqueUserCount: 11, Rank: 1, UpdatedAt: pgtype.Timestamp{Time: now, Valid: true}},
			}, nil
		},
		GetMoodRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			return []db.SourceCommunityMoodRollup{
				{MoodName: "steady", EntryCount: 11, UniqueUserCount: 11, Rank: 1, UpdatedAt: pgtype.Timestamp{Time: now, Valid: true}},
			}, nil
		},
		GetCommunitySummaryByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			return db.SourceCommunitySummary{SummaryText: "People are slowing down.", UpdatedAt: pgtype.Timestamp{Time: now, Valid: true}}, nil
		},
		GetCommunityPromptSetByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{
				PromptSetJson: []byte(`[
					{"prompt_id":"global_day_naming","prompt_text":"What needs a little more room in your mind today?","inspiration_tags":["rest"],"tone":"gentle","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"naming"},
					{"prompt_id":"global_day_processing","prompt_text":"What feels unfinished right now?","inspiration_tags":["rest"],"tone":"reflective","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"processing"}
				]`),
				UpdatedAt: pgtype.Timestamp{Time: now, Valid: true},
			}, nil
		},
	}

	server := &internalgrpc.CommunityServer{}
	resp, err := server.GetCommunityPrompts(communityTestCtx(mockQuerier), &pb.GetCommunityPromptsRequest{
		ViewerUserId:    viewerID.String(),
		ScopePreference: "global",
		Surface:         "dashboard",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	require.NotNil(t, resp.FeaturedPrompt)
	assert.Equal(t, "global_day_naming", resp.FeaturedPrompt.PromptId)
	assert.Len(t, resp.AlternatePrompts, 1)
}
