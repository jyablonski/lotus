export type CommunityTimeRange = "today" | "this_week" | "this_month";

export type CommunityScopePreference = "global" | "nearby";

export type CommunityScopeType = "global" | "region";

export type CommunityPrivacyState = "ready" | "fallback" | "insufficient_data";

export interface CommunityMetric {
  name: string;
  entryCount: number;
  uniqueUserCount: number;
  rank: number;
  deltaVsPrevious: number | null;
}

export interface CommunityPrivacyMetadata {
  state: CommunityPrivacyState;
  scopeFallbackApplied: boolean;
  periodFallbackApplied: boolean;
}

export interface CommunityPrompt {
  promptId: string;
  promptText: string;
  inspirationTags: string[];
  tone: string;
  timeRangeApplied: string;
  scopeApplied: string;
  generationMethod: string;
  category: string;
}

export interface CommunityPulseData {
  requestedTimeRange: CommunityTimeRange;
  appliedTimeRange: string;
  requestedScope: CommunityScopePreference;
  appliedScopeType: CommunityScopeType | "";
  appliedScopeValue: string;
  topThemes: CommunityMetric[];
  topMoods: CommunityMetric[];
  risingThemes: CommunityMetric[];
  communitySummary: string;
  privacy: CommunityPrivacyMetadata;
  generatedAt: string | null;
  isEmpty: boolean;
}

export interface TodayTogetherData {
  bucketDate: string | null;
  periodApplied: string;
  themes: CommunityMetric[];
  dominantMood: string;
  communityNote: string;
  appliedScopeType: CommunityScopeType | "";
  appliedScopeValue: string;
  privacy: CommunityPrivacyMetadata;
  generatedAt: string | null;
  isEmpty: boolean;
}

export interface CommunityPromptSetData {
  featuredPrompt: CommunityPrompt | null;
  alternatePrompts: CommunityPrompt[];
  timeRangeApplied: string;
  appliedScopeType: CommunityScopeType | "";
  appliedScopeValue: string;
  privacy: CommunityPrivacyMetadata;
  generatedAt: string | null;
  isEmpty: boolean;
}

export const COMMUNITY_TIME_RANGE_OPTIONS: ReadonlyArray<{
  value: CommunityTimeRange;
  label: string;
}> = [
  { value: "today", label: "Today" },
  { value: "this_week", label: "This Week" },
  { value: "this_month", label: "This Month" },
];

export const COMMUNITY_SCOPE_OPTIONS: ReadonlyArray<{
  value: CommunityScopePreference;
  label: string;
}> = [
  { value: "nearby", label: "Nearby" },
  { value: "global", label: "Global" },
];

export function formatCommunityTimeRangeLabel(value: string): string {
  switch (value) {
    case "today":
    case "day":
      return "Today";
    case "this_week":
    case "week":
      return "This Week";
    case "this_month":
    case "month":
      return "This Month";
    default:
      return "Recent";
  }
}

export function formatCommunityScopeLabel(
  scopeType: string,
  _scopeValue?: string,
): string {
  if (scopeType === "region") {
    return "Nearby community";
  }
  return "Global community";
}

export function formatCommunityDateLabel(value: string | null): string {
  if (!value) {
    return "Today";
  }

  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return "Today";
  }

  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  }).format(date);
}

export function isCommunityFallback(
  privacy: CommunityPrivacyMetadata | null | undefined,
): boolean {
  return Boolean(
    privacy &&
    (privacy.scopeFallbackApplied ||
      privacy.periodFallbackApplied ||
      privacy.state === "fallback"),
  );
}
