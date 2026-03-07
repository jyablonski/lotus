import { JournalEntry } from "@/types/journal";
import { JournalEntryCard } from "./JournalEntryCard";

interface JournalListProps {
  entries: JournalEntry[];
  timezone: string;
}

export function JournalList({ entries, timezone }: JournalListProps) {
  return (
    <div className="space-y-6">
      {entries.map((entry) => (
        <JournalEntryCard
          key={entry.journalId}
          entry={entry}
          timezone={timezone}
        />
      ))}
    </div>
  );
}
