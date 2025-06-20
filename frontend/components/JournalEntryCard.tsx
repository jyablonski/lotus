type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string; // ISO string
};

interface JournalEntryCardProps {
    entry: JournalEntry;
}

export function JournalEntryCard({ entry }: JournalEntryCardProps) {
    // Format date like "Monday, June 11 12:04:00 PM UTC"
    const formattedDate = new Date(entry.createdAt).toLocaleString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: true,
        timeZone: 'UTC',
        timeZoneName: 'short',
    });

    return (
        <li className="border rounded-md shadow p-4 bg-white">
            <div className="flex justify-between items-center mb-2">
                <p className="text-sm text-gray-500">{formattedDate}</p>
                <span className="px-2 py-1 text-xs font-semibold rounded bg-indigo-100 text-indigo-700">
                    Mood: {entry.userMood}
                </span>
            </div>
            <p className="text-gray-800 whitespace-pre-wrap">{entry.journalText}</p>
        </li>
    );
}
