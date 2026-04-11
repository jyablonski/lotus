package community

import (
	"context"
	"fmt"
	"slices"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
)

const (
	ScopeGlobal              = "global"
	ScopeRegion              = "region"
	TimeGrainDay             = "day"
	TimeGrainWeek            = "week"
	TimeGrainMonth           = "month"
	GlobalMinimumUniqueUsers = 10
	RegionMinimumUniqueUsers = 20
	GenerationMethodTemplate = "template"
	DefaultAnalysisVersion   = "v1"
)

var themeAliases = map[string]string{
	"work and career":              "work",
	"stress and overwhelm":         "stress",
	"joy and happiness":            "joy",
	"gratitude and appreciation":   "gratitude",
	"physical health and fitness":  "health",
	"reflection and introspection": "reflection",
}

type Projection struct {
	JournalID            int32
	UserID               pgtype.UUID
	EligibleForCommunity bool
	EntryLocalDate       time.Time
	HasEntryLocalDate    bool
	PrimaryMood          *string
	PrimarySentiment     *string
	ThemeNames           []string
	CountryCode          *string
	RegionCode           *string
	AnalysisVersion      string
}

type CountMetric struct {
	Name            string
	EntryCount      int
	UniqueUserCount int
	Rank            int
	DeltaVsPrevious *float64
}

type ScopeRollup struct {
	ScopeType       string
	ScopeValue      string
	ThemeMetrics    []CountMetric
	MoodMetrics     []CountMetric
	SourceThemes    []string
	SourceMoods     []string
	SummaryText     string
	PromptSet       []map[string]any
	UniqueUserCount int
}

type GrainRefresh struct {
	BucketDate time.Time
	TimeGrain  string
	Scopes     []ScopeRollup
}

func BuildProjection(source db.GetCommunityProjectionSourceByJournalIdRow) Projection {
	entryLocalDate, validDate := localEntryDate(source.CreatedAt.Time, source.Timezone)
	primarySentiment := normalizeSentimentValue(source.PrimarySentiment)
	themeNames := normalizeThemeValue(source.ThemeNames)
	primaryMood := derivePrimaryMood(source.MoodScore, primarySentiment)

	var countryCode *string
	var regionCode *string
	if source.CommunityLocationOptIn {
		countryCode = normalizeCodePtr(source.CommunityCountryCode)
		regionCode = normalizeCodePtr(source.CommunityRegionCode)
	}

	eligible := source.CommunityInsightsOptIn &&
		validDate &&
		primarySentiment != nil &&
		len(themeNames) > 0

	analysisVersion := buildAnalysisVersion(
		normalizeStringValue(source.TopicModelVersion),
		normalizeSentimentModelVersion(source.SentimentModelVersion),
	)

	return Projection{
		JournalID:            source.JournalID,
		UserID:               source.UserID,
		EligibleForCommunity: eligible,
		EntryLocalDate:       entryLocalDate,
		HasEntryLocalDate:    validDate,
		PrimaryMood:          primaryMood,
		PrimarySentiment:     primarySentiment,
		ThemeNames:           themeNames,
		CountryCode:          countryCode,
		RegionCode:           regionCode,
		AnalysisVersion:      analysisVersion,
	}
}

func BuildRollupForGrain(bucketDate time.Time, grain string, current, previous []db.SourceJournalCommunityProjection) GrainRefresh {
	return GrainRefresh{
		BucketDate: bucketDate,
		TimeGrain:  grain,
		Scopes:     buildScopeRollups(current, previous, grain),
	}
}

