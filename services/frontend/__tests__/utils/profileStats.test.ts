import {
  getUniqueDateStrings,
  calculateBasicCounts,
  calculateAverageMood,
  getFirstEntryDate,
  getMostActiveDay,
  getFavoriteMoodCategory,
  calculateTotalWords,
  calculateCurrentStreak,
  calculateLongestStreak,
  calculateProfileStats,
} from "@/lib/utils/profileStats";
import { JournalEntry } from "@/types/journal";

/** Helper to create a JournalEntry with sensible defaults. */
function makeEntry(
  overrides: Partial<JournalEntry> & { createdAt: string },
): JournalEntry {
  return {
    journalId: "1",
    userId: "user1",
    journalText: "Some text",
    userMood: 5,
    ...overrides,
  };
}

/** Build a list of entries on consecutive days ending on `endDate`. */
function makeStreakEntries(days: number, endDateStr: string): JournalEntry[] {
  const entries: JournalEntry[] = [];
  const end = new Date(endDateStr);
  for (let i = 0; i < days; i++) {
    const d = new Date(end);
    d.setDate(d.getDate() - i);
    entries.push(
      makeEntry({
        journalId: String(i),
        createdAt: d.toISOString(),
      }),
    );
  }
  return entries;
}

describe("profileStats", () => {
  describe("getUniqueDateStrings", () => {
    test("returns empty set for no journals", () => {
      expect(getUniqueDateStrings([]).size).toBe(0);
    });

    test("deduplicates entries on the same day", () => {
      const entries = [
        makeEntry({ createdAt: "2025-06-01T08:00:00Z" }),
        makeEntry({ createdAt: "2025-06-01T20:00:00Z" }),
        makeEntry({ createdAt: "2025-06-02T12:00:00Z" }),
      ];
      const dates = getUniqueDateStrings(entries);
      expect(dates.size).toBe(2);
      expect(dates.has("2025-06-01")).toBe(true);
      expect(dates.has("2025-06-02")).toBe(true);
    });
  });

  describe("calculateBasicCounts", () => {
    test("returns zeros for empty array", () => {
      const counts = calculateBasicCounts([]);
      expect(counts.totalEntries).toBe(0);
      expect(counts.thisMonth).toBe(0);
      expect(counts.thisWeek).toBe(0);
    });

    test("counts total entries correctly", () => {
      const entries = [
        makeEntry({ createdAt: "2020-01-01T00:00:00Z" }),
        makeEntry({ createdAt: "2020-01-02T00:00:00Z" }),
      ];
      expect(calculateBasicCounts(entries).totalEntries).toBe(2);
    });

    test("counts entries this week", () => {
      const now = new Date();
      const recent = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
      const old = new Date("2020-01-01");
      const entries = [
        makeEntry({ createdAt: recent.toISOString() }),
        makeEntry({ createdAt: old.toISOString() }),
      ];
      const counts = calculateBasicCounts(entries);
      expect(counts.thisWeek).toBe(1);
    });
  });

  describe("calculateAverageMood", () => {
    test("returns 0 for no journals", () => {
      expect(calculateAverageMood([])).toBe(0);
    });

    test("calculates average correctly", () => {
      const entries = [
        makeEntry({ createdAt: "2025-01-01T00:00:00Z", userMood: 8 }),
        makeEntry({ createdAt: "2025-01-02T00:00:00Z", userMood: 4 }),
      ];
      expect(calculateAverageMood(entries)).toBe(6);
    });

    test("handles single entry", () => {
      const entries = [
        makeEntry({ createdAt: "2025-01-01T00:00:00Z", userMood: 3 }),
      ];
      expect(calculateAverageMood(entries)).toBe(3);
    });
  });

  describe("getFirstEntryDate", () => {
    test("returns null for no journals", () => {
      expect(getFirstEntryDate([])).toBeNull();
    });

    test("returns last element createdAt (oldest when sorted desc)", () => {
      const entries = [
        makeEntry({ createdAt: "2025-06-15T00:00:00Z" }),
        makeEntry({ createdAt: "2025-06-01T00:00:00Z" }),
      ];
      expect(getFirstEntryDate(entries)).toBe("2025-06-01T00:00:00Z");
    });
  });

  describe("getMostActiveDay", () => {
    test('returns "No data" for empty array', () => {
      expect(getMostActiveDay([])).toBe("No data");
    });

    test("returns the day with the most entries", () => {
      // 2025-06-02 is a Monday (3 entries), 2025-06-03 is a Tuesday (1 entry).
      const entries = [
        makeEntry({ createdAt: "2025-06-02T08:00:00Z" }),
        makeEntry({ createdAt: "2025-06-02T12:00:00Z" }),
        makeEntry({ createdAt: "2025-06-02T18:00:00Z" }),
        makeEntry({ createdAt: "2025-06-03T10:00:00Z" }),
      ];
      expect(getMostActiveDay(entries)).toBe("Monday");
    });
  });

  describe("getFavoriteMoodCategory", () => {
    test('returns "No data" for empty array', () => {
      expect(getFavoriteMoodCategory([])).toBe("No data");
    });

    test('returns "Positive" when most moods are >= 7', () => {
      const entries = [
        makeEntry({ createdAt: "2025-01-01T00:00:00Z", userMood: 8 }),
        makeEntry({ createdAt: "2025-01-02T00:00:00Z", userMood: 7 }),
        makeEntry({ createdAt: "2025-01-03T00:00:00Z", userMood: 3 }),
      ];
      expect(getFavoriteMoodCategory(entries)).toBe("Positive");
    });

    test('returns "Neutral" when most moods are 4-6', () => {
      const entries = [
        makeEntry({ createdAt: "2025-01-01T00:00:00Z", userMood: 5 }),
        makeEntry({ createdAt: "2025-01-02T00:00:00Z", userMood: 4 }),
        makeEntry({ createdAt: "2025-01-03T00:00:00Z", userMood: 6 }),
        makeEntry({ createdAt: "2025-01-04T00:00:00Z", userMood: 1 }),
      ];
      expect(getFavoriteMoodCategory(entries)).toBe("Neutral");
    });

    test('returns "Negative" when most moods are < 4', () => {
      const entries = [
        makeEntry({ createdAt: "2025-01-01T00:00:00Z", userMood: 1 }),
        makeEntry({ createdAt: "2025-01-02T00:00:00Z", userMood: 2 }),
        makeEntry({ createdAt: "2025-01-03T00:00:00Z", userMood: 3 }),
        makeEntry({ createdAt: "2025-01-04T00:00:00Z", userMood: 7 }),
      ];
      expect(getFavoriteMoodCategory(entries)).toBe("Negative");
    });
  });

  describe("calculateTotalWords", () => {
    test("returns 0 for no journals", () => {
      expect(calculateTotalWords([])).toBe(0);
    });

    test("counts words across entries", () => {
      const entries = [
        makeEntry({
          createdAt: "2025-01-01T00:00:00Z",
          journalText: "Hello world",
        }),
        makeEntry({
          createdAt: "2025-01-02T00:00:00Z",
          journalText: "One two three four",
        }),
      ];
      expect(calculateTotalWords(entries)).toBe(6);
    });

    test("ignores extra whitespace", () => {
      const entries = [
        makeEntry({
          createdAt: "2025-01-01T00:00:00Z",
          journalText: "  spaced   out  ",
        }),
      ];
      expect(calculateTotalWords(entries)).toBe(2);
    });

    test("returns 0 for empty text", () => {
      const entries = [
        makeEntry({
          createdAt: "2025-01-01T00:00:00Z",
          journalText: "   ",
        }),
      ];
      expect(calculateTotalWords(entries)).toBe(0);
    });
  });

  describe("calculateCurrentStreak", () => {
    test("returns 0 for no journals", () => {
      expect(calculateCurrentStreak([])).toBe(0);
    });

    test("returns streak of 1 for entry today only", () => {
      const today = new Date().toISOString();
      const entries = [makeEntry({ createdAt: today })];
      expect(calculateCurrentStreak(entries)).toBe(1);
    });

    test("returns streak for consecutive days ending today", () => {
      const today = new Date().toISOString().split("T")[0];
      const entries = makeStreakEntries(5, today + "T12:00:00Z");
      expect(calculateCurrentStreak(entries)).toBe(5);
    });

    test("allows streak starting from yesterday", () => {
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
      const yesterdayStr = yesterday.toISOString().split("T")[0];
      const entries = makeStreakEntries(3, yesterdayStr + "T12:00:00Z");
      expect(calculateCurrentStreak(entries)).toBe(3);
    });

    test("returns 0 if last entry was 2+ days ago", () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
      const entries = [makeEntry({ createdAt: twoDaysAgo.toISOString() })];
      expect(calculateCurrentStreak(entries)).toBe(0);
    });

    test("handles multiple entries on the same day", () => {
      const today = new Date().toISOString().split("T")[0];
      const entries = [
        makeEntry({ journalId: "1", createdAt: today + "T08:00:00Z" }),
        makeEntry({ journalId: "2", createdAt: today + "T20:00:00Z" }),
      ];
      expect(calculateCurrentStreak(entries)).toBe(1);
    });
  });

  describe("calculateLongestStreak", () => {
    test("returns 0 for no journals", () => {
      expect(calculateLongestStreak([])).toBe(0);
    });

    test("returns 1 for a single entry", () => {
      const entries = [makeEntry({ createdAt: "2025-06-15T12:00:00Z" })];
      expect(calculateLongestStreak(entries)).toBe(1);
    });

    test("calculates longest streak from non-consecutive groups", () => {
      // Two streaks separated by a gap: Jun 1-3 (3 days) and Jun 10-14 (5 days).
      const entries = [
        makeEntry({ journalId: "1", createdAt: "2025-06-01T12:00:00Z" }),
        makeEntry({ journalId: "2", createdAt: "2025-06-02T12:00:00Z" }),
        makeEntry({ journalId: "3", createdAt: "2025-06-03T12:00:00Z" }),
        makeEntry({ journalId: "4", createdAt: "2025-06-10T12:00:00Z" }),
        makeEntry({ journalId: "5", createdAt: "2025-06-11T12:00:00Z" }),
        makeEntry({ journalId: "6", createdAt: "2025-06-12T12:00:00Z" }),
        makeEntry({ journalId: "7", createdAt: "2025-06-13T12:00:00Z" }),
        makeEntry({ journalId: "8", createdAt: "2025-06-14T12:00:00Z" }),
      ];
      expect(calculateLongestStreak(entries)).toBe(5);
    });

    test("deduplicates same-day entries", () => {
      const entries = [
        makeEntry({ journalId: "1", createdAt: "2025-06-01T08:00:00Z" }),
        makeEntry({ journalId: "2", createdAt: "2025-06-01T20:00:00Z" }),
        makeEntry({ journalId: "3", createdAt: "2025-06-02T12:00:00Z" }),
      ];
      expect(calculateLongestStreak(entries)).toBe(2);
    });
  });

  describe("calculateProfileStats", () => {
    test("returns default values for empty journals", () => {
      const stats = calculateProfileStats([]);
      expect(stats.totalEntries).toBe(0);
      expect(stats.thisMonth).toBe(0);
      expect(stats.thisWeek).toBe(0);
      expect(stats.averageMood).toBe(0);
      expect(stats.longestStreak).toBe(0);
      expect(stats.currentStreak).toBe(0);
      expect(stats.mostActiveDay).toBe("No data");
      expect(stats.firstEntryDate).toBeNull();
      expect(stats.favoriteModCategory).toBe("No data");
      expect(stats.totalWords).toBe(0);
    });

    test("computes all fields for a set of entries", () => {
      const today = new Date().toISOString().split("T")[0];
      const entries = [
        makeEntry({
          journalId: "1",
          createdAt: today + "T10:00:00Z",
          userMood: 7,
          journalText: "Hello world today",
        }),
        makeEntry({
          journalId: "2",
          createdAt: today + "T14:00:00Z",
          userMood: 5,
          journalText: "Another entry here",
        }),
      ];
      const stats = calculateProfileStats(entries);
      expect(stats.totalEntries).toBe(2);
      expect(stats.averageMood).toBe(6);
      expect(stats.totalWords).toBe(6);
      expect(stats.currentStreak).toBe(1);
      expect(stats.longestStreak).toBe(1);
    });

    test("rounds averageMood to one decimal place", () => {
      const entries = [
        makeEntry({
          journalId: "1",
          createdAt: "2025-01-01T00:00:00Z",
          userMood: 7,
        }),
        makeEntry({
          journalId: "2",
          createdAt: "2025-01-02T00:00:00Z",
          userMood: 5,
        }),
        makeEntry({
          journalId: "3",
          createdAt: "2025-01-03T00:00:00Z",
          userMood: 3,
        }),
      ];
      const stats = calculateProfileStats(entries);
      expect(stats.averageMood).toBe(5);
    });
  });
});
