import { buildMoodDailySeries } from "@/lib/utils/moodSeries";
import type { JournalEntry } from "@/types/journal";

describe("buildMoodDailySeries", () => {
  const base: JournalEntry = {
    journalId: "1",
    userId: "u",
    journalText: "x",
    userMood: 6,
    createdAt: new Date().toISOString(),
  };

  it("returns empty when no journals", () => {
    expect(buildMoodDailySeries([], "UTC", 30)).toEqual([]);
  });

  it("averages multiple entries on the same day", () => {
    const d = new Date();
    const j1: JournalEntry = {
      ...base,
      userMood: 4,
      createdAt: d.toISOString(),
    };
    const j2: JournalEntry = {
      ...base,
      journalId: "2",
      userMood: 8,
      createdAt: d.toISOString(),
    };
    const points = buildMoodDailySeries([j1, j2], "UTC", 30);
    expect(points.length).toBe(1);
    expect(points[0]?.avgMood).toBe(6);
  });
});
