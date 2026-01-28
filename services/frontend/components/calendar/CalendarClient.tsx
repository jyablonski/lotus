"use client";

import { useState, useMemo } from "react";
import { CalendarHeader } from "@/components/calendar/CalendarHeader";
import { CalendarGrid } from "@/components/calendar/CalendarGrid";
import { SelectedDateEntries } from "@/components/calendar/SelectedDateEntries";
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

/**
 * Format date as YYYY-MM-DD in local timezone (not UTC)
 * This ensures entries created at 5pm PT show on today's date, not tomorrow
 */
function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

interface CalendarClientProps {
  journals: JournalEntry[];
  totalEntries: number;
  /** Server-provided current date string (YYYY-MM-DD) to avoid hydration mismatch */
  serverDate: string;
}

export function CalendarClient({
  journals,
  totalEntries,
  serverDate,
}: CalendarClientProps) {
  // Parse server-provided date to avoid hydration mismatch
  // Server sends a stable date string that both server and client can parse identically
  const initialDate = useMemo(() => {
    const [year, month, day] = serverDate.split("-").map(Number);
    return new Date(year, month - 1, day);
  }, [serverDate]);

  const [currentMonth, setCurrentMonth] = useState(() => {
    return new Date(initialDate.getFullYear(), initialDate.getMonth(), 1);
  });
  const [selectedDate, setSelectedDate] = useState<Date | null>(initialDate);

  // Group journals by date for efficient lookup
  const journalsByDate = useMemo(() => {
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
  }, [journals]);

  // Generate calendar days for the current month
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    // Get first day of month and calculate starting date (include previous month days)
    const firstDayOfMonth = new Date(year, month, 1);
    const startDate = new Date(firstDayOfMonth);
    startDate.setDate(startDate.getDate() - firstDayOfMonth.getDay());

    // Generate 42 days (6 weeks) to fill calendar grid
    const days: CalendarDay[] = [];
    // Use server-provided date for "today" to ensure consistency during hydration
    const todayString = serverDate;

    for (let i = 0; i < 42; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);

      const dateKey = toLocalDateString(date);
      const dayEntries = journalsByDate.get(dateKey) || [];

      // Calculate average mood for the day
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
  }, [currentMonth, journalsByDate, selectedDate, serverDate]);

  // Get entries for the selected date
  const selectedDateEntries = useMemo(() => {
    if (!selectedDate) return [];

    const dateKey = toLocalDateString(selectedDate);
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

  return (
    <div className="page-container">
      <div className="content-container">
        <CalendarHeader
          currentMonth={currentMonth}
          onNavigateMonth={navigateMonth}
          onGoToToday={goToToday}
          totalEntries={totalEntries}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar Grid */}
          <div className="lg:col-span-2">
            <CalendarGrid
              calendarDays={calendarDays}
              onDateSelect={setSelectedDate}
            />
          </div>

          {/* Selected Date Entries */}
          <div>
            {selectedDate && (
              <SelectedDateEntries
                selectedDate={selectedDate}
                entries={selectedDateEntries}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
