"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { getMoodConfigByInt } from "@/lib/utils/moodMapping";
import { JournalEntry } from "@/types/journal";
import { trackEvent } from "@/lib/analytics";
import { formatEntryDate } from "@/lib/utils/datetime";

interface JournalEntryCardProps {
  entry: JournalEntry;
  timezone: string;
}

export function JournalEntryCard({ entry, timezone }: JournalEntryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formattedDate = formatEntryDate(entry.createdAt, timezone);

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
            <p className="text-sm text-dark-400">{formattedDate}</p>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full ${moodConfig.color}`}
          >
            <span className="text-sm leading-none">{moodConfig.emoji}</span>
            <span>{moodConfig.label}</span>
          </span>
        </div>

        <div className="prose prose-sm max-w-none">
          <p className="text-dark-200 whitespace-pre-wrap leading-relaxed">
            {displayText}
          </p>
        </div>

        {shouldTruncate && (
          <div className="mt-4 pt-4 border-t border-dark-600">
            <button
              onClick={() => {
                const expanding = !isExpanded;
                setIsExpanded(expanding);

                // §3c: entry_viewed — fire when the user expands to read
                if (expanding) {
                  const createdDate = new Date(entry.createdAt);
                  const now = new Date();
                  const daysOld = Math.floor(
                    (now.getTime() - createdDate.getTime()) /
                      (1000 * 60 * 60 * 24),
                  );
                  trackEvent("entry_viewed", { days_old: daysOld });
                }
              }}
              className="link-lotus text-sm font-medium"
            >
              {isExpanded ? "Show less" : "Read more"}
            </button>
          </div>
        )}
      </div>
    </Card>
  );
}
