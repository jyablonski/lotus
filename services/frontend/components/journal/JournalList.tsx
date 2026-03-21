import { JournalEntry } from "@/types/journal";
import { JournalEntryCard } from "./JournalEntryCard";

interface JournalListProps {
  entries: JournalEntry[];
  timezone: string;
  showTags?: boolean;
  /** Map of journalId → similarity score (admin-only, from semantic search). */
  similarityScores?: Map<string, number>;
}

export function JournalList({
  entries,
  timezone,
  showTags = false,
  similarityScores,
}: JournalListProps) {
  return (
    <div className="space-y-6">
      {entries.map((entry) => (
        <JournalEntryCard
          key={entry.journalId}
          entry={entry}
          timezone={timezone}
          showTags={showTags}
          similarityScore={similarityScores?.get(entry.journalId)}
        />
      ))}
    </div>
  );
}
