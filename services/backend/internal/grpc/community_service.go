package grpc

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/community"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/community"
)

type CommunityServer struct {
	pb.UnimplementedCommunityServiceServer
}

func (s *CommunityServer) GetCommunityPulse(ctx context.Context, req *pb.GetCommunityPulseRequest) (*pb.GetCommunityPulseResponse, error) {
	if strings.TrimSpace(req.TimeRange) == "" {
		req.TimeRange = "today"
	}
	if req.ViewerUserId != "" {
		if _, err := uuid.Parse(req.ViewerUserId); err != nil {
			return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
		}
	}

	dbq := inject.DBFrom(ctx)
	selection, err := community.ReadCommunityPulse(ctx, dbq, req.ViewerUserId, req.TimeRange, req.ScopeType, req.ScopeValue)
	if err != nil {
		return nil, err
	}

	return &pb.GetCommunityPulseResponse{
		RequestedTimeRange:  selection.RequestedTimeRange,
		AppliedTimeRange:    selection.AppliedTimeRange,
		RequestedScopeType:  selection.RequestedScopeType,
		RequestedScopeValue: selection.RequestedScopeValue,
		AppliedScopeType:    selection.AppliedScopeType,
		AppliedScopeValue:   selection.AppliedScopeValue,
		TopThemes:           pulseMetrics(selection.ThemeMetrics),
		TopMoods:            moodMetrics(selection.MoodMetrics),
		RisingThemes:        pulseMetrics(community.RisingThemeMetrics(selection.ThemeMetrics, 3)),
		CommunitySummary:    communitySummary(selection),
		Privacy:             privacy(selection),
		GeneratedAt:         selection.GeneratedAt.Format(time.RFC3339),
	}, nil
}

func (s *CommunityServer) GetTodayTogether(ctx context.Context, req *pb.GetTodayTogetherRequest) (*pb.GetTodayTogetherResponse, error) {
	if _, err := uuid.Parse(req.ViewerUserId); err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	dbq := inject.DBFrom(ctx)
	selection, err := community.ReadTodayTogether(ctx, dbq, req.ViewerUserId, req.ScopePreference)
	if err != nil {
		return nil, err
	}

	var bucketDate string
	if selection.AppliedTimeRange != "" {
		bucketDate = community.BucketForDate(time.Now().UTC(), communityTimeRangeToGrain(selection.AppliedTimeRange)).Format("2006-01-02")
	}

	return &pb.GetTodayTogetherResponse{
		BucketDate:        bucketDate,
		PeriodApplied:     selection.AppliedTimeRange,
		Themes:            limitedPulseMetrics(selection.ThemeMetrics, 3),
		DominantMood:      dominantMood(selection.MoodMetrics),
		CommunityNote:     communitySummary(selection),
		ScopeTypeApplied:  selection.AppliedScopeType,
		ScopeValueApplied: selection.AppliedScopeValue,
		Privacy:           privacy(selection),
		GeneratedAt:       selection.GeneratedAt.Format(time.RFC3339),
	}, nil
}

func (s *CommunityServer) GetCommunityPrompts(ctx context.Context, req *pb.GetCommunityPromptsRequest) (*pb.GetCommunityPromptsResponse, error) {
	if _, err := uuid.Parse(req.ViewerUserId); err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	dbq := inject.DBFrom(ctx)
	selection, err := community.ReadCommunityPrompts(ctx, dbq, req.ViewerUserId, req.ScopePreference)
	if err != nil {
		return nil, err
	}

	prompts, err := decodePrompts(selection)
	if err != nil {
		return nil, err
	}

	featured, alternates := splitPrompts(prompts, req.Surface)
	return &pb.GetCommunityPromptsResponse{
		FeaturedPrompt:    featured,
		AlternatePrompts:  alternates,
		TimeRangeApplied:  selection.AppliedTimeRange,
		ScopeTypeApplied:  selection.AppliedScopeType,
		ScopeValueApplied: selection.AppliedScopeValue,
		Privacy:           privacy(selection),
		GeneratedAt:       selection.GeneratedAt.Format(time.RFC3339),
	}, nil
}

