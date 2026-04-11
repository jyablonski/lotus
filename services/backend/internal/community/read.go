package community

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
)

const (
	PrivacyStateReady            = "ready"
	PrivacyStateFallback         = "fallback"
	PrivacyStateInsufficientData = "insufficient_data"
)

type ReadSelection struct {
	RequestedTimeRange  string
	AppliedTimeRange    string
	RequestedScopeType  string
	RequestedScopeValue string
	AppliedScopeType    string
	AppliedScopeValue   string
	ThemeMetrics        []db.SourceCommunityThemeRollup
	MoodMetrics         []db.SourceCommunityMoodRollup
	Summary             *db.SourceCommunitySummary
	PromptSet           *db.SourceCommunityPromptSet
	GeneratedAt         time.Time
	ScopeFallback       bool
	PeriodFallback      bool
	PrivacyState        string
}

type PromptPayload struct {
	PromptID         string   `json:"prompt_id"`
	PromptText       string   `json:"prompt_text"`
	InspirationTags  []string `json:"inspiration_tags"`
	Tone             string   `json:"tone"`
	TimeRangeApplied string   `json:"time_range_applied"`
	ScopeApplied     string   `json:"scope_applied"`
	GenerationMethod string   `json:"generation_method"`
	Category         string   `json:"category"`
}

type ReadQuerier interface {
	GetCommunitySettingsByUserId(ctx context.Context, id pgtype.UUID) (db.GetCommunitySettingsByUserIdRow, error)
	GetThemeRollupsByBucketAndScope(ctx context.Context, arg db.GetThemeRollupsByBucketAndScopeParams) ([]db.SourceCommunityThemeRollup, error)
	GetMoodRollupsByBucketAndScope(ctx context.Context, arg db.GetMoodRollupsByBucketAndScopeParams) ([]db.SourceCommunityMoodRollup, error)
	GetCommunitySummaryByBucketAndScope(ctx context.Context, arg db.GetCommunitySummaryByBucketAndScopeParams) (db.SourceCommunitySummary, error)
	GetCommunityPromptSetByBucketAndScope(ctx context.Context, arg db.GetCommunityPromptSetByBucketAndScopeParams) (db.SourceCommunityPromptSet, error)
}

func ReadCommunityPulse(ctx context.Context, dbq ReadQuerier, viewerUserID, timeRange, scopeType, scopeValue string) (ReadSelection, error) {
	requestedTimeRange, grain, err := normalizePulseTimeRange(timeRange)
	if err != nil {
		return ReadSelection{}, err
	}

	scope, err := resolveScope(ctx, dbq, viewerUserID, scopeType, scopeValue)
	if err != nil {
		return ReadSelection{}, err
	}

	selection, err := fetchSelection(ctx, dbq, requestedTimeRange, grain, scope)
	if err != nil {
		return ReadSelection{}, err
	}
	selection.RequestedTimeRange = requestedTimeRange
	return selection, nil
}

func ReadTodayTogether(ctx context.Context, dbq ReadQuerier, viewerUserID, scopePreference string) (ReadSelection, error) {
	if strings.TrimSpace(viewerUserID) == "" {
		return ReadSelection{}, fmt.Errorf("viewer user ID is required")
	}

	scope, err := resolveScope(ctx, dbq, viewerUserID, scopePreference, "")
	if err != nil {
		return ReadSelection{}, err
	}

	selection, found, err := fetchWithFallback(ctx, dbq, []string{"today", "this_week"}, scope, true)
	if err != nil {
		return ReadSelection{}, err
	}
	if !found {
		return emptySelection("today", scope, false, true), nil
	}
	return selection, nil
}

func ReadCommunityPrompts(ctx context.Context, dbq ReadQuerier, viewerUserID, scopePreference string) (ReadSelection, error) {
	if strings.TrimSpace(viewerUserID) == "" {
		return ReadSelection{}, fmt.Errorf("viewer user ID is required")
	}

	scope, err := resolveScope(ctx, dbq, viewerUserID, scopePreference, "")
	if err != nil {
		return ReadSelection{}, err
	}

	selection, found, err := fetchWithFallback(ctx, dbq, []string{"today", "this_week"}, scope, false)
	if err != nil {
		return ReadSelection{}, err
	}
	if !found {
		return emptySelection("today", scope, false, true), nil
	}
	return selection, nil
}

