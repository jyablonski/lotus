/**
 * Tests for lib/server/profile.ts
 *
 * Tests fetchProfileStats by mocking the journals fetcher and verifying
 * it delegates correctly to calculateProfileStats.
 */

import { fetchProfileStats } from "@/lib/server/profile";

// Mock the journals module that profile.ts depends on
jest.mock("@/lib/server/journals", () => ({
  fetchAllJournalsForUser: jest.fn(),
}));

import { fetchAllJournalsForUser } from "@/lib/server/journals";
const mockFetchAll = fetchAllJournalsForUser as jest.MockedFunction<
  typeof fetchAllJournalsForUser
>;

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const mockJournals = [
  {
    journalId: "j1",
    userId: "u1",
    journalText: "Hello world",
    userMood: 7,
    createdAt: new Date().toISOString(),
  },
  {
    journalId: "j2",
    userId: "u1",
    journalText: "Another day another entry",
    userMood: 5,
    createdAt: new Date().toISOString(),
  },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("fetchProfileStats", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("fetches all journals and returns computed stats", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: mockJournals,
      totalCount: 2,
      hasMore: false,
    });

    const stats = await fetchProfileStats("u1");

    expect(mockFetchAll).toHaveBeenCalledWith("u1");
    expect(stats.totalEntries).toBe(2);
    expect(stats.averageMood).toBeDefined();
    expect(stats.totalWords).toBeGreaterThan(0);
  });

  test("returns zero stats when user has no journals", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: [],
      totalCount: 0,
      hasMore: false,
    });

    const stats = await fetchProfileStats("u1");

    expect(stats.totalEntries).toBe(0);
    expect(stats.currentStreak).toBe(0);
    expect(stats.longestStreak).toBe(0);
    expect(stats.totalWords).toBe(0);
  });
});
