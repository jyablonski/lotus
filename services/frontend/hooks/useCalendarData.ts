import { useState, useMemo } from "react";
import { useJournalData } from "./useJournalData";
import { JournalEntry } from "@/types/journal";

export interface CalendarDay {
  date: Date;
  dateString: string;
  entries: JournalEntry[];
  isCurrentMonth: boolean;
  isToday: boolean;
  isSelected: boolean;
  entryCount: number;
  avgMood: number;
}

export function useCalendarData() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

  // Load ALL journals for calendar display
  // Calendar needs complete data to show entries for all dates
  const { journals, loading, error } = useJournalData({
    initialLimit: 1000, // Large number to get all entries
    autoLoad: true,
  });

  // Group journals by date for efficient lookup
  const journalsByDate = useMemo(() => {
    const grouped = new Map<string, JournalEntry[]>();

    journals.forEach((journal) => {
      const date = new Date(journal.createdAt);
      const dateKey = date.toISOString().split("T")[0]; // YYYY-MM-DD format

      if (!grouped.has(dateKey)) {
        grouped.set(dateKey, []);
      }
      grouped.get(dateKey)!.push(journal);
    });

    return grouped;
  }, [journals]);

  // Generate calendar days for the current month
  // Mood scores: excited=8, happy=7, content=6, neutral=5, tired=4, sad=3, anxious=2, angry=1
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    // Get first day of month and calculate starting date (include previous month days)
    const firstDayOfMonth = new Date(year, month, 1);
    const startDate = new Date(firstDayOfMonth);
    startDate.setDate(startDate.getDate() - firstDayOfMonth.getDay()); // Start from Sunday

    // Generate 42 days (6 weeks) to fill calendar grid
    const days: CalendarDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < 42; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);

      const dateKey = date.toISOString().split("T")[0];
      const dayEntries = journalsByDate.get(dateKey) || [];

      // Calculate average mood for the day
      // userMood is already a number, no need to parseInt
      const avgMood =
        dayEntries.length > 0
          ? dayEntries.reduce((sum, entry) => sum + entry.userMood, 0) /
            dayEntries.length
          : 0;

      const isSelected = selectedDate
        ? date.toDateString() === selectedDate.toDateString()
        : false;

      days.push({
        date: new Date(date),
        dateString: dateKey, // YYYY-MM-DD format
        entries: dayEntries,
        isCurrentMonth: date.getMonth() === month,
        isToday: date.toDateString() === today.toDateString(),
        isSelected,
        entryCount: dayEntries.length,
        avgMood: Math.round(avgMood * 10) / 10, // Round to 1 decimal
      });
    }

    return days;
  }, [currentMonth, journalsByDate, selectedDate]);

  // Get entries for the selected date
  const selectedDateEntries = useMemo(() => {
    if (!selectedDate) return [];

    const dateKey = selectedDate.toISOString().split("T")[0];
    return journalsByDate.get(dateKey) || [];
  }, [selectedDate, journalsByDate]);

  // Navigation functions
  const navigateMonth = (direction: "prev" | "next") => {
    setCurrentMonth((prev) => {
      const newMonth = new Date(prev);
      if (direction === "prev") {
        newMonth.setMonth(newMonth.getMonth() - 1);
      } else {
        newMonth.setMonth(newMonth.getMonth() + 1);
      }
      return newMonth;
    });
  };

  const goToToday = () => {
    const today = new Date();
    setCurrentMonth(new Date(today.getFullYear(), today.getMonth(), 1));
    setSelectedDate(today);
  };

  return {
    calendarDays,
    selectedDate,
    setSelectedDate,
    selectedDateEntries,
    currentMonth,
    navigateMonth,
    goToToday,
    loading,
    error,
    totalEntries: journals.length,
  };
}
