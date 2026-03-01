"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { JournalEntry } from "@/types/journal";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import { JournalEntryCard } from "@/components/journal/JournalEntryCard";

interface SelectedDateEntriesProps {
  selectedDate: Date;
  entries: JournalEntry[];
}

/**
 * Format date in a locale-independent way to avoid hydration mismatch
 */
function formatDateHeader(date: Date): string {
  const days = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const dayName = days[date.getUTCDay()];
  const monthName = months[date.getUTCMonth()];
  const day = date.getUTCDate();
  const year = date.getUTCFullYear();

  return `${dayName}, ${monthName} ${day}, ${year}`;
}

export function SelectedDateEntries({
  selectedDate,
  entries,
}: SelectedDateEntriesProps) {
  // Use state for "today" checks to avoid hydration mismatch
  // Initial render uses false (safe default), then updates after hydration
  const [isToday, setIsToday] = useState(false);
  const [isPastDate, setIsPastDate] = useState(false);

  useEffect(() => {
    const now = new Date();
    setIsToday(selectedDate.toDateString() === now.toDateString());
    setIsPastDate(selectedDate < new Date(now.setHours(0, 0, 0, 0)));
  }, [selectedDate]);

  const formattedDate = formatDateHeader(selectedDate);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-dark-50">
            {isToday ? "Today" : formattedDate}
          </h2>
          {/* Only show Add Entry button for today */}
          {entries.length === 0 && isToday && (
            <Link href="/journal/create">
              <button className="btn-primary px-4 py-2 text-sm">
                Add Entry
              </button>
            </Link>
          )}
        </div>
        <p className="text-dark-400 text-sm">
          {entries.length} {entries.length === 1 ? "entry" : "entries"}
        </p>
      </CardHeader>

      <CardContent>
        {entries.length === 0 ? (
          <div className="text-center py-8">
            {isToday ? (
              <>
                <p className="text-dark-400 mb-4">No entries for today yet</p>
                <Link href="/journal/create">
                  <button className="btn-primary px-4 py-2">
                    Create Todays Entry
                  </button>
                </Link>
              </>
            ) : isPastDate ? (
              <div>
                <p className="text-dark-400 mb-2">No entries for this date</p>
                <p className="text-xs text-dark-500">
                  Past entries cannot be created
                </p>
              </div>
            ) : (
              <div>
                <p className="text-dark-400 mb-2">No entries for this date</p>
                <p className="text-xs text-dark-500">
                  Future entries cannot be created
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <JournalEntryCard key={entry.journalId} entry={entry} />
            ))}

            {/* Show add another entry button only for today */}
            {isToday && (
              <div className="pt-4 border-t border-dark-600">
                <Link href="/journal/create" className="block">
                  <button className="w-full link-lotus py-3 text-sm font-medium border border-lotus-500/30 rounded-lg hover:bg-lotus-500/10 transition-colors">
                    Add Another Entry for Today
                  </button>
                </Link>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
