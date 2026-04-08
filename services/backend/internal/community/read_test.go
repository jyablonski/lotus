package community

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type stubReadQuerier struct {
	getSettings func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error)
	getThemes   func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error)
	getMoods    func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error)
	getSummary  func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error)
	getPrompt   func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error)
}

func (s stubReadQuerier) GetCommunitySettingsByUserId(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
	return s.getSettings(ctx, id)
}

func (s stubReadQuerier) GetThemeRollupsByBucketAndScope(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
	return s.getThemes(ctx, arg)
}

func (s stubReadQuerier) GetMoodRollupsByBucketAndScope(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
	return s.getMoods(ctx, arg)
}

func (s stubReadQuerier) GetCommunitySummaryByBucketAndScope(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
	return s.getSummary(ctx, arg)
}

func (s stubReadQuerier) GetCommunityPromptSetByBucketAndScope(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
	return s.getPrompt(ctx, arg)
}

func TestReadCommunityPulseFallsBackToGlobalWhenRegionDataMissing(t *testing.T) {
	viewerID := uuid.New()

	q := stubReadQuerier{
		getSettings: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			assert.Equal(t, viewerID, uuid.UUID(id.Bytes))
			return db.GetCommunitySettingsByUserIdRow{
				ID:                     id,
				CommunityLocationOptIn: true,
				CommunityRegionCode:    strPtr("US-CA"),
			}, nil
		},
		getThemes: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			if arg.ScopeType == ScopeRegion {
				return nil, nil
			}
			return []db.SourceCommunityThemeRollup{
				{ThemeName: "work", EntryCount: 25, UniqueUserCount: 18, Rank: 1, UpdatedAt: tsNow()},
			}, nil
		},
		getMoods: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			if arg.ScopeType == ScopeRegion {
				return nil, nil
			}
			return []db.SourceCommunityMoodRollup{
				{MoodName: "hopeful", EntryCount: 20, UniqueUserCount: 15, Rank: 1, UpdatedAt: tsNow()},
			}, nil
		},
		getSummary: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			if arg.ScopeType == ScopeRegion {
				return db.SourceCommunitySummary{}, pgx.ErrNoRows
			}
			return db.SourceCommunitySummary{SummaryText: "People are broadly feeling hopeful.", UpdatedAt: tsNow()}, nil
		},
		getPrompt: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{}, pgx.ErrNoRows
		},
	}

	selection, err := ReadCommunityPulse(context.Background(), q, viewerID.String(), "today", "region", "")
	require.NoError(t, err)
	assert.Equal(t, ScopeGlobal, selection.AppliedScopeType)
	assert.Equal(t, ScopeGlobal, selection.AppliedScopeValue)
	assert.True(t, selection.ScopeFallback)
	assert.Equal(t, PrivacyStateFallback, selection.PrivacyState)
	assert.Len(t, selection.ThemeMetrics, 1)
}

func TestReadTodayTogetherFallsBackToWeekWhenDailyDataMissing(t *testing.T) {
	viewerID := uuid.New()
	dayBucket := BucketForDate(time.Now().UTC(), TimeGrainDay)
	weekBucket := BucketForDate(time.Now().UTC(), TimeGrainWeek)

	q := stubReadQuerier{
		getSettings: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{ID: id}, nil
		},
		getThemes: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			if arg.BucketDate.Time.Equal(dayBucket) {
				return nil, nil
			}
			if arg.BucketDate.Time.Equal(weekBucket) {
				return []db.SourceCommunityThemeRollup{{ThemeName: "rest", EntryCount: 12, UniqueUserCount: 12, Rank: 1, UpdatedAt: tsNow()}}, nil
			}
			return nil, nil
		},
		getMoods: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			if arg.BucketDate.Time.Equal(weekBucket) {
				return []db.SourceCommunityMoodRollup{{MoodName: "steady", EntryCount: 12, UniqueUserCount: 12, Rank: 1, UpdatedAt: tsNow()}}, nil
			}
			return nil, nil
		},
		getSummary: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			if arg.BucketDate.Time.Equal(weekBucket) {
				return db.SourceCommunitySummary{SummaryText: "People are slowing down.", UpdatedAt: tsNow()}, nil
			}
			return db.SourceCommunitySummary{}, pgx.ErrNoRows
		},
		getPrompt: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{}, pgx.ErrNoRows
		},
	}

	selection, err := ReadTodayTogether(context.Background(), q, viewerID.String(), "global")
	require.NoError(t, err)
	assert.Equal(t, "this_week", selection.AppliedTimeRange)
	assert.True(t, selection.PeriodFallback)
	assert.Equal(t, PrivacyStateFallback, selection.PrivacyState)
	assert.Equal(t, "rest", selection.ThemeMetrics[0].ThemeName)
}

func TestReadCommunityPromptsReturnsInsufficientDataWithoutPromptSet(t *testing.T) {
	viewerID := uuid.New()
	q := stubReadQuerier{
		getSettings: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{ID: id}, nil
		},
		getThemes: func(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error) {
			return nil, nil
		},
		getMoods: func(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error) {
			return nil, nil
		},
		getSummary: func(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error) {
			return db.SourceCommunitySummary{}, pgx.ErrNoRows
		},
		getPrompt: func(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error) {
			return db.SourceCommunityPromptSet{}, pgx.ErrNoRows
		},
	}

	selection, err := ReadCommunityPrompts(context.Background(), q, viewerID.String(), "global")
	require.NoError(t, err)
	assert.Equal(t, PrivacyStateFallback, selection.PrivacyState)
	assert.Nil(t, selection.PromptSet)
}

func TestDecodePromptSet(t *testing.T) {
	data := []byte(`[{"prompt_id":"global_day_naming","prompt_text":"Test prompt","inspiration_tags":["rest"],"tone":"gentle","time_range_applied":"day","scope_applied":"global","generation_method":"template","category":"naming"}]`)

	prompts, err := DecodePromptSet(data)
	require.NoError(t, err)
	require.Len(t, prompts, 1)
	assert.Equal(t, "global_day_naming", prompts[0].PromptID)
}

func TestReadCommunityPulseErrorsOnUnsupportedTimeRange(t *testing.T) {
	q := stubReadQuerier{
		getSettings: func(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error) {
			return db.GetCommunitySettingsByUserIdRow{}, errors.New("should not be called")
		},
	}

	_, err := ReadCommunityPulse(context.Background(), q, "", "fortnight", "global", "")
	require.Error(t, err)
	assert.Contains(t, err.Error(), "unsupported time range")
}

func tsNow() pgtype.Timestamp {
	return pgtype.Timestamp{Time: time.Now().UTC(), Valid: true}
}

func strPtr(value string) *string {
	return &value
}
