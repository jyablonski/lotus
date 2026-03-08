import {
  filterJournalsBySearch,
  filterJournalsByMood,
  filterJournalsByTag,
  filterJournals,
  getUniqueMoodsFromJournals,
  getUniqueTagsFromJournals,
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

    test("filters by mood number (1-10 scale)", () => {
      const result = filterJournalsByMood(sampleEntries, "7");
      expect(result).toHaveLength(1);
      expect(result[0].userMood).toBe(7);
    });

    test("returns empty when mood has no entries", () => {
      expect(filterJournalsByMood(sampleEntries, "2")).toHaveLength(0);
    });

    test("filters mood 8", () => {
      const result = filterJournalsByMood(sampleEntries, "8");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("3");
    });

    test("filters mood 1", () => {
      const result = filterJournalsByMood(sampleEntries, "1");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("4");
    });
  });

  // ── filterJournalsByTag ───────────────────────────────────────────────

  describe("filterJournalsByTag", () => {
    const entriesWithTags: JournalEntry[] = [
      makeEntry({
        journalId: "1",
        journalText: "a",
        userMood: 5,
        topicNames: ["work", "goals"],
      }),
      makeEntry({
        journalId: "2",
        journalText: "b",
        userMood: 5,
        topicNames: ["work"],
      }),
      makeEntry({
        journalId: "3",
        journalText: "c",
        userMood: 5,
        topicNames: ["goals"],
      }),
      makeEntry({ journalId: "4", journalText: "d", userMood: 5 }),
    ];

    test('returns all journals when selectedTag is "all"', () => {
      expect(filterJournalsByTag(entriesWithTags, "all")).toHaveLength(4);
    });

    test("filters by topic name", () => {
      const result = filterJournalsByTag(entriesWithTags, "work");
      expect(result).toHaveLength(2);
      expect(result.map((e) => e.journalId)).toEqual(["1", "2"]);
    });

    test("returns empty when no entry has the tag", () => {
      expect(filterJournalsByTag(entriesWithTags, "unknown")).toHaveLength(0);
    });

    test("excludes entries with no topicNames", () => {
      const result = filterJournalsByTag(entriesWithTags, "goals");
      expect(result).toHaveLength(2);
      expect(result[0].journalId).toBe("1");
      expect(result[1].journalId).toBe("3");
    });
  });

  // ── filterJournals (combined) ─────────────────────────────────────────

  describe("filterJournals", () => {
    test("applies both search and mood filters", () => {
      // Search for "day" (matches entries 1 and 5) + mood 7 (entry 1)
      const result = filterJournals(sampleEntries, "day", "7");
      expect(result).toHaveLength(1);
      expect(result[0].journalId).toBe("1");
    });

    test("returns all when both filters are permissive", () => {
      expect(filterJournals(sampleEntries, "", "all")).toHaveLength(5);
    });

    test("returns empty when filters are incompatible", () => {
      // Search for "excited" (entry 3, mood 8) but filter mood to 1
      expect(filterJournals(sampleEntries, "excited", "1")).toHaveLength(0);
    });

    test("applies tag filter when selectedTag provided", () => {
      const withTags = [
        makeEntry({
          journalId: "1",
          journalText: "a",
          userMood: 5,
          topicNames: ["focus"],
        }),
        makeEntry({
          journalId: "2",
          journalText: "b",
          userMood: 5,
          topicNames: ["focus", "goals"],
        }),
      ];
      expect(filterJournals(withTags, "", "all", "all")).toHaveLength(2);
      expect(filterJournals(withTags, "", "all", "focus")).toHaveLength(2);
      expect(filterJournals(withTags, "", "all", "goals")).toHaveLength(1);
      expect(filterJournals(withTags, "", "all", "goals")[0].journalId).toBe(
        "2",
      );
    });
  });

  // ── getUniqueTagsFromJournals ─────────────────────────────────────────

  describe("getUniqueTagsFromJournals", () => {
    test("returns empty array when no journals have topics", () => {
      expect(getUniqueTagsFromJournals(sampleEntries)).toHaveLength(0);
    });

    test("returns unique tags sorted alphabetically", () => {
      const entries = [
        makeEntry({
          journalId: "1",
          journalText: "a",
          userMood: 5,
          topicNames: ["work", "goals"],
        }),
        makeEntry({
          journalId: "2",
          journalText: "b",
          userMood: 5,
          topicNames: ["work"],
        }),
      ];
      expect(getUniqueTagsFromJournals(entries)).toEqual(["goals", "work"]);
    });

    test("deduplicates tags across entries", () => {
      const entries = [
        makeEntry({
          journalId: "1",
          journalText: "a",
          userMood: 5,
          topicNames: ["focus"],
        }),
        makeEntry({
          journalId: "2",
          journalText: "b",
          userMood: 5,
          topicNames: ["focus"],
        }),
      ];
      expect(getUniqueTagsFromJournals(entries)).toEqual(["focus"]);
    });
  });

  // ── getUniqueMoodsFromJournals ────────────────────────────────────────

  describe("getUniqueMoodsFromJournals", () => {
    test("returns empty array for no journals", () => {
      expect(getUniqueMoodsFromJournals([])).toHaveLength(0);
    });

    test("extracts unique moods sorted by number (1-10 scale)", () => {
      const moods = getUniqueMoodsFromJournals(sampleEntries);
      // Moods present: 1, 4, 5, 7, 8
      expect(moods).toHaveLength(5);
      expect(moods[0]).toEqual({ key: "1", label: "1" });
      expect(moods[4]).toEqual({ key: "8", label: "8" });
    });

    test("each mood has key and label as string number", () => {
      const moods = getUniqueMoodsFromJournals([
        makeEntry({ journalText: "test", userMood: 7 }),
      ]);
      expect(moods).toHaveLength(1);
      expect(moods[0]).toEqual({ key: "7", label: "7" });
    });

    test("deduplicates same mood values", () => {
      const entries = [
        makeEntry({ journalId: "1", journalText: "a", userMood: 5 }),
        makeEntry({ journalId: "2", journalText: "b", userMood: 5 }),
        makeEntry({ journalId: "3", journalText: "c", userMood: 5 }),
      ];
      expect(getUniqueMoodsFromJournals(entries)).toHaveLength(1);
      expect(getUniqueMoodsFromJournals(entries)[0]).toEqual({
        key: "5",
        label: "5",
      });
    });
  });
});
