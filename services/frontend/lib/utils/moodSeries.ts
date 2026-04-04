import type { JournalEntry } from "@/types/journal";
import { toTimezoneDateString } from "@/lib/utils/datetime";

export type MoodDailyPoint = {
  /** YYYY-MM-DD in user timezone */
  dateKey: string;
  /** Short label for chart axis */
  label: string;
  /** Average mood for that calendar day (1–10) */
  avgMood: number;
};

function addDays(d: Date, delta: number): Date {
  const next = new Date(d);
  next.setDate(next.getDate() + delta);
  return next;
}

/**
 * One point per calendar day in the window where the user wrote at least one entry.
 * Mood is averaged when multiple entries fall on the same day.
 */
export function buildMoodDailySeries(
  journals: JournalEntry[],
  timezone: string,
  days: 30 | 60 | 90,
): MoodDailyPoint[] {
  if (!journals.length) {
    return [];
  }

  const end = new Date();
  const start = addDays(end, -(days - 1));
  const startKey = toTimezoneDateString(start, timezone);
  const endKey = toTimezoneDateString(end, timezone);

  const byDay = new Map<string, { sum: number; count: number }>();
  for (const j of journals) {
    const key = toTimezoneDateString(new Date(j.createdAt), timezone);
    if (key < startKey || key > endKey) {
      continue;
    }
    const cur = byDay.get(key) ?? { sum: 0, count: 0 };
    cur.sum += j.userMood;
    cur.count += 1;
    byDay.set(key, cur);
  }

  const sortedKeys = [...byDay.keys()].sort();
  return sortedKeys.map((key) => {
    const agg = byDay.get(key)!;
    const parts = key.split("-");
    const m = parseInt(parts[1]!, 10);
    const d = parseInt(parts[2]!, 10);
    return {
      dateKey: key,
      label: `${m}/${d}`,
      avgMood: Math.round((agg.sum / agg.count) * 10) / 10,
    };
  });
}
