import {
  calculateEntriesThisWeek,
  calculateStreak,
  calculateAverageMood,
  getSentimentFromMood,
  getSentimentFromMoodInt,
  generateTitle,
  formatAbsoluteDate,
  formatRelativeDate,
  formatRecentEntries,
} from "@/lib/utils/dashboard";
import { JournalEntry } from "@/types/journal";

function makeEntry(overrides: Partial<JournalEntry> = {}): JournalEntry {
  return {
    journalId: "1",
    userId: "user1",
    journalText: "Some journal text here",
    userMood: 5,
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

describe("dashboard utils", () => {
  // ── calculateEntriesThisWeek ──────────────────────────────────────────

  describe("calculateEntriesThisWeek", () => {
    test("returns 0 for no journals", () => {
      expect(calculateEntriesThisWeek([])).toBe(0);
    });

    test("counts only entries from the last 7 days", () => {
      const now = new Date();
      const recent = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
      const old = new Date("2020-01-01T00:00:00Z");
      const entries = [
        makeEntry({ journalId: "1", createdAt: recent.toISOString() }),
        makeEntry({ journalId: "2", createdAt: now.toISOString() }),
        makeEntry({ journalId: "3", createdAt: old.toISOString() }),
      ];
      expect(calculateEntriesThisWeek(entries)).toBe(2);
    });
  });

  // ── calculateStreak (delegates to profileStats.calculateCurrentStreak) ─

  describe("calculateStreak", () => {
    test("returns 0 for no journals", () => {
      expect(calculateStreak([])).toBe(0);
    });

    test("returns 1 for entry today", () => {
      const entries = [makeEntry({ createdAt: new Date().toISOString() })];
      expect(calculateStreak(entries)).toBe(1);
    });
  });

  // ── calculateAverageMood ──────────────────────────────────────────────

  describe("calculateAverageMood", () => {
    test("returns 0 when no recent entries", () => {
      const old = [
        makeEntry({ createdAt: "2020-01-01T00:00:00Z", userMood: 7 }),
      ];
      expect(calculateAverageMood(old, 7)).toBe(0);
    });

    test("calculates average for entries within the specified days", () => {
      const now = new Date();
      const entries = [
        makeEntry({
          journalId: "1",
          createdAt: now.toISOString(),
          userMood: 8,
        }),
        makeEntry({
          journalId: "2",
          createdAt: now.toISOString(),
          userMood: 4,
        }),
      ];
      expect(calculateAverageMood(entries, 7)).toBe(6);
    });

    test("defaults to 7 days window", () => {
      const now = new Date();
      const entries = [
        makeEntry({ createdAt: now.toISOString(), userMood: 6 }),
      ];
      expect(calculateAverageMood(entries)).toBe(6);
    });
  });

  // ── getSentimentFromMood ──────────────────────────────────────────────

  describe("getSentimentFromMood", () => {
    test('returns "Positive" for mood >= 7', () => {
      expect(getSentimentFromMood(7)).toBe("Positive");
      expect(getSentimentFromMood(8)).toBe("Positive");
    });

    test('returns "Neutral" for mood 4-6', () => {
      expect(getSentimentFromMood(4)).toBe("Neutral");
      expect(getSentimentFromMood(5)).toBe("Neutral");
      expect(getSentimentFromMood(6)).toBe("Neutral");
    });

    test('returns "Negative" for mood < 4', () => {
      expect(getSentimentFromMood(3)).toBe("Negative");
      expect(getSentimentFromMood(1)).toBe("Negative");
    });
  });

  // ── getSentimentFromMoodInt ───────────────────────────────────────────

  describe("getSentimentFromMoodInt", () => {
    test('returns "positive" for mood >= 7', () => {
      expect(getSentimentFromMoodInt(7)).toBe("positive");
      expect(getSentimentFromMoodInt(8)).toBe("positive");
    });

    test('returns "neutral" for mood 4-6', () => {
      expect(getSentimentFromMoodInt(4)).toBe("neutral");
      expect(getSentimentFromMoodInt(6)).toBe("neutral");
    });

    test('returns "negative" for mood < 4', () => {
      expect(getSentimentFromMoodInt(1)).toBe("negative");
      expect(getSentimentFromMoodInt(3)).toBe("negative");
    });

    test("boundary: 7 is positive, not neutral", () => {
      expect(getSentimentFromMoodInt(7)).toBe("positive");
    });

    test("boundary: 4 is neutral, not negative", () => {
      expect(getSentimentFromMoodInt(4)).toBe("neutral");
    });
  });

  // ── generateTitle ─────────────────────────────────────────────────────

  describe("generateTitle", () => {
    test("returns full text if 4 words or fewer", () => {
      expect(generateTitle("Hello world")).toBe("Hello world");
      expect(generateTitle("One two three four")).toBe("One two three four");
    });

    test('truncates to 4 words with "..." for longer text', () => {
      expect(generateTitle("One two three four five")).toBe(
        "One two three four...",
      );
    });

    test("handles single word", () => {
      expect(generateTitle("Hello")).toBe("Hello");
    });

    test("trims leading/trailing whitespace", () => {
      expect(generateTitle("  Hello world  ")).toBe("Hello world");
    });
  });

  // ── formatAbsoluteDate ────────────────────────────────────────────────

  describe("formatAbsoluteDate", () => {
    test("returns YYYY-MM-DD format", () => {
      expect(formatAbsoluteDate("2025-06-15T14:30:00Z")).toBe("2025-06-15");
    });

    test("handles different timestamps on the same day", () => {
      expect(formatAbsoluteDate("2025-01-01T00:00:00Z")).toBe("2025-01-01");
      expect(formatAbsoluteDate("2025-01-01T23:59:59Z")).toBe("2025-01-01");
    });
  });

  // ── formatRelativeDate ────────────────────────────────────────────────

  describe("formatRelativeDate", () => {
    test('returns "Just now" for very recent dates', () => {
      const now = new Date();
      expect(formatRelativeDate(now.toISOString())).toBe("Just now");
    });

    test('returns "X hours ago" for dates within 24 hours', () => {
      const threeHoursAgo = new Date(
        Date.now() - 3 * 60 * 60 * 1000,
      ).toISOString();
      expect(formatRelativeDate(threeHoursAgo)).toBe("3 hours ago");
    });

    test('returns "1 day ago" for dates 24-48 hours old', () => {
      const oneDayAgo = new Date(
        Date.now() - 30 * 60 * 60 * 1000,
      ).toISOString();
      expect(formatRelativeDate(oneDayAgo)).toBe("1 day ago");
    });

    test('returns "X days ago" for dates within a week', () => {
      const fourDaysAgo = new Date(
        Date.now() - 4 * 24 * 60 * 60 * 1000,
      ).toISOString();
      expect(formatRelativeDate(fourDaysAgo)).toBe("4 days ago");
    });

    test("returns locale date string for dates older than a week", () => {
      const old = "2020-01-15T12:00:00Z";
      const result = formatRelativeDate(old);
      // Should not be "X days ago" — should be a full date
      expect(result).not.toContain("days ago");
      expect(result).not.toBe("Just now");
    });
  });

  // ── formatRecentEntries ───────────────────────────────────────────────

  describe("formatRecentEntries", () => {
    test("returns empty array for no journals", () => {
      expect(formatRecentEntries([])).toHaveLength(0);
    });

    test("limits to specified count", () => {
      const entries = [
        makeEntry({ journalId: "1" }),
        makeEntry({ journalId: "2" }),
        makeEntry({ journalId: "3" }),
        makeEntry({ journalId: "4" }),
      ];
      expect(formatRecentEntries(entries, 2)).toHaveLength(2);
    });

    test("defaults to 3 entries", () => {
      const entries = [
        makeEntry({ journalId: "1" }),
        makeEntry({ journalId: "2" }),
        makeEntry({ journalId: "3" }),
        makeEntry({ journalId: "4" }),
        makeEntry({ journalId: "5" }),
      ];
      expect(formatRecentEntries(entries)).toHaveLength(3);
    });

    test("formats each entry with correct fields", () => {
      const entries = [
        makeEntry({
          journalId: "42",
          journalText: "One two three four five",
          createdAt: "2025-06-15T12:00:00Z",
          userMood: 7,
        }),
      ];
      const [result] = formatRecentEntries(entries, 1);
      expect(result.id).toBe(42);
      expect(result.title).toBe("One two three four...");
      expect(result.date).toBe("2025-06-15T12:00:00Z");
      expect(result.preview).toBe("One two three four five");
      expect(result.sentiment).toBe("positive");
    });

    test("assigns correct sentiment per mood", () => {
      const entries = [
        makeEntry({ journalId: "1", userMood: 8 }), // positive
        makeEntry({ journalId: "2", userMood: 5 }), // neutral
        makeEntry({ journalId: "3", userMood: 2 }), // negative
      ];
      const results = formatRecentEntries(entries, 3);
      expect(results[0].sentiment).toBe("positive");
      expect(results[1].sentiment).toBe("neutral");
      expect(results[2].sentiment).toBe("negative");
    });
  });
});
