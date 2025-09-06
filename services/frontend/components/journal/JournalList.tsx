import { JournalEntryCard } from './JournalEntryCard';

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

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