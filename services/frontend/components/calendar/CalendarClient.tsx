"use client";

import { useState, useMemo } from "react";
import { CalendarHeader } from "@/components/calendar/CalendarHeader";
import { CalendarGrid } from "@/components/calendar/CalendarGrid";
import { SelectedDateEntries } from "@/components/calendar/SelectedDateEntries";
import { JournalEntry } from "@/types/journal";
import {
  type CalendarDay,
  toLocalDateString,
  groupJournalsByDate,
  generateCalendarDays,
} from "@/lib/utils/calendar";

export type { CalendarDay };

interface CalendarClientProps {
  journals: JournalEntry[];
  totalEntries: number;
  /** Server-provided current date string (YYYY-MM-DD) to avoid hydration mismatch */
  serverDate: string;
  timezone: string;
}

export function CalendarClient({
  journals,
  totalEntries,
  serverDate,
  timezone,
}: CalendarClientProps) {
  const initialDate = useMemo(() => {
    const [year, month, day] = serverDate.split("-").map(Number);
    return new Date(year, month - 1, day);
  }, [serverDate]);

  const [currentMonth, setCurrentMonth] = useState(() => {
    return new Date(initialDate.getFullYear(), initialDate.getMonth(), 1);
  });
  const [selectedDate, setSelectedDate] = useState<Date | null>(initialDate);

  const journalsByDate = useMemo(
    () => groupJournalsByDate(journals, timezone),
    [journals, timezone],
  );

  const calendarDays = useMemo(
    () =>
      generateCalendarDays(
        currentMonth,
        journalsByDate,
        selectedDate,
        serverDate,
        timezone,
      ),
    [currentMonth, journalsByDate, selectedDate, serverDate, timezone],
  );

  const selectedDateEntries = useMemo(() => {
    if (!selectedDate) return [];
    const dateKey = toLocalDateString(selectedDate, timezone);
    return journalsByDate.get(dateKey) || [];
  }, [selectedDate, journalsByDate, timezone]);

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
          timezone={timezone}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <CalendarGrid
              calendarDays={calendarDays}
              onDateSelect={setSelectedDate}
            />
          </div>

          <div>
            {selectedDate && (
              <SelectedDateEntries
                selectedDate={selectedDate}
                entries={selectedDateEntries}
                timezone={timezone}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