func DecodePromptSet(data []byte) ([]PromptPayload, error) {
	if len(data) == 0 {
		return nil, nil
	}
	var prompts []PromptPayload
	if err := json.Unmarshal(data, &prompts); err != nil {
		return nil, fmt.Errorf("decode prompt set: %w", err)
	}
	return prompts, nil
}

type resolvedScope struct {
	RequestedType  string
	RequestedValue string
	AppliedType    string
	AppliedValue   string
	Fallback       bool
}

func fetchWithFallback(ctx context.Context, dbq ReadQuerier, timeRanges []string, scope resolvedScope, requireSummary bool) (ReadSelection, bool, error) {
	for idx, requestedTimeRange := range timeRanges {
		grain, err := timeRangeToGrain(requestedTimeRange)
		if err != nil {
			return ReadSelection{}, false, err
		}

		selection, err := fetchSelection(ctx, dbq, requestedTimeRange, grain, scope)
		if err != nil {
			return ReadSelection{}, false, err
		}

		if hasSelection(selection, requireSummary) {
			selection.PeriodFallback = idx > 0
			if selection.PeriodFallback && selection.PrivacyState == PrivacyStateReady {
				selection.PrivacyState = PrivacyStateFallback
			}
			return selection, true, nil
		}
	}

	return ReadSelection{}, false, nil
}

func fetchSelection(ctx context.Context, dbq ReadQuerier, requestedTimeRange, grain string, scope resolvedScope) (ReadSelection, error) {
	anchor := BucketForDate(time.Now().UTC(), grain)

	selection, found, err := fetchExact(ctx, dbq, anchor, grain, scope.RequestedType, scope.RequestedValue)
	if err != nil {
		return ReadSelection{}, err
	}
	if found {
		selection.RequestedScopeType = scope.RequestedType
		selection.RequestedScopeValue = scope.RequestedValue
		selection.RequestedTimeRange = requestedTimeRange
		selection.ScopeFallback = scope.Fallback
		if scope.Fallback {
			selection.PrivacyState = PrivacyStateFallback
		}
		return selection, nil
	}

	if scope.RequestedType == ScopeRegion {
		fallbackScope := resolvedScope{
			RequestedType:  scope.RequestedType,
			RequestedValue: scope.RequestedValue,
			AppliedType:    ScopeGlobal,
			AppliedValue:   ScopeGlobal,
			Fallback:       true,
		}
		selection, found, err = fetchExact(ctx, dbq, anchor, grain, ScopeGlobal, ScopeGlobal)
		if err != nil {
			return ReadSelection{}, err
		}
		if found {
			selection.RequestedScopeType = fallbackScope.RequestedType
			selection.RequestedScopeValue = fallbackScope.RequestedValue
			selection.RequestedTimeRange = requestedTimeRange
			selection.ScopeFallback = true
			selection.PrivacyState = PrivacyStateFallback
			return selection, nil
		}
	}

	return emptySelection(requestedTimeRange, scope, scope.Fallback, false), nil
}

