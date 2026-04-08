jest.mock("@/lib/config", () => ({
  BACKEND_URL: "http://backend:8080",
  BACKEND_API_KEY: "test-api-key",
}));

import {
  fetchCommunityPrompts,
  fetchCommunityPulse,
  fetchTodayTogether,
} from "@/lib/server/community";

const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("fetchCommunityPulse", () => {
  it("requests the nearby scope and maps the response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        appliedTimeRange: "today",
        appliedScopeType: "region",
        appliedScopeValue: "US-CA",
        topThemes: [
          {
            name: "rest",
            entryCount: 12,
            uniqueUserCount: 11,
            rank: 1,
            deltaVsPrevious: 0.15,
          },
        ],
        topMoods: [],
        risingThemes: [],
        communitySummary: "People are slowing down together.",
        privacy: {
          state: "ready",
          scopeFallbackApplied: false,
          periodFallbackApplied: false,
        },
        generatedAt: "2026-04-07T10:00:00Z",
      }),
    });

    const result = await fetchCommunityPulse("user-123", {
      timeRange: "today",
      scope: "nearby",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/v1/community/pulse?viewer_user_id=user-123&time_range=today&scope_type=region",
      ),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-key",
        }),
      }),
    );
    expect(result?.appliedScopeType).toBe("region");
    expect(result?.topThemes[0]?.name).toBe("rest");
    expect(result?.communitySummary).toBe("People are slowing down together.");
    expect(result?.isEmpty).toBe(false);
  });
});

describe("fetchTodayTogether", () => {
  it("normalizes a compact today together payload", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        bucketDate: "2026-04-07",
        periodApplied: "today",
        themes: [
          {
            name: "change",
            entryCount: 9,
            uniqueUserCount: 9,
            rank: 1,
          },
        ],
        dominantMood: "hopeful",
        communityNote: "A lot of people are trying to reset.",
        scopeTypeApplied: "global",
        scopeValueApplied: "global",
        privacy: {
          state: "fallback",
          scopeFallbackApplied: true,
          periodFallbackApplied: false,
        },
      }),
    });

    const result = await fetchTodayTogether("user-123");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/v1/community/today-together?viewer_user_id=user-123&scope_preference=nearby",
      ),
      expect.anything(),
    );
    expect(result?.dominantMood).toBe("hopeful");
    expect(result?.privacy.scopeFallbackApplied).toBe(true);
  });
});

describe("fetchCommunityPrompts", () => {
  it("returns null when the backend request fails", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
    });

    const result = await fetchCommunityPrompts("user-123", {
      surface: "journal_create",
      scope: "nearby",
    });

    expect(result).toBeNull();
  });
});
