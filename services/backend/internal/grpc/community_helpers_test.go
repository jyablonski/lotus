package grpc

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/community"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/community"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func TestCommunityHelpers(t *testing.T) {
	var validDelta pgtype.Numeric
	require.NoError(t, validDelta.Scan("0.125"))

	themeMetrics := []db.SourceCommunityThemeRollup{
		{
			ThemeName:       "rest",
			EntryCount:      10,
			UniqueUserCount: 9,
			Rank:            1,
			DeltaVsPrevious: validDelta,
		},
		{
			ThemeName:       "change",
			EntryCount:      8,
			UniqueUserCount: 8,
			Rank:            2,
		},
	}

	moodMetricsInput := []db.SourceCommunityMoodRollup{
		{
			MoodName:        "hopeful",
			EntryCount:      7,
			UniqueUserCount: 7,
			Rank:            1,
			DeltaVsPrevious: validDelta,
		},
	}

	pulse := pulseMetrics(themeMetrics)
	require.Len(t, pulse, 2)
	require.NotNil(t, pulse[0].DeltaVsPrevious)
	assert.Equal(t, 0.125, *pulse[0].DeltaVsPrevious)

	limited := limitedPulseMetrics(themeMetrics, 1)
	require.Len(t, limited, 1)
	assert.Equal(t, "rest", limited[0].Name)

	moods := moodMetrics(moodMetricsInput)
	require.Len(t, moods, 1)
	require.NotNil(t, moods[0].DeltaVsPrevious)

	assert.Equal(t, "hopeful", dominantMood(moodMetricsInput))
	assert.Equal(t, "", dominantMood(nil))

	assert.Equal(t, "", communitySummary(community.ReadSelection{}))
	assert.Equal(t, "A steady day.", communitySummary(community.ReadSelection{
		Summary: &db.SourceCommunitySummary{SummaryText: "A steady day."},
	}))

	decoded, err := decodePrompts(community.ReadSelection{})
	require.NoError(t, err)
	assert.Nil(t, decoded)

	decoded, err = decodePrompts(community.ReadSelection{
		PromptSet: &db.SourceCommunityPromptSet{
			PromptSetJson: []byte(`[{"prompt_id":"p1","prompt_text":"Prompt","inspiration_tags":["rest"],"tone":"gentle","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"naming"}]`),
		},
	})
	require.NoError(t, err)
	require.Len(t, decoded, 1)

	_, err = decodePrompts(community.ReadSelection{
		PromptSet: &db.SourceCommunityPromptSet{PromptSetJson: []byte(`{not-json}`)},
	})
	require.Error(t, err)

	featured, alternates := splitPrompts([]community.PromptPayload{
		{PromptID: "p1", PromptText: "First"},
		{PromptID: "p2", PromptText: "Second"},
		{PromptID: "p3", PromptText: "Third"},
		{PromptID: "p4", PromptText: "Fourth"},
	}, "dashboard")
	require.NotNil(t, featured)
	assert.Equal(t, "p1", featured.PromptId)
	require.Len(t, alternates, 2)

	featured, alternates = splitPrompts([]community.PromptPayload{
		{PromptID: "p1", PromptText: "First"},
	}, "")
	require.NotNil(t, featured)
	assert.Empty(t, alternates)

	featured, alternates = splitPrompts(nil, "community_page")
	assert.Nil(t, featured)
	assert.Nil(t, alternates)

	assert.Equal(t, community.TimeGrainDay, communityTimeRangeToGrain("today"))
	assert.Equal(t, community.TimeGrainWeek, communityTimeRangeToGrain("this_week"))
	assert.Equal(t, community.TimeGrainMonth, communityTimeRangeToGrain("this_month"))

	assert.Equal(t, 0.125, communityNumericToFloat(validDelta))
	assert.Equal(t, 0.0, communityNumericToFloat(pgtype.Numeric{}))

	assert.Equal(t, "[0.5,1.25,-3]", formatVector([]float64{0.5, 1.25, -3}))

	semantic := searchRowFromSemantic(db.SearchJournalsSemanticRow{
		ID:          44,
		JournalText: "semantic",
		MoodScore:   func() *int32 { v := int32(6); return &v }(),
		Similarity:  0.88,
		CreatedAt:   pgtype.Timestamp{Time: time.Date(2026, 4, 7, 9, 0, 0, 0, time.UTC), Valid: true},
	})
	assert.Equal(t, int32(44), semantic.ID)
	assert.Equal(t, "semantic", semantic.JournalText)
	assert.Equal(t, 0.88, semantic.Score)
	assert.False(t, semantic.CreatedAt.IsZero())

	assert.Nil(t, normalizeOptionalString(""))
	value := normalizeOptionalString("US")
	require.NotNil(t, value)
	assert.Equal(t, "US", *value)
}

