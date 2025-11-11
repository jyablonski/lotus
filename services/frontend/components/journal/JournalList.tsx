import { JournalEntry } from "@/types/journal";
import { JournalEntryCard } from "./JournalEntryCard";

interface JournalListProps {
  entries: JournalEntry[];
}

export function JournalList({ entries }: JournalListProps) {
  return (
    <div className="space-y-6">
      {entries.map((entry) => (
        <JournalEntryCard key={entry.journalId} entry={entry} />
      ))}
    </div>
  );
}
