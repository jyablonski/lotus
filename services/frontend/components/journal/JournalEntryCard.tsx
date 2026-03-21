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
  /** When true, show topic tags (gated by frontend_show_tags). */
  showTags?: boolean;
  /** Similarity score from semantic search (admin-only). */
  similarityScore?: number;
}

export function JournalEntryCard({
  entry,
  timezone,
  showTags = false,
  similarityScore,
}: JournalEntryCardProps) {
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
          <div className="flex items-center gap-2">
            {similarityScore !== undefined && (
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-purple-600/20 text-purple-300 ring-1 ring-purple-500/30">
                {Math.round(similarityScore * 100)}% match
              </span>
            )}
            <span
              className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded-full ${moodConfig.color}`}
            >
              Mood {moodConfig.label}
            </span>
          </div>
        </div>

        <div className="prose prose-sm max-w-none">
          <p className="text-dark-200 whitespace-pre-wrap leading-relaxed">
            {displayText}
          </p>
        </div>

        {showTags && entry.topicNames && entry.topicNames.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2" aria-label="Topics">
            {[...new Set(entry.topicNames)].map((name) => (
              <span
                key={name}
                className="inline-flex items-center rounded-md bg-dark-700 px-2.5 py-1 text-xs font-medium text-dark-200 ring-1 ring-dark-600"
              >
                {name.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}

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