func TestCommunityServerGetTodayTogetherSuccess(t *testing.T) {
	viewerID := uuid.New()
	mockQuerier := &mocks.QuerierMock{
		GetCommunitySettingsByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			region := "US-CA"
			return db.GetCommunitySettingsByUserIdRow{
				CommunityLocationOptIn: true,
				CommunityRegionCode:    &region,
			}, nil
		},
		GetThemeRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			return []db.SourceCommunityThemeRollup{
				{ThemeName: "rest", EntryCount: 12, UniqueUserCount: 11, Rank: 1},
				{ThemeName: "change", EntryCount: 10, UniqueUserCount: 10, Rank: 2},
				{ThemeName: "connection", EntryCount: 8, UniqueUserCount: 8, Rank: 3},
				{ThemeName: "work", EntryCount: 7, UniqueUserCount: 7, Rank: 4},
			}, nil
		},
		GetMoodRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			return []db.SourceCommunityMoodRollup{
				{MoodName: "hopeful", EntryCount: 12, UniqueUserCount: 11, Rank: 1},
			}, nil
		},
		GetCommunitySummaryByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			return db.SourceCommunitySummary{SummaryText: "People are making room to breathe."}, nil
		},
		GetCommunityPromptSetByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{}, pgx.ErrNoRows
		},
	}

	ctx := inject.WithDB(context.Background(), mockQuerier)
	server := &CommunityServer{}

	resp, err := server.GetTodayTogether(ctx, &pb.GetTodayTogetherRequest{
		ViewerUserId:    viewerID.String(),
		ScopePreference: "nearby",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, "today", resp.PeriodApplied)
	assert.Len(t, resp.Themes, 3)
	assert.Equal(t, "hopeful", resp.DominantMood)
	assert.Equal(t, "People are making room to breathe.", resp.CommunityNote)
}

func TestCommunityServerGetTodayTogetherInvalidViewerID(t *testing.T) {
	server := &CommunityServer{}

	resp, err := server.GetTodayTogether(context.Background(), &pb.GetTodayTogetherRequest{
		ViewerUserId: "not-a-uuid",
	})

	require.Error(t, err)
	assert.Nil(t, resp)
}

func TestCommunityServerGetCommunityPromptsDecodeError(t *testing.T) {
	viewerID := uuid.New()
	mockQuerier := &mocks.QuerierMock{
		GetCommunitySettingsByUserIdFunc: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{}, nil
		},
		GetThemeRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			return []db.SourceCommunityThemeRollup{
				{ThemeName: "rest", EntryCount: 12, UniqueUserCount: 11, Rank: 1},
			}, nil
		},
		GetMoodRollupsByBucketAndScopeFunc: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			return []db.SourceCommunityMoodRollup{
				{MoodName: "hopeful", EntryCount: 12, UniqueUserCount: 11, Rank: 1},
			}, nil
		},
		GetCommunitySummaryByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			return db.SourceCommunitySummary{}, pgx.ErrNoRows
		},
		GetCommunityPromptSetByBucketAndScopeFunc: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{
				PromptSetJson: []byte(`{bad-json}`),
			}, nil
		},
	}

	ctx := inject.WithDB(context.Background(), mockQuerier)
	server := &CommunityServer{}

	resp, err := server.GetCommunityPrompts(ctx, &pb.GetCommunityPromptsRequest{
		ViewerUserId:    viewerID.String(),
		ScopePreference: "global",
	})

	require.Error(t, err)
	assert.Nil(t, resp)
}

func TestLoggingInterceptorAndRegistration(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	interceptor := LoggingInterceptor(logger)

	resp, err := interceptor(context.Background(), "req", &grpc.UnaryServerInfo{
		FullMethod: "/community.CommunityService/GetCommunityPulse",
	}, func(ctx context.Context, req any) (any, error) {
		return "ok", nil
	})
	require.NoError(t, err)
	assert.Equal(t, "ok", resp)

	_, err = interceptor(context.Background(), "req", &grpc.UnaryServerInfo{
		FullMethod: "/community.CommunityService/GetCommunityPulse",
	}, func(ctx context.Context, req any) (any, error) {
		return nil, errors.New("boom")
	})
	require.Error(t, err)

	server := grpc.NewServer()
	RegisterServices(server)
	serviceInfo := server.GetServiceInfo()
	assert.Contains(t, serviceInfo, "user.UserService")
	assert.Contains(t, serviceInfo, "community.CommunityService")
	assert.Contains(t, serviceInfo, "journal.JournalService")
}

func TestRegisterGatewayRegistration(t *testing.T) {
	err := RegisterGateway(context.Background(), runtime.NewServeMux(), "127.0.0.1:1", []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	})
	require.NoError(t, err)
}
