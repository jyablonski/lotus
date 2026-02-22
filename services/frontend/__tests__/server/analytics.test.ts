/**
 * Tests for lib/server/analytics.ts
 *
 * Tests fetchUserAnalytics by mocking global fetch and verifying correct
 * URL construction, response mapping, and error handling.
 */

import { fetchUserAnalytics } from "@/lib/server/analytics";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const backendSummary = {
  userId: "u1",
  userEmail: "test@example.com",
  userRole: "user",
  userTimezone: "UTC",
  userCreatedAt: "2025-01-01T00:00:00Z",
  totalJournals: 10,
  activeDays: 5,
  avgMoodScore: 6.5,
  minMoodScore: 2,
  maxMoodScore: 8,
  moodScoreStddev: 1.2,
  positiveEntries: 6,
  negativeEntries: 2,
  neutralEntries: 2,
  avgSentimentScore: 0.7,
  avgJournalLength: 150,
  firstJournalAt: "2025-01-01T00:00:00Z",
  lastJournalAt: "2025-01-10T00:00:00Z",
  lastModifiedAt: "2025-01-10T00:00:00Z",
  totalJournals_30d: 8,
  avgMoodScore_30d: 6.8,
  minMoodScore_30d: 3,
  maxMoodScore_30d: 8,
  dailyStreak: 3,
  positivePercentage: 60,
  daysSinceLastJournal: 1,
  daysBetweenFirstAndLastJournal: 9,
  journalsPerActiveDay: 2.0,
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("fetchUserAnalytics", () => {
  test("returns mapped analytics on success", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ summary: backendSummary }),
    });

    const result = await fetchUserAnalytics("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/analytics/users/u1/journal-summary"),
      expect.objectContaining({ method: "GET" }),
    );
    expect(result).not.toBeNull();
    expect(result!.userId).toBe("u1");
    expect(result!.totalJournals).toBe(10);
    expect(result!.avgMoodScore).toBe(6.5);
    expect(result!.totalJournals30d).toBe(8);
    expect(result!.avgMoodScore30d).toBe(6.8);
    expect(result!.dailyStreak).toBe(3);
  });

  test("returns null on 404 (new user, no analytics)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });

    const result = await fetchUserAnalytics("u1");

    expect(result).toBeNull();
  });

  test("returns null on non-404 error", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    const result = await fetchUserAnalytics("u1");

    expect(result).toBeNull();
  });

  test("returns null on network error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Connection refused"));

    const result = await fetchUserAnalytics("u1");

    expect(result).toBeNull();
  });

  test("defaults numeric fields to 0 when missing", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        summary: {
          userId: "u1",
          userEmail: "test@example.com",
          userRole: "user",
          userTimezone: "UTC",
          userCreatedAt: "2025-01-01",
          // All numeric fields missing/undefined
        },
      }),
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).not.toBeNull();
    expect(result!.totalJournals).toBe(0);
    expect(result!.activeDays).toBe(0);
    expect(result!.positiveEntries).toBe(0);
    expect(result!.negativeEntries).toBe(0);
    expect(result!.neutralEntries).toBe(0);
    expect(result!.totalJournals30d).toBe(0);
    expect(result!.dailyStreak).toBe(0);
  });

  test("uses null for nullable fields when missing", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        summary: {
          userId: "u1",
          userEmail: "test@example.com",
          userRole: "user",
          userTimezone: "UTC",
          userCreatedAt: "2025-01-01",
        },
      }),
    });

    const result = await fetchUserAnalytics("u1");

    expect(result!.avgMoodScore).toBeNull();
    expect(result!.minMoodScore).toBeNull();
    expect(result!.maxMoodScore).toBeNull();
    expect(result!.avgSentimentScore).toBeNull();
    expect(result!.avgJournalLength).toBeNull();
    expect(result!.firstJournalAt).toBeNull();
    expect(result!.lastJournalAt).toBeNull();
    expect(result!.positivePercentage).toBeNull();
    expect(result!.daysSinceLastJournal).toBeNull();
  });
});
