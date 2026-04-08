import "server-only";

import { BACKEND_URL } from "@/lib/config";
import { backendHeaders } from "@/lib/server/backendHeaders";
import type {
  CommunityMetric,
  CommunityPrivacyMetadata,
  CommunityPrompt,
  CommunityPromptSetData,
  CommunityPulseData,
  CommunityScopePreference,
  CommunityScopeType,
  CommunityTimeRange,
  TodayTogetherData,
} from "@/types/community";

function pickValue<T>(
  value: Record<string, unknown> | null | undefined,
  camelKey: string,
  snakeKey: string,
): T | undefined {
  return (value?.[camelKey] ?? value?.[snakeKey]) as T | undefined;
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asNumber(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function asBoolean(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function normalizeMetric(raw: unknown): CommunityMetric {
  const value = raw as Record<string, unknown> | null | undefined;
  const delta =
    pickValue<number | null>(value, "deltaVsPrevious", "delta_vs_previous") ??
    null;

  return {
    name: asString(pickValue(value, "name", "name")),
    entryCount: asNumber(pickValue(value, "entryCount", "entry_count")),
    uniqueUserCount: asNumber(
      pickValue(value, "uniqueUserCount", "unique_user_count"),
    ),
    rank: asNumber(pickValue(value, "rank", "rank")),
    deltaVsPrevious: typeof delta === "number" ? delta : null,
  };
}

function normalizePrompt(raw: unknown): CommunityPrompt {
  const value = raw as Record<string, unknown> | null | undefined;

  return {
    promptId: asString(pickValue(value, "promptId", "prompt_id")),
    promptText: asString(pickValue(value, "promptText", "prompt_text")),
    inspirationTags: asStringArray(
      pickValue(value, "inspirationTags", "inspiration_tags"),
    ),
    tone: asString(pickValue(value, "tone", "tone")),
    timeRangeApplied: asString(
      pickValue(value, "timeRangeApplied", "time_range_applied"),
    ),
    scopeApplied: asString(pickValue(value, "scopeApplied", "scope_applied")),
    generationMethod: asString(
      pickValue(value, "generationMethod", "generation_method"),
    ),
    category: asString(pickValue(value, "category", "category")),
  };
}

function normalizePrivacy(raw: unknown): CommunityPrivacyMetadata {
  const value = raw as Record<string, unknown> | null | undefined;
  const state = asString(pickValue(value, "state", "state"));

  return {
    state:
      state === "ready" || state === "fallback" || state === "insufficient_data"
        ? state
        : "insufficient_data",
    scopeFallbackApplied: asBoolean(
      pickValue(value, "scopeFallbackApplied", "scope_fallback_applied"),
    ),
    periodFallbackApplied: asBoolean(
      pickValue(value, "periodFallbackApplied", "period_fallback_applied"),
    ),
  };
}

async function fetchCommunityEndpoint(
  path: string,
  params: Record<string, string>,
): Promise<Record<string, unknown> | null> {
  const url = new URL(`${BACKEND_URL}${path}`);

  for (const [key, value] of Object.entries(params)) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }

  try {
    const response = await fetch(url.toString(), {
      method: "GET",
      headers: backendHeaders(),
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(`Community endpoint error: ${path} ${response.status}`);
      return null;
    }

    return (await response.json()) as Record<string, unknown>;
  } catch (error) {
    console.error(`Error fetching community endpoint ${path}:`, error);
    return null;
  }
}

function normalizeScopePreference(value: CommunityScopePreference): {
  scopeType: CommunityScopeType;
  scopeValue?: string;
} {
  if (value === "nearby") {
    return { scopeType: "region" };
  }

  return { scopeType: "global", scopeValue: "global" };
}

export async function fetchCommunityPulse(
  userId: string,
  options?: {
    timeRange?: CommunityTimeRange;
    scope?: CommunityScopePreference;
  },
): Promise<CommunityPulseData | null> {
  const timeRange = options?.timeRange ?? "today";
  const scope = options?.scope ?? "nearby";
  const normalizedScope = normalizeScopePreference(scope);

  const payload = await fetchCommunityEndpoint("/v1/community/pulse", {
    viewer_user_id: userId,
    time_range: timeRange,
    scope_type: normalizedScope.scopeType,
    ...(normalizedScope.scopeValue
      ? { scope_value: normalizedScope.scopeValue }
      : {}),
  });

  if (!payload) {
    return null;
  }

  const topThemes = Array.isArray(payload.topThemes)
    ? payload.topThemes.map(normalizeMetric)
    : [];
  const topMoods = Array.isArray(payload.topMoods)
    ? payload.topMoods.map(normalizeMetric)
    : [];
  const risingThemes = Array.isArray(payload.risingThemes)
    ? payload.risingThemes.map(normalizeMetric)
    : [];

  return {
    requestedTimeRange: timeRange,
    requestedScope: scope,
    appliedTimeRange: asString(
      pickValue(payload, "appliedTimeRange", "applied_time_range"),
    ),
    appliedScopeType: asString(
      pickValue(payload, "appliedScopeType", "applied_scope_type"),
    ) as CommunityScopeType | "",
    appliedScopeValue: asString(
      pickValue(payload, "appliedScopeValue", "applied_scope_value"),
    ),
    topThemes,
    topMoods,
    risingThemes,
    communitySummary: asString(
      pickValue(payload, "communitySummary", "community_summary"),
    ),
    privacy: normalizePrivacy(payload.privacy),
    generatedAt:
      asString(pickValue(payload, "generatedAt", "generated_at")) || null,
    isEmpty:
      topThemes.length === 0 &&
      topMoods.length === 0 &&
      risingThemes.length === 0 &&
      !asString(pickValue(payload, "communitySummary", "community_summary")),
  };
}

export async function fetchTodayTogether(
  userId: string,
  scopePreference: CommunityScopePreference = "nearby",
): Promise<TodayTogetherData | null> {
  const payload = await fetchCommunityEndpoint("/v1/community/today-together", {
    viewer_user_id: userId,
    scope_preference: scopePreference,
  });

  if (!payload) {
    return null;
  }

  const themes = Array.isArray(payload.themes)
    ? payload.themes.map(normalizeMetric)
    : [];

  return {
    bucketDate:
      asString(pickValue(payload, "bucketDate", "bucket_date")) || null,
    periodApplied: asString(
      pickValue(payload, "periodApplied", "period_applied"),
    ),
    themes,
    dominantMood: asString(pickValue(payload, "dominantMood", "dominant_mood")),
    communityNote: asString(
      pickValue(payload, "communityNote", "community_note"),
    ),
    appliedScopeType: asString(
      pickValue(payload, "scopeTypeApplied", "scope_type_applied"),
    ) as CommunityScopeType | "",
    appliedScopeValue: asString(
      pickValue(payload, "scopeValueApplied", "scope_value_applied"),
    ),
    privacy: normalizePrivacy(payload.privacy),
    generatedAt:
      asString(pickValue(payload, "generatedAt", "generated_at")) || null,
    isEmpty:
      themes.length === 0 &&
      !asString(pickValue(payload, "dominantMood", "dominant_mood")) &&
      !asString(pickValue(payload, "communityNote", "community_note")),
  };
}

export async function fetchCommunityPrompts(
  userId: string,
  options?: {
    surface?: "dashboard" | "journal_create" | "community_page";
    scope?: CommunityScopePreference;
  },
): Promise<CommunityPromptSetData | null> {
  const payload = await fetchCommunityEndpoint("/v1/community/prompts", {
    viewer_user_id: userId,
    surface: options?.surface ?? "community_page",
    scope_preference: options?.scope ?? "nearby",
  });

  if (!payload) {
    return null;
  }

  const featuredPrompt = payload.featuredPrompt
    ? normalizePrompt(payload.featuredPrompt)
    : null;
  const alternatePrompts = Array.isArray(payload.alternatePrompts)
    ? payload.alternatePrompts.map(normalizePrompt)
    : [];

  return {
    featuredPrompt,
    alternatePrompts,
    timeRangeApplied: asString(
      pickValue(payload, "timeRangeApplied", "time_range_applied"),
    ),
    appliedScopeType: asString(
      pickValue(payload, "scopeTypeApplied", "scope_type_applied"),
    ) as CommunityScopeType | "",
    appliedScopeValue: asString(
      pickValue(payload, "scopeValueApplied", "scope_value_applied"),
    ),
    privacy: normalizePrivacy(payload.privacy),
    generatedAt:
      asString(pickValue(payload, "generatedAt", "generated_at")) || null,
    isEmpty: !featuredPrompt && alternatePrompts.length === 0,
  };
}
