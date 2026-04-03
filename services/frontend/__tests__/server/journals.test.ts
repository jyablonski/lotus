/**
 * Tests for lib/server/journals.ts
 *
 * These test the server-side data-fetching layer by mocking global fetch
 * and verifying correct URL construction, response transformation, error
 * handling, and that the Authorization header is always included.
 */

jest.mock("@/lib/config", () => ({
  BACKEND_URL: "http://backend:8080",
  BACKEND_API_KEY: "test-api-key",
}));

import {
  fetchJournalsForUser,
  fetchRecentJournals,
  fetchAllJournalsForUser,
} from "@/lib/server/journals";

// ---------------------------------------------------------------------------
// Setup: mock global fetch
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
const backendJournals = [
  {
    journalId: "j1",
    userId: "u1",
    journalText: "First entry",
    userMood: "7",
    createdAt: "2025-01-01T00:00:00Z",
  },
  {
    journalId: "j2",
    userId: "u1",
    journalText: "Second entry",
    userMood: "3",
    createdAt: "2025-01-02T00:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// fetchJournalsForUser
// ---------------------------------------------------------------------------
describe("fetchJournalsForUser", () => {
  test("returns transformed journals on successful response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        journals: backendJournals,
        totalCount: "2",
        hasMore: false,
      }),
    });

    const result = await fetchJournalsForUser("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/journals?user_id=u1&limit=10&offset=0"),
      expect.objectContaining({ method: "GET" }),
    );
    expect(result.journals).toHaveLength(2);
    // userMood should be transformed from string to number
    expect(result.journals[0].userMood).toBe(7);
    expect(result.journals[1].userMood).toBe(3);
    expect(result.totalCount).toBe(2);
    expect(result.hasMore).toBe(false);
  });

  test("passes limit and offset to the URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journals: [], totalCount: "0", hasMore: false }),
    });

    await fetchJournalsForUser("u1", { limit: 5, offset: 10 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=5&offset=10"),
      expect.anything(),
    );
  });

  test("uses default limit=10 and offset=0 when no options", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journals: [], totalCount: "0", hasMore: false }),
    });

    await fetchJournalsForUser("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=10&offset=0"),
      expect.anything(),
    );
  });

  test("sends Authorization Bearer header on every request", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journals: [], totalCount: "0", hasMore: false }),
    });

    await fetchJournalsForUser("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-key",
        }),
      }),
    );
  });

  test("returns empty result on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    const result = await fetchJournalsForUser("u1");

    expect(result).toEqual({ journals: [], totalCount: 0, hasMore: false });
  });

  test("returns empty result on network error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network failure"));

    const result = await fetchJournalsForUser("u1");

    expect(result).toEqual({ journals: [], totalCount: 0, hasMore: false });
  });

  test("handles missing journals array in response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ totalCount: "0", hasMore: false }),
    });

    const result = await fetchJournalsForUser("u1");

    expect(result.journals).toEqual([]);
  });

  test("parses totalCount from string", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        journals: [],
        totalCount: "42",
        hasMore: true,
      }),
    });

    const result = await fetchJournalsForUser("u1");

    expect(result.totalCount).toBe(42);
    expect(result.hasMore).toBe(true);
  });

  test("defaults totalCount to 0 when not a number", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        journals: [],
        totalCount: "invalid",
        hasMore: false,
      }),
    });

    const result = await fetchJournalsForUser("u1");

    expect(result.totalCount).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// fetchRecentJournals
// ---------------------------------------------------------------------------
describe("fetchRecentJournals", () => {
  test("returns just the journals array with default count of 5", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        journals: backendJournals,
        totalCount: "2",
        hasMore: false,
      }),
    });

    const journals = await fetchRecentJournals("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=5"),
      expect.anything(),
    );
    expect(journals).toHaveLength(2);
    expect(journals[0].journalId).toBe("j1");
  });

  test("accepts custom count", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ journals: [], totalCount: "0", hasMore: false }),
    });

    await fetchRecentJournals("u1", 3);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=3"),
      expect.anything(),
    );
  });
});

// ---------------------------------------------------------------------------
// fetchAllJournalsForUser
// ---------------------------------------------------------------------------
describe("fetchAllJournalsForUser", () => {
  test("paginates with limit=100 until hasMore is false", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        journals: backendJournals,
        totalCount: "2",
        hasMore: false,
      }),
    });

    const result = await fetchAllJournalsForUser("u1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=100&offset=0"),
      expect.anything(),
    );
    expect(result.journals).toHaveLength(2);
  });

  test("loads multiple pages when hasMore is true", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          journals: [backendJournals[0]],
          totalCount: "2",
          hasMore: true,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          journals: [backendJournals[1]],
          totalCount: "2",
          hasMore: false,
        }),
      });

    const result = await fetchAllJournalsForUser("u1");

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.journals).toHaveLength(2);
  });
});