func buildScopeRollups(current, previous []db.SourceJournalCommunityProjection, timeGrain string) []ScopeRollup {
	var scopes []ScopeRollup

	if rollup := buildScopeRollup(ScopeGlobal, ScopeGlobal, current, previous, GlobalMinimumUniqueUsers, timeGrain); rollup != nil {
		scopes = append(scopes, *rollup)
	}

	currentByRegion := groupByRegion(current)
	previousByRegion := groupByRegion(previous)
	regionKeys := make([]string, 0, len(currentByRegion))
	for key := range currentByRegion {
		regionKeys = append(regionKeys, key)
	}
	slices.Sort(regionKeys)
	for _, region := range regionKeys {
		if rollup := buildScopeRollup(ScopeRegion, region, currentByRegion[region], previousByRegion[region], RegionMinimumUniqueUsers, timeGrain); rollup != nil {
			scopes = append(scopes, *rollup)
		}
	}

	return scopes
}

func buildScopeRollup(scopeType, scopeValue string, current, previous []db.SourceJournalCommunityProjection, minUsers int, timeGrain string) *ScopeRollup {
	currentThemeCounts, currentThemeUsers, currentMoodCounts, currentMoodUsers, uniqueUsers := aggregate(current)
	if len(uniqueUsers) < minUsers {
		return nil
	}

	prevThemeCounts, _, prevMoodCounts, _, _ := aggregate(previous)

	themeMetrics := rankMetrics(currentThemeCounts, currentThemeUsers, prevThemeCounts)
	moodMetrics := rankMetrics(currentMoodCounts, currentMoodUsers, prevMoodCounts)
	if len(themeMetrics) == 0 || len(moodMetrics) == 0 {
		return nil
	}

	sourceThemes := topMetricNames(themeMetrics, 3)
	sourceMoods := topMetricNames(moodMetrics, 2)
	summary := BuildSummary(timeGrain, sourceThemes, sourceMoods, risingMetricName(themeMetrics))
	prompts := BuildPromptSet(timeGrain, scopeType, sourceThemes, sourceMoods, risingMetricName(themeMetrics))

	return &ScopeRollup{
		ScopeType:       scopeType,
		ScopeValue:      scopeValue,
		ThemeMetrics:    themeMetrics,
		MoodMetrics:     moodMetrics,
		SourceThemes:    sourceThemes,
		SourceMoods:     sourceMoods,
		SummaryText:     summary,
		PromptSet:       prompts,
		UniqueUserCount: len(uniqueUsers),
	}
}

func BuildSummary(timeGrain string, themes, moods []string, risingTheme string) string {
	if len(themes) == 0 || len(moods) == 0 {
		return ""
	}

	var summary string
	switch len(themes) {
	case 1:
		summary = fmt.Sprintf(
			"People are broadly feeling %s lately, with %s showing up most often in recent reflections.",
			moods[0], themes[0],
		)
	default:
		summary = fmt.Sprintf(
			"People are broadly feeling %s lately, with %s and %s appearing most often in recent reflections.",
			moods[0], themes[0], themes[1],
		)
	}

	if risingTheme != "" && risingTheme != themes[0] {
		summary += fmt.Sprintf(" %s is also gaining momentum compared with the previous %s.", titleize(risingTheme), timeGrain)
	}

	return summary
}

func BuildPromptSet(timeGrain, scopeType string, themes, moods []string, risingTheme string) []map[string]any {
	if len(themes) == 0 || len(moods) == 0 {
		return nil
	}

	topTheme := themes[0]
	secondaryTheme := topTheme
	if len(themes) > 1 {
		secondaryTheme = themes[1]
	}
	mood := moods[0]

	prompts := []map[string]any{
		prompt("naming", timeGrain, scopeType, []string{topTheme, mood}, "gentle", fmt.Sprintf("What feels most present for you about %s right now, and how would you name it in your own words?", topTheme)),
		prompt("processing", timeGrain, scopeType, []string{topTheme, secondaryTheme}, "reflective", fmt.Sprintf("When %s and %s show up together, what story do you notice yourself telling about this season of life?", topTheme, secondaryTheme)),
		prompt("grounding", timeGrain, scopeType, []string{mood, topTheme}, "steady", fmt.Sprintf("If the broader mood feels %s, what helps you stay grounded while %s is in the background?", mood, topTheme)),
		prompt("future_facing", timeGrain, scopeType, []string{topTheme, mood}, "hopeful", fmt.Sprintf("What is one small next step that feels possible while %s is still part of the picture?", topTheme)),
		prompt("gratitude_or_repair", timeGrain, scopeType, []string{secondaryTheme, mood}, "warm", fmt.Sprintf("Where could a little care, gratitude, or repair help you respond to %s this week?", secondaryTheme)),
	}

	if risingTheme != "" && risingTheme != topTheme {
		prompts[3] = prompt("future_facing", timeGrain, scopeType, []string{risingTheme, mood}, "hopeful", fmt.Sprintf("As %s seems to be gaining momentum, what would help you meet it with intention?", risingTheme))
	}

	return prompts
}

