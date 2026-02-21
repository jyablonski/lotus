import { JournalEntry } from "@/types/journal";

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
 * Format date as YYYY-MM-DD in local timezone (not UTC).
 * This ensures entries created at e.g. 5pm PT show on today's date, not tomorrow.
 */
export function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Group journals by local date for efficient lookup.
 */
export function groupJournalsByDate(
  journals: JournalEntry[],
): Map<string, JournalEntry[]> {
  const grouped = new Map<string, JournalEntry[]>();

  journals.forEach((journal) => {
    const date = new Date(journal.createdAt);
    const dateKey = toLocalDateString(date);

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

    const dateKey = toLocalDateString(date);
    const dayEntries = journalsByDate.get(dateKey) || [];

    const avgMood =
      dayEntries.length > 0
        ? dayEntries.reduce((sum, entry) => sum + entry.userMood, 0) /
          dayEntries.length
        : 0;

    const isSelected = selectedDate
      ? toLocalDateString(date) === toLocalDateString(selectedDate)
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