func fetchExact(ctx context.Context, dbq ReadQuerier, bucketDate time.Time, grain, scopeType, scopeValue string) (ReadSelection, bool, error) {
	date := PgDate(bucketDate)

	themes, err := dbq.GetThemeRollupsByBucketAndScope(ctx, db.GetThemeRollupsByBucketAndScopeParams{
		BucketDate: date,
		TimeGrain:  grain,
		ScopeType:  scopeType,
		ScopeValue: scopeValue,
	})
	if err != nil {
		return ReadSelection{}, false, fmt.Errorf("get theme rollups: %w", err)
	}

	moods, err := dbq.GetMoodRollupsByBucketAndScope(ctx, db.GetMoodRollupsByBucketAndScopeParams{
		BucketDate: date,
		TimeGrain:  grain,
		ScopeType:  scopeType,
		ScopeValue: scopeValue,
	})
	if err != nil {
		return ReadSelection{}, false, fmt.Errorf("get mood rollups: %w", err)
	}

	summary, err := dbq.GetCommunitySummaryByBucketAndScope(ctx, db.GetCommunitySummaryByBucketAndScopeParams{
		BucketDate: date,
		TimeGrain:  grain,
		ScopeType:  scopeType,
		ScopeValue: scopeValue,
	})
	var summaryPtr *db.SourceCommunitySummary
	if err == nil {
		summaryPtr = &summary
	} else if !errors.Is(err, pgx.ErrNoRows) {
		return ReadSelection{}, false, fmt.Errorf("get community summary: %w", err)
	}

	promptSet, err := dbq.GetCommunityPromptSetByBucketAndScope(ctx, db.GetCommunityPromptSetByBucketAndScopeParams{
		BucketDate: date,
		TimeGrain:  grain,
		ScopeType:  scopeType,
		ScopeValue: scopeValue,
	})
	var promptPtr *db.SourceCommunityPromptSet
	if err == nil {
		promptPtr = &promptSet
	} else if !errors.Is(err, pgx.ErrNoRows) {
		return ReadSelection{}, false, fmt.Errorf("get community prompt set: %w", err)
	}

	if len(themes) == 0 && len(moods) == 0 && summaryPtr == nil && promptPtr == nil {
		return ReadSelection{}, false, nil
	}

	selection := ReadSelection{
		AppliedTimeRange:  grainToTimeRange(grain),
		AppliedScopeType:  scopeType,
		AppliedScopeValue: scopeValue,
		ThemeMetrics:      themes,
		MoodMetrics:       moods,
		Summary:           summaryPtr,
		PromptSet:         promptPtr,
		GeneratedAt:       latestUpdatedAt(themes, moods, summaryPtr, promptPtr),
		PrivacyState:      PrivacyStateReady,
	}

	return selection, true, nil
}

func resolveScope(ctx context.Context, dbq ReadQuerier, scopeViewerUserID, requestedType, requestedValue string) (resolvedScope, error) {
	requestedType = normalizeScopeType(requestedType)
	requestedValue = strings.TrimSpace(requestedValue)
	if requestedType == "" {
		requestedType = ScopeGlobal
	}

	if requestedType == ScopeGlobal {
		return resolvedScope{
			RequestedType:  ScopeGlobal,
			RequestedValue: ScopeGlobal,
			AppliedType:    ScopeGlobal,
			AppliedValue:   ScopeGlobal,
		}, nil
	}

	if requestedType != ScopeRegion {
		return resolvedScope{}, fmt.Errorf("unsupported scope type: %s", requestedType)
	}

	if requestedValue != "" {
		return resolvedScope{
			RequestedType:  ScopeRegion,
			RequestedValue: strings.ToUpper(requestedValue),
			AppliedType:    ScopeRegion,
			AppliedValue:   strings.ToUpper(requestedValue),
		}, nil
	}

	viewerID, err := uuid.Parse(scopeViewerUserID)
	if err != nil {
		return resolvedScope{}, fmt.Errorf("region scope requires a valid viewer user ID: %w", err)
	}

	settings, err := dbq.GetCommunitySettingsByUserId(ctx, pgtype.UUID{Bytes: viewerID, Valid: true})
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return resolvedScope{
				RequestedType:  ScopeRegion,
				RequestedValue: "",
				AppliedType:    ScopeGlobal,
				AppliedValue:   ScopeGlobal,
				Fallback:       true,
			}, nil
		}
		return resolvedScope{}, fmt.Errorf("get community settings: %w", err)
	}

	if settings.CommunityLocationOptIn && settings.CommunityRegionCode != nil && strings.TrimSpace(*settings.CommunityRegionCode) != "" {
		value := strings.ToUpper(strings.TrimSpace(*settings.CommunityRegionCode))
		return resolvedScope{
			RequestedType:  ScopeRegion,
			RequestedValue: value,
			AppliedType:    ScopeRegion,
			AppliedValue:   value,
		}, nil
	}

	return resolvedScope{
		RequestedType:  ScopeRegion,
		RequestedValue: "",
		AppliedType:    ScopeGlobal,
		AppliedValue:   ScopeGlobal,
		Fallback:       true,
	}, nil
}

