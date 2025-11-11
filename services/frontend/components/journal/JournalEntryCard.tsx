import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { getMoodConfigByInt } from "@/utils/moodMapping";
import { JournalEntry } from "@/types/journal";

interface JournalEntryCardProps {
  entry: JournalEntry;
}

export function JournalEntryCard({ entry }: JournalEntryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formattedDate = new Date(entry.createdAt).toLocaleString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  });

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
