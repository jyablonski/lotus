import { JournalEntry } from "@/types/journal";
import { toTimezoneDateString } from "@/lib/utils/datetime";

export type CalendarDay = {
  date: Date;
  dateString: string;
  entries: JournalEntry[];
  isCurrentMonth: boolean;
  isToday: boolean;
  isSelected: boolean;
  entryCount: number;
  avgMood: number;
};

/**
 * Format date as YYYY-MM-DD in the given timezone.
 * This ensures entries created at e.g. 5pm PT show on today's date, not tomorrow.
 */
export function toLocalDateString(
  date: Date,
  timezone: string = "UTC",
): string {
  return toTimezoneDateString(date, timezone);
}

/**
 * Group journals by local date for efficient lookup.
 */
export function groupJournalsByDate(
  journals: JournalEntry[],
  timezone: string = "UTC",
): Map<string, JournalEntry[]> {
  const grouped = new Map<string, JournalEntry[]>();

  journals.forEach((journal) => {
    const date = new Date(journal.createdAt);
    const dateKey = toLocalDateString(date, timezone);

    if (!grouped.has(dateKey)) {
      grouped.set(dateKey, []);
    }
    grouped.get(dateKey)!.push(journal);
  });

  return grouped;
}

/**
 * Generate 42 calendar days (6 weeks) for a given month.
 */
export function generateCalendarDays(
  currentMonth: Date,
  journalsByDate: Map<string, JournalEntry[]>,
  selectedDate: Date | null,
  todayString: string,
  timezone: string = "UTC",
): CalendarDay[] {
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const startDate = new Date(firstDayOfMonth);
  startDate.setDate(startDate.getDate() - firstDayOfMonth.getDay());

  const days: CalendarDay[] = [];

  for (let i = 0; i < 42; i++) {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);

    const dateKey = toLocalDateString(date, timezone);
    const dayEntries = journalsByDate.get(dateKey) || [];

    const avgMood =
      dayEntries.length > 0
        ? dayEntries.reduce((sum, entry) => sum + entry.userMood, 0) /
          dayEntries.length
        : 0;

    const isSelected = selectedDate
      ? toLocalDateString(date, timezone) ===
        toLocalDateString(selectedDate, timezone)
      : false;

    days.push({
      date: new Date(date),
      dateString: dateKey,
      entries: dayEntries,
      isCurrentMonth: date.getMonth() === month,
      isToday: dateKey === todayString,
      isSelected,
      entryCount: dayEntries.length,
      avgMood: Math.round(avgMood * 10) / 10,
    });
  }

  return days;
}