func prompt(category, timeGrain, scopeType string, tags []string, tone, text string) map[string]any {
	return map[string]any{
		"prompt_id":          fmt.Sprintf("%s_%s_%s", scopeType, timeGrain, category),
		"prompt_text":        text,
		"inspiration_tags":   tags,
		"tone":               tone,
		"time_range_applied": timeGrain,
		"scope_applied":      scopeType,
		"generation_method":  GenerationMethodTemplate,
		"category":           category,
	}
}

func localEntryDate(createdAt time.Time, timezone string) (time.Time, bool) {
	loc, err := time.LoadLocation(timezone)
	if err != nil {
		loc = time.UTC
	}
	local := createdAt.In(loc)
	if local.IsZero() {
		return time.Time{}, false
	}
	return time.Date(local.Year(), local.Month(), local.Day(), 0, 0, 0, 0, time.UTC), true
}

func bucketForDate(date time.Time, grain string) time.Time {
	date = date.UTC()
	switch grain {
	case TimeGrainWeek:
		weekday := int(date.Weekday())
		if weekday == 0 {
			weekday = 7
		}
		return time.Date(date.Year(), date.Month(), date.Day()-(weekday-1), 0, 0, 0, 0, time.UTC)
	case TimeGrainMonth:
		return time.Date(date.Year(), date.Month(), 1, 0, 0, 0, 0, time.UTC)
	default:
		return time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.UTC)
	}
}

func WindowForBucket(bucketDate time.Time, grain string) (time.Time, time.Time) {
	switch grain {
	case TimeGrainWeek:
		return bucketDate, bucketDate.AddDate(0, 0, 6)
	case TimeGrainMonth:
		return bucketDate, bucketDate.AddDate(0, 1, -1)
	default:
		return bucketDate, bucketDate
	}
}

func PreviousWindowForBucket(bucketDate time.Time, grain string) (time.Time, time.Time) {
	switch grain {
	case TimeGrainWeek:
		start := bucketDate.AddDate(0, 0, -7)
		return start, start.AddDate(0, 0, 6)
	case TimeGrainMonth:
		start := bucketDate.AddDate(0, -1, 0)
		return start, bucketDate.AddDate(0, 0, -1)
	default:
		prev := bucketDate.AddDate(0, 0, -1)
		return prev, prev
	}
}

func BucketForDate(date time.Time, grain string) time.Time {
	return bucketForDate(date, grain)
}

func normalizeThemes(raw []string) []string {
	if len(raw) == 0 {
		return []string{}
	}

	seen := map[string]struct{}{}
	result := make([]string, 0, len(raw))
	for _, theme := range raw {
		normalized := normalizeTheme(theme)
		if normalized == "" {
			continue
		}
		if _, exists := seen[normalized]; exists {
			continue
		}
		seen[normalized] = struct{}{}
		result = append(result, normalized)
	}
	if len(result) == 0 {
		return []string{}
	}
	return result
}