func pulseMetrics(items []db.SourceCommunityThemeRollup) []*pb.CommunityMetric {
	metrics := make([]*pb.CommunityMetric, 0, len(items))
	for _, item := range items {
		metric := &pb.CommunityMetric{
			Name:            item.ThemeName,
			EntryCount:      item.EntryCount,
			UniqueUserCount: item.UniqueUserCount,
			Rank:            item.Rank,
		}
		if item.DeltaVsPrevious.Valid {
			delta := communityNumericToFloat(item.DeltaVsPrevious)
			metric.DeltaVsPrevious = &delta
		}
		metrics = append(metrics, metric)
	}
	return metrics
}

func limitedPulseMetrics(items []db.SourceCommunityThemeRollup, limit int) []*pb.CommunityMetric {
	if len(items) > limit {
		items = items[:limit]
	}
	return pulseMetrics(items)
}

func moodMetrics(items []db.SourceCommunityMoodRollup) []*pb.CommunityMetric {
	metrics := make([]*pb.CommunityMetric, 0, len(items))
	for _, item := range items {
		metric := &pb.CommunityMetric{
			Name:            item.MoodName,
			EntryCount:      item.EntryCount,
			UniqueUserCount: item.UniqueUserCount,
			Rank:            item.Rank,
		}
		if item.DeltaVsPrevious.Valid {
			delta := communityNumericToFloat(item.DeltaVsPrevious)
			metric.DeltaVsPrevious = &delta
		}
		metrics = append(metrics, metric)
	}
	return metrics
}

func dominantMood(items []db.SourceCommunityMoodRollup) string {
	if len(items) == 0 {
		return ""
	}
	return items[0].MoodName
}

func communitySummary(selection community.ReadSelection) string {
	if selection.Summary == nil {
		return ""
	}
	return selection.Summary.SummaryText
}

func privacy(selection community.ReadSelection) *pb.PrivacyMetadata {
	return &pb.PrivacyMetadata{
		State:                 selection.PrivacyState,
		ScopeFallbackApplied:  selection.ScopeFallback,
		PeriodFallbackApplied: selection.PeriodFallback,
	}
}

func decodePrompts(selection community.ReadSelection) ([]community.PromptPayload, error) {
	if selection.PromptSet == nil {
		return nil, nil
	}
	return community.DecodePromptSet(selection.PromptSet.PromptSetJson)
}

func splitPrompts(prompts []community.PromptPayload, surface string) (*pb.CommunityPrompt, []*pb.CommunityPrompt) {
	if len(prompts) == 0 {
		return nil, nil
	}

	limit := 4
	switch strings.ToLower(strings.TrimSpace(surface)) {
	case "dashboard":
		limit = 2
	case "journal_create", "community_page", "":
		limit = 4
	}

	featured := toPromptPB(prompts[0])
	alternatePayloads := prompts[1:]
	if len(alternatePayloads) > limit {
		alternatePayloads = alternatePayloads[:limit]
	}

	alternates := make([]*pb.CommunityPrompt, 0, len(alternatePayloads))
	for _, prompt := range alternatePayloads {
		alternates = append(alternates, toPromptPB(prompt))
	}
	return featured, alternates
}

func toPromptPB(prompt community.PromptPayload) *pb.CommunityPrompt {
	return &pb.CommunityPrompt{
		PromptId:         prompt.PromptID,
		PromptText:       prompt.PromptText,
		InspirationTags:  prompt.InspirationTags,
		Tone:             prompt.Tone,
		TimeRangeApplied: prompt.TimeRangeApplied,
		ScopeApplied:     prompt.ScopeApplied,
		GenerationMethod: prompt.GenerationMethod,
		Category:         prompt.Category,
	}
}

func communityTimeRangeToGrain(timeRange string) string {
	switch timeRange {
	case "this_week":
		return community.TimeGrainWeek
	case "this_month":
		return community.TimeGrainMonth
	default:
		return community.TimeGrainDay
	}
}

func communityNumericToFloat(n pgtype.Numeric) float64 {
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
