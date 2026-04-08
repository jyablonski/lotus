package community

import (
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestBuildProjectionEligibleWithNormalizedSignals(t *testing.T) {
	createdAt := time.Date(2026, 4, 7, 15, 0, 0, 0, time.UTC)
	score := int32(8)
	sentiment := "Positive"
	country := "us"
	region := "us-ca"
	topicModel := "topics_v1"

	projection := BuildProjection(db.GetCommunityProjectionSourceByJournalIdRow{
		JournalID:              42,
		UserID:                 pgtype.UUID{Valid: true},
		CreatedAt:              pgtype.Timestamp{Time: createdAt, Valid: true},
		MoodScore:              &score,
		Timezone:               "America/Los_Angeles",
		CommunityInsightsOptIn: true,
		CommunityLocationOptIn: true,
		CommunityCountryCode:   &country,
		CommunityRegionCode:    &region,
		PrimarySentiment:       sentiment,
		SentimentModelVersion:  "sentiment_v1",
		ThemeNames:             []string{" Work and Career ", "stress and overwhelm", "work and career"},
		TopicModelVersion:      &topicModel,
	})

	require.True(t, projection.EligibleForCommunity)
	assert.True(t, projection.HasEntryLocalDate)
	assert.Equal(t, time.Date(2026, 4, 7, 0, 0, 0, 0, time.UTC), projection.EntryLocalDate)
	assert.Equal(t, []string{"work", "stress"}, projection.ThemeNames)
	assert.Equal(t, "hopeful", deref(projection.PrimaryMood))
	assert.Equal(t, "positive", deref(projection.PrimarySentiment))
	assert.Equal(t, "US", deref(projection.CountryCode))
	assert.Equal(t, "US-CA", deref(projection.RegionCode))
	assert.Equal(t, "topics_v1", projection.AnalysisVersion)
}

func TestBuildProjectionIneligibleWithoutConsentOrThemes(t *testing.T) {
	createdAt := time.Date(2026, 4, 7, 15, 0, 0, 0, time.UTC)
	sentiment := "neutral"

	projection := BuildProjection(db.GetCommunityProjectionSourceByJournalIdRow{
		JournalID:              7,
		UserID:                 pgtype.UUID{Valid: true},
		CreatedAt:              pgtype.Timestamp{Time: createdAt, Valid: true},
		Timezone:               "UTC",
		CommunityInsightsOptIn: false,
		PrimarySentiment:       sentiment,
		ThemeNames:             nil,
	})

	assert.False(t, projection.EligibleForCommunity)
	assert.Nil(t, projection.CountryCode)
	assert.Nil(t, projection.RegionCode)
}

func TestBuildSummaryAndPromptSetDeterministic(t *testing.T) {
	summary := BuildSummary(TimeGrainWeek, []string{"work", "stress"}, []string{"steady"}, "joy")
	assert.Contains(t, summary, "steady")
	assert.Contains(t, summary, "work and stress")
	assert.Contains(t, summary, "Joy is also gaining momentum")

	prompts := BuildPromptSet(TimeGrainWeek, ScopeGlobal, []string{"work", "stress"}, []string{"steady"}, "joy")
	require.Len(t, prompts, 5)
	assert.Equal(t, "global_week_naming", prompts[0]["prompt_id"])
	assert.Equal(t, GenerationMethodTemplate, prompts[0]["generation_method"])
	assert.Equal(t, "week", prompts[0]["time_range_applied"])
	assert.Equal(t, "global", prompts[0]["scope_applied"])
}

func TestBuildRollupForGrainAppliesThresholdsAndRanks(t *testing.T) {
	current := make([]db.SourceJournalCommunityProjection, 0, 20)
	previous := make([]db.SourceJournalCommunityProjection, 0, 10)
	bucketDate := time.Date(2026, 4, 7, 0, 0, 0, 0, time.UTC)

	for i := 0; i < 20; i++ {
		userID := pgtype.UUID{Valid: true}
		userID.Bytes[15] = byte(i + 1)
		current = append(current, db.SourceJournalCommunityProjection{
			JournalID:            int32(i + 1),
			UserID:               userID,
			EligibleForCommunity: true,
			EntryLocalDate:       pgtype.Date{Time: bucketDate, Valid: true},
			PrimaryMood:          ptr("hopeful"),
			PrimarySentiment:     ptr("positive"),
			ThemeNames:           []string{"work", "stress"},
			RegionCode:           ptr("US-CA"),
		})
	}
	for i := 0; i < 10; i++ {
		userID := pgtype.UUID{Valid: true}
		userID.Bytes[15] = byte(50 + i)
		previous = append(previous, db.SourceJournalCommunityProjection{
			JournalID:            int32(100 + i),
			UserID:               userID,
			EligibleForCommunity: true,
			EntryLocalDate:       pgtype.Date{Time: bucketDate.AddDate(0, 0, -1), Valid: true},
			PrimaryMood:          ptr("steady"),
			PrimarySentiment:     ptr("positive"),
			ThemeNames:           []string{"work"},
			RegionCode:           ptr("US-CA"),
		})
	}

	refresh := BuildRollupForGrain(bucketDate, TimeGrainDay, current, previous)
	require.Len(t, refresh.Scopes, 2)
	assert.Equal(t, ScopeGlobal, refresh.Scopes[0].ScopeType)
	assert.Equal(t, "stress", refresh.Scopes[0].ThemeMetrics[0].Name)
	assert.Equal(t, 20, refresh.Scopes[0].ThemeMetrics[0].EntryCount)
	assert.Nil(t, refresh.Scopes[0].ThemeMetrics[0].DeltaVsPrevious)
	assert.Equal(t, "work", refresh.Scopes[0].ThemeMetrics[1].Name)
	assert.NotNil(t, refresh.Scopes[0].ThemeMetrics[1].DeltaVsPrevious)
	assert.Equal(t, ScopeRegion, refresh.Scopes[1].ScopeType)
	assert.Equal(t, "US-CA", refresh.Scopes[1].ScopeValue)
}

func ptr[T any](value T) *T {
	return &value
}

func deref[T any](value *T) T {
	var zero T
	if value == nil {
		return zero
	}
	return *value
}