func normalizeTheme(raw string) string {
	normalized := strings.ToLower(strings.TrimSpace(raw))
	normalized = strings.ReplaceAll(normalized, "_", " ")
	normalized = strings.Join(strings.Fields(normalized), " ")
	if alias, ok := themeAliases[normalized]; ok {
		return alias
	}
	return normalized
}

func normalizeSentimentPtr(raw *string) *string {
	if raw == nil {
		return nil
	}
	normalized := strings.ToLower(strings.TrimSpace(*raw))
	switch normalized {
	case "positive", "negative", "neutral", "uncertain":
		return &normalized
	default:
		return nil
	}
}

func normalizeSentimentValue(raw interface{}) *string {
	switch v := raw.(type) {
	case string:
		if strings.TrimSpace(v) == "" {
			return nil
		}
		return normalizeSentimentPtr(&v)
	case *string:
		if v == nil || strings.TrimSpace(*v) == "" {
			return nil
		}
		return normalizeSentimentPtr(v)
	default:
		return nil
	}
}

func normalizeSentimentModelVersion(raw interface{}) *string {
	return normalizeStringValue(raw)
}

func normalizeThemeValue(raw interface{}) []string {
	switch v := raw.(type) {
	case []string:
		return normalizeThemes(v)
	case []interface{}:
		values := make([]string, 0, len(v))
		for _, item := range v {
			if text, ok := item.(string); ok {
				values = append(values, text)
			}
		}
		return normalizeThemes(values)
	default:
		return []string{}
	}
}

func derivePrimaryMood(moodScore *int32, sentiment *string) *string {
	if moodScore != nil {
		var mood string
		switch {
		case *moodScore <= 2:
			mood = "overwhelmed"
		case *moodScore <= 4:
			mood = "low"
		case *moodScore <= 6:
			mood = "steady"
		case *moodScore <= 8:
			mood = "hopeful"
		default:
			mood = "uplifted"
		}
		return &mood
	}

	if sentiment == nil {
		return nil
	}

	var mood string
	switch *sentiment {
	case "positive":
		mood = "hopeful"
	case "negative":
		mood = "heavy"
	case "neutral":
		mood = "steady"
	case "uncertain":
		mood = "mixed"
	default:
		return nil
	}
	return &mood
}

func normalizeCodePtr(raw *string) *string {
	if raw == nil {
		return nil
	}
	normalized := strings.ToUpper(strings.TrimSpace(*raw))
	if normalized == "" {
		return nil
	}
	return &normalized
}

func buildAnalysisVersion(topicModel, sentimentModel *string) string {
	switch {
	case topicModel != nil && strings.TrimSpace(*topicModel) != "":
		return strings.TrimSpace(*topicModel)
	case sentimentModel != nil && strings.TrimSpace(*sentimentModel) != "":
		return strings.TrimSpace(*sentimentModel)
	default:
		return DefaultAnalysisVersion
	}
}

func normalizeStringValue(raw interface{}) *string {
	switch v := raw.(type) {
	case string:
		if strings.TrimSpace(v) == "" {
			return nil
		}
		return &v
	case *string:
		if v == nil || strings.TrimSpace(*v) == "" {
			return nil
		}
		return v
	default:
		return nil
	}
}

func groupByRegion(items []db.SourceJournalCommunityProjection) map[string][]db.SourceJournalCommunityProjection {
	result := make(map[string][]db.SourceJournalCommunityProjection)
	for _, item := range items {
		if item.RegionCode == nil || strings.TrimSpace(*item.RegionCode) == "" {
			continue
		}
		result[*item.RegionCode] = append(result[*item.RegionCode], item)
	}
	return result
}

