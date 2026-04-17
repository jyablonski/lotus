import { JournalEntry } from "@/types/journal";

jest.mock("@/lib/server/journals", () => ({
  fetchAllJournalsForUser: jest.fn(),
}));

import { fetchUserAnalytics } from "@/lib/server/analytics";
import { fetchAllJournalsForUser } from "@/lib/server/journals";

const mockFetchAll = fetchAllJournalsForUser as jest.MockedFunction<
  typeof fetchAllJournalsForUser
>;

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

function makeJournal(
  overrides: Partial<JournalEntry> & { createdAt: string },
): JournalEntry {
  return {
    journalId: "j1",
    userId: "u1",
    journalText: "A test journal entry with some words",
    userMood: 5,
    ...overrides,
  };
}

const now = new Date();
const today = now.toISOString();
const yesterday = new Date(
  now.getTime() - 1 * 24 * 60 * 60 * 1000,
).toISOString();
const twoDaysAgo = new Date(
  now.getTime() - 2 * 24 * 60 * 60 * 1000,
).toISOString();

const sampleJournals: JournalEntry[] = [
  makeJournal({
    journalId: "j1",
    userMood: 8,
    journalText: "Great day today",
    createdAt: today,
  }),
  makeJournal({
    journalId: "j2",
    userMood: 7,
    journalText: "Good day yesterday",
    createdAt: yesterday,
  }),
  makeJournal({
    journalId: "j3",
    userMood: 3,
    journalText: "Rough day two days ago",
    createdAt: twoDaysAgo,
  }),
];

describe("fetchUserAnalytics", () => {
  test("returns computed analytics from journals", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: sampleJournals,
      totalCount: 3,
      hasMore: false,
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).not.toBeNull();
    expect(result!.userId).toBe("u1");
    expect(result!.totalJournals).toBe(3);
    expect(result!.positiveEntries).toBe(2);
    expect(result!.negativeEntries).toBe(1);
    expect(result!.neutralEntries).toBe(0);
    expect(result!.minMoodScore).toBe(3);
    expect(result!.maxMoodScore).toBe(8);
    expect(result!.avgMoodScore).toBeCloseTo(6, 0);
  });

  test("returns null when no journals exist", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: [],
      totalCount: 0,
      hasMore: false,
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).toBeNull();
  });

  test("returns null on error", async () => {
    mockFetchAll.mockRejectedValueOnce(new Error("Connection refused"));

    const result = await fetchUserAnalytics("u1");

    expect(result).toBeNull();
  });

  test("computes 30-day metrics correctly", async () => {
    const oldJournal = makeJournal({
      journalId: "j-old",
      userMood: 2,
      createdAt: new Date(
        now.getTime() - 60 * 24 * 60 * 60 * 1000,
      ).toISOString(),
    });

    mockFetchAll.mockResolvedValueOnce({
      journals: [...sampleJournals, oldJournal],
      totalCount: 4,
      hasMore: false,
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).not.toBeNull();
    expect(result!.totalJournals).toBe(4);
    expect(result!.totalJournals30d).toBe(3);
  });

  test("computes streak correctly", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: sampleJournals,
      totalCount: 3,
      hasMore: false,
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).not.toBeNull();
    expect(result!.dailyStreak).toBe(3);
  });

  test("computes positive percentage", async () => {
    mockFetchAll.mockResolvedValueOnce({
      journals: sampleJournals,
      totalCount: 3,
      hasMore: false,
    });

    const result = await fetchUserAnalytics("u1");

    expect(result).not.toBeNull();
    expect(result!.positivePercentage).toBeCloseTo(66.67, 1);
  });
});