func emptySelection(timeRange string, scope resolvedScope, scopeFallback, periodFallback bool) ReadSelection {
	appliedScopeType := scope.AppliedType
	appliedScopeValue := scope.AppliedValue
	if appliedScopeType == "" {
		appliedScopeType = ScopeGlobal
	}
	if appliedScopeValue == "" {
		appliedScopeValue = ScopeGlobal
	}

	state := PrivacyStateInsufficientData
	if scopeFallback || periodFallback {
		state = PrivacyStateFallback
	}

	return ReadSelection{
		RequestedTimeRange:  timeRange,
		AppliedTimeRange:    timeRange,
		RequestedScopeType:  scope.RequestedType,
		RequestedScopeValue: scope.RequestedValue,
		AppliedScopeType:    appliedScopeType,
		AppliedScopeValue:   appliedScopeValue,
		ScopeFallback:       scopeFallback,
		PeriodFallback:      periodFallback,
		PrivacyState:        state,
	}
}

func latestUpdatedAt(themes []db.SourceCommunityThemeRollup, moods []db.SourceCommunityMoodRollup, summary *db.SourceCommunitySummary, promptSet *db.SourceCommunityPromptSet) time.Time {
	var latest time.Time
	for _, item := range themes {
		if item.UpdatedAt.Valid && item.UpdatedAt.Time.After(latest) {
			latest = item.UpdatedAt.Time
		}
	}
	for _, item := range moods {
		if item.UpdatedAt.Valid && item.UpdatedAt.Time.After(latest) {
			latest = item.UpdatedAt.Time
		}
	}
	if summary != nil && summary.UpdatedAt.Valid && summary.UpdatedAt.Time.After(latest) {
		latest = summary.UpdatedAt.Time
	}
	if promptSet != nil && promptSet.UpdatedAt.Valid && promptSet.UpdatedAt.Time.After(latest) {
		latest = promptSet.UpdatedAt.Time
	}
	if latest.IsZero() {
		return time.Now().UTC()
	}
	return latest.UTC()
}

func RisingThemeMetrics(items []db.SourceCommunityThemeRollup, limit int) []db.SourceCommunityThemeRollup {
	filtered := make([]db.SourceCommunityThemeRollup, 0, len(items))
	for _, item := range items {
		if !item.DeltaVsPrevious.Valid {
			continue
		}
		filtered = append(filtered, item)
	}

	slices.SortFunc(filtered, func(a, b db.SourceCommunityThemeRollup) int {
		aDelta := numericToFloat64(a.DeltaVsPrevious)
		bDelta := numericToFloat64(b.DeltaVsPrevious)
		switch {
		case aDelta != bDelta:
			if aDelta < bDelta {
				return 1
			}
			return -1
		case a.EntryCount != b.EntryCount:
			return int(b.EntryCount - a.EntryCount)
		default:
			return strings.Compare(a.ThemeName, b.ThemeName)
		}
	})

	if len(filtered) > limit {
		filtered = filtered[:limit]
	}
	return filtered
}

func normalizeScopeType(value string) string {
	value = strings.ToLower(strings.TrimSpace(value))
	switch value {
	case "", ScopeGlobal:
		return ScopeGlobal
	case ScopeRegion, "nearby":
		return ScopeRegion
	default:
		return value
	}
}

func normalizePulseTimeRange(value string) (string, string, error) {
	value = strings.ToLower(strings.TrimSpace(value))
	if value == "" {
		value = "today"
	}
	grain, err := timeRangeToGrain(value)
	if err != nil {
		return "", "", err
	}
	return value, grain, nil
}

func timeRangeToGrain(value string) (string, error) {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "today":
		return TimeGrainDay, nil
	case "this_week":
		return TimeGrainWeek, nil
	case "this_month":
		return TimeGrainMonth, nil
	default:
		return "", fmt.Errorf("unsupported time range: %s", value)
	}
}

func grainToTimeRange(value string) string {
	switch value {
	case TimeGrainWeek:
		return "this_week"
	case TimeGrainMonth:
		return "this_month"
	default:
		return "today"
	}
}

func hasSelection(selection ReadSelection, requireSummary bool) bool {
	if len(selection.ThemeMetrics) == 0 || len(selection.MoodMetrics) == 0 {
		return false
	}
	if requireSummary && selection.Summary == nil {
		return false
	}
	return true
}

func numericToFloat64(n pgtype.Numeric) float64 {
	if !n.Valid {
		return 0
	}
	v, err := n.Value()
	if err != nil || v == nil {
		return 0
	}
	str, ok := v.(string)
	if !ok {
		return 0
	}
	f, err := strconv.ParseFloat(str, 64)
	if err != nil {
		return 0
	}
	return f
}