func aggregate(items []db.SourceJournalCommunityProjection) (map[string]int, map[string]map[[16]byte]struct{}, map[string]int, map[string]map[[16]byte]struct{}, map[[16]byte]struct{}) {
	themeCounts := map[string]int{}
	themeUsers := map[string]map[[16]byte]struct{}{}
	moodCounts := map[string]int{}
	moodUsers := map[string]map[[16]byte]struct{}{}
	uniqueUsers := map[[16]byte]struct{}{}

	for _, item := range items {
		userKey := item.UserID.Bytes
		uniqueUsers[userKey] = struct{}{}

		for _, theme := range item.ThemeNames {
			themeCounts[theme]++
			if themeUsers[theme] == nil {
				themeUsers[theme] = map[[16]byte]struct{}{}
			}
			themeUsers[theme][userKey] = struct{}{}
		}

		if item.PrimaryMood != nil && strings.TrimSpace(*item.PrimaryMood) != "" {
			mood := *item.PrimaryMood
			moodCounts[mood]++
			if moodUsers[mood] == nil {
				moodUsers[mood] = map[[16]byte]struct{}{}
			}
			moodUsers[mood][userKey] = struct{}{}
		}
	}

	return themeCounts, themeUsers, moodCounts, moodUsers, uniqueUsers
}

func rankMetrics(counts map[string]int, uniqueUsers map[string]map[[16]byte]struct{}, previous map[string]int) []CountMetric {
	metrics := make([]CountMetric, 0, len(counts))
	for name, entryCount := range counts {
		metric := CountMetric{
			Name:            name,
			EntryCount:      entryCount,
			UniqueUserCount: len(uniqueUsers[name]),
		}
		if prevCount, ok := previous[name]; ok && prevCount > 0 {
			delta := float64(entryCount-prevCount) / float64(prevCount)
			metric.DeltaVsPrevious = &delta
		}
		metrics = append(metrics, metric)
	}

	slices.SortFunc(metrics, func(a, b CountMetric) int {
		switch {
		case a.EntryCount != b.EntryCount:
			return b.EntryCount - a.EntryCount
		case a.UniqueUserCount != b.UniqueUserCount:
			return b.UniqueUserCount - a.UniqueUserCount
		default:
			return strings.Compare(a.Name, b.Name)
		}
	})

	if len(metrics) > 10 {
		metrics = metrics[:10]
	}
	for idx := range metrics {
		metrics[idx].Rank = idx + 1
	}
	return metrics
}

func topMetricNames(metrics []CountMetric, limit int) []string {
	if len(metrics) == 0 {
		return nil
	}
	if len(metrics) < limit {
		limit = len(metrics)
	}
	names := make([]string, 0, limit)
	for i := 0; i < limit; i++ {
		names = append(names, metrics[i].Name)
	}
	return names
}

func risingMetricName(metrics []CountMetric) string {
	bestName := ""
	bestDelta := 0.0
	for _, metric := range metrics {
		if metric.DeltaVsPrevious == nil {
			continue
		}
		if bestName == "" || *metric.DeltaVsPrevious > bestDelta {
			bestName = metric.Name
			bestDelta = *metric.DeltaVsPrevious
		}
	}
	return bestName
}

func titleize(value string) string {
	if value == "" {
		return value
	}
	parts := strings.Fields(value)
	for i := range parts {
		if parts[i] == "" {
			continue
		}
		parts[i] = strings.ToUpper(parts[i][:1]) + parts[i][1:]
	}
	return strings.Join(parts, " ")
}

func PgDate(t time.Time) pgtype.Date {
	return pgtype.Date{Time: t, Valid: true}
}

func NullablePgDate(t time.Time, valid bool) pgtype.Date {
	if !valid {
		return pgtype.Date{}
	}
	return PgDate(t)
}

func LoadProjectionsForWindow(ctx context.Context, queries *db.Queries, start, end time.Time) ([]db.SourceJournalCommunityProjection, error) {
	return queries.ListEligibleCommunityProjectionsByDateRange(ctx, db.ListEligibleCommunityProjectionsByDateRangeParams{
		EntryLocalDate:   PgDate(start),
		EntryLocalDate_2: PgDate(end),
	})
}
