import {
  filterJournalsBySearch,
  filterJournalsByMood,
  filterJournals,
  getUniqueMoodsFromJournals,
} from "@/lib/utils/journalFilters";
import { JournalEntry } from "@/types/journal";

function makeEntry(
  overrides: Partial<JournalEntry> &
    Pick<JournalEntry, "journalText" | "userMood">,
): JournalEntry {
  return {
    journalId: "1",
    userId: "user1",
    createdAt: "2025-06-15T12:00:00Z",
    ...overrides,
  };
}

const sampleEntries: JournalEntry[] = [
  makeEntry({
    journalId: "1",
    journalText: "Had a great day at the park",
    userMood: 7,
  }),
  makeEntry({
    journalId: "2",
    journalText: "Feeling tired and gloomy",
    userMood: 4,
  }),
  makeEntry({
    journalId: "3",
    journalText: "Excited about the new project",
    userMood: 8,
  }),
  makeEntry({
    journalId: "4",
    journalText: "Angry about the traffic",
    userMood: 1,
  }),
  makeEntry({
    journalId: "5",
    journalText: "A neutral kind of day",
    userMood: 5,
  }),
];

describe("journalFilters", () => {
  // ── filterJournalsBySearch ────────────────────────────────────────────

  describe("filterJournalsBySearch", () => {
    test("returns all journals when search term is empty", () => {
      expect(filterJournalsBySearch(sampleEntries, "")).toHaveLength(5);
    });

    test("returns all journals when search term is whitespace", () => {
      expect(filterJournalsBySearch(sampleEntries, "   ")).toHaveLength(5);
    });

    test("filters by case-insensitive substring", () => {
      const result = filterJournalsBySearch(sampleEntries, "excited");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("3");
    });

    test("matches partial words", () => {
      const result = filterJournalsBySearch(sampleEntries, "day");
      // "great day at the park" and "neutral kind of day"
      expect(result).toHaveLength(2);
    });

    test("returns empty array when nothing matches", () => {
      expect(filterJournalsBySearch(sampleEntries, "zzzzz")).toHaveLength(0);
    });
  });

  // ── filterJournalsByMood ──────────────────────────────────────────────

  describe("filterJournalsByMood", () => {
    test('returns all journals when selectedMood is "all"', () => {
      expect(filterJournalsByMood(sampleEntries, "all")).toHaveLength(5);
    });

    test("filters by mood key", () => {
      // happy = value 7
      const result = filterJournalsByMood(sampleEntries, "happy");
      expect(result).toHaveLength(1);
      expect(result[0].userMood).toBe(7);
    });

    test("returns empty when mood has no entries", () => {
      // anxious = value 2, not present
      expect(filterJournalsByMood(sampleEntries, "anxious")).toHaveLength(0);
    });

    test("filters excited (value 8)", () => {
      const result = filterJournalsByMood(sampleEntries, "excited");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("3");
    });

    test("filters angry (value 1)", () => {
      const result = filterJournalsByMood(sampleEntries, "angry");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("4");
    });
  });

  // ── filterJournals (combined) ─────────────────────────────────────────

  describe("filterJournals", () => {
    test("applies both search and mood filters", () => {
      // Search for "day" (matches entries 1 and 5) + mood "happy" (value 7, entry 1)
      const result = filterJournals(sampleEntries, "day", "happy");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("1");
    });

    test("returns all when both filters are permissive", () => {
      expect(filterJournals(sampleEntries, "", "all")).toHaveLength(5);
    });

    test("returns empty when filters are incompatible", () => {
      // Search for "excited" (entry 3, mood 8) but filter mood to "angry" (value 1)
      expect(filterJournals(sampleEntries, "excited", "angry")).toHaveLength(0);
    });
  });

  // ── getUniqueMoodsFromJournals ────────────────────────────────────────

  describe("getUniqueMoodsFromJournals", () => {
    test("returns empty array for no journals", () => {
      expect(getUniqueMoodsFromJournals([])).toHaveLength(0);
    });

    test("extracts unique moods sorted alphabetically", () => {
      const moods = getUniqueMoodsFromJournals(sampleEntries);
      // Moods present: happy(7), tired(4), excited(8), angry(1), neutral(5)
      // Alphabetical: Angry, Excited, Happy, Neutral, Tired
      expect(moods).toHaveLength(5);
      expect(moods[0].label).toBe("Angry");
      expect(moods[4].label).toBe("Tired");
    });

    test("each mood has key, label, and emoji", () => {
      const moods = getUniqueMoodsFromJournals([
        makeEntry({ journalText: "test", userMood: 7 }),
      ]);
      expect(moods).toHaveLength(1);
      expect(moods[0]).toEqual({
        key: "happy",
        label: "Happy",
        emoji: "😊",
      });
    });

    test("deduplicates same mood values", () => {
      const entries = [
        makeEntry({ journalId: "1", journalText: "a", userMood: 5 }),
        makeEntry({ journalId: "2", journalText: "b", userMood: 5 }),
        makeEntry({ journalId: "3", journalText: "c", userMood: 5 }),
      ];
      expect(getUniqueMoodsFromJournals(entries)).toHaveLength(1);
    });
  });
});
