"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { getMoodConfigByInt } from "@/utils/moodMapping";
import { JournalEntry } from "@/types/journal";

interface JournalEntryCardProps {
  entry: JournalEntry;
}

/**
 * Format date/time in a locale-independent way to avoid hydration mismatch
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
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

  const dayName = days[date.getDay()];
  const monthName = months[date.getMonth()];
  const day = date.getDate();

  let hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12
  const minutesStr = minutes < 10 ? `0${minutes}` : minutes;

  return `${dayName}, ${monthName} ${day}, ${hours}:${minutesStr} ${ampm}`;
}

export function JournalEntryCard({ entry }: JournalEntryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formattedDate = formatDateTime(entry.createdAt);

  // userMood is already a number, no need to parseInt
  const moodConfig = getMoodConfigByInt(entry.userMood);

  const shouldTruncate = entry.journalText.length > 200;
  const displayText =
    shouldTruncate && !isExpanded
      ? entry.journalText.substring(0, 200) + "..."
      : entry.journalText;

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-sm text-gray-500">{formattedDate}</p>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full ${moodConfig.color}`}
          >
            <span className="text-sm leading-none">{moodConfig.emoji}</span>
            <span>{moodConfig.label}</span>
          </span>
        </div>

        <div className="prose prose-sm max-w-none">
          <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
            {displayText}
          </p>
        </div>

        {shouldTruncate && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
            >
              {isExpanded ? "Show less ↑" : "Read more →"}
            </button>
          </div>
        )}
      </div>
    </Card>
  );
}
