import {
  toLocalDateString,
  groupJournalsByDate,
  generateCalendarDays,
} from "@/lib/utils/calendar";
import { JournalEntry } from "@/types/journal";

function makeEntry(overrides: Partial<JournalEntry> = {}): JournalEntry {
  return {
    journalId: "1",
    userId: "user1",
    journalText: "test entry",
    userMood: 5,
    createdAt: "2025-06-15T12:00:00Z",
    ...overrides,
  };
}

describe("calendar utils", () => {
  // ── toLocalDateString ─────────────────────────────────────────────────

  describe("toLocalDateString", () => {
    test("formats date as YYYY-MM-DD", () => {
      const date = new Date(2025, 5, 15); // June 15, 2025 (month is 0-indexed)
      expect(toLocalDateString(date)).toBe("2025-06-15");
    });

    test("pads single-digit month and day", () => {
      const date = new Date(2025, 0, 5); // Jan 5
      expect(toLocalDateString(date)).toBe("2025-01-05");
    });

    test("handles Dec 31", () => {
      const date = new Date(2025, 11, 31);
      expect(toLocalDateString(date)).toBe("2025-12-31");
    });

    test("handles Jan 1", () => {
      const date = new Date(2025, 0, 1);
      expect(toLocalDateString(date)).toBe("2025-01-01");
    });
  });

  // ── groupJournalsByDate ───────────────────────────────────────────────

  describe("groupJournalsByDate", () => {
    test("returns empty map for no journals", () => {
      const result = groupJournalsByDate([]);
      expect(result.size).toBe(0);
    });

    test("groups entries by date", () => {
      const entries = [
        makeEntry({ journalId: "1", createdAt: "2025-06-15T08:00:00Z" }),
        makeEntry({ journalId: "2", createdAt: "2025-06-15T20:00:00Z" }),
        makeEntry({ journalId: "3", createdAt: "2025-06-16T12:00:00Z" }),
      ];
      const grouped = groupJournalsByDate(entries);
      expect(grouped.size).toBe(2);
      expect(grouped.get("2025-06-15")).toHaveLength(2);
      expect(grouped.get("2025-06-16")).toHaveLength(1);
    });

    test("each entry is in the correct group", () => {
      const entries = [
        makeEntry({ journalId: "a", createdAt: "2025-06-15T12:00:00Z" }),
      ];
      const grouped = groupJournalsByDate(entries);
      const dayEntries = grouped.get("2025-06-15")!;
      expect(dayEntries[0].journalId).toBe("a");
    });
  });

  // ── generateCalendarDays ──────────────────────────────────────────────

  describe("generateCalendarDays", () => {
    test("always generates exactly 42 days (6 weeks)", () => {
      const month = new Date(2025, 5, 1); // June 2025
      const days = generateCalendarDays(month, new Map(), null, "2025-06-15");
      expect(days).toHaveLength(42);
    });

    test("marks current month days correctly", () => {
      // June 2025 starts on Sunday
      const month = new Date(2025, 5, 1);
      const days = generateCalendarDays(month, new Map(), null, "2025-06-15");

      // First day should be June 1 (Sunday) and be in current month
      const june1 = days.find((d) => d.dateString === "2025-06-01");
      expect(june1).toBeDefined();
      expect(june1!.isCurrentMonth).toBe(true);

      // June 30 should be in current month
      const june30 = days.find((d) => d.dateString === "2025-06-30");
      expect(june30).toBeDefined();
      expect(june30!.isCurrentMonth).toBe(true);

      // July 1 should not be in current month
      const july1 = days.find((d) => d.dateString === "2025-07-01");
      expect(july1).toBeDefined();
      expect(july1!.isCurrentMonth).toBe(false);
    });

    test("marks today correctly", () => {
      const month = new Date(2025, 5, 1);
      const days = generateCalendarDays(month, new Map(), null, "2025-06-15");

      const today = days.find((d) => d.dateString === "2025-06-15");
      expect(today).toBeDefined();
      expect(today!.isToday).toBe(true);

      const notToday = days.find((d) => d.dateString === "2025-06-14");
      expect(notToday!.isToday).toBe(false);
    });

    test("marks selected date correctly", () => {
      const month = new Date(2025, 5, 1);
      const selectedDate = new Date(2025, 5, 20);
      const days = generateCalendarDays(
        month,
        new Map(),
        selectedDate,
        "2025-06-15",
      );

      const selected = days.find((d) => d.dateString === "2025-06-20");
      expect(selected!.isSelected).toBe(true);

      const notSelected = days.find((d) => d.dateString === "2025-06-21");
      expect(notSelected!.isSelected).toBe(false);
    });

    test("populates entry data from journalsByDate", () => {
      const month = new Date(2025, 5, 1);
      const entry1 = makeEntry({ journalId: "1", userMood: 8 });
      const entry2 = makeEntry({ journalId: "2", userMood: 4 });

      const journalsByDate = new Map<string, JournalEntry[]>();
      journalsByDate.set("2025-06-15", [entry1, entry2]);

      const days = generateCalendarDays(
        month,
        journalsByDate,
        null,
        "2025-06-15",
      );

      const june15 = days.find((d) => d.dateString === "2025-06-15");
      expect(june15!.entryCount).toBe(2);
      expect(june15!.entries).toHaveLength(2);
      expect(june15!.avgMood).toBe(6); // (8+4)/2 = 6
    });

    test("days without entries have 0 entryCount and avgMood", () => {
      const month = new Date(2025, 5, 1);
      const days = generateCalendarDays(month, new Map(), null, "2025-06-15");

      const emptyDay = days.find((d) => d.dateString === "2025-06-10");
      expect(emptyDay!.entryCount).toBe(0);
      expect(emptyDay!.avgMood).toBe(0);
      expect(emptyDay!.entries).toHaveLength(0);
    });

    test("handles null selectedDate", () => {
      const month = new Date(2025, 5, 1);
      const days = generateCalendarDays(month, new Map(), null, "2025-06-15");

      // No day should be selected
      const anySelected = days.some((d) => d.isSelected);
      expect(anySelected).toBe(false);
    });
  });
});
