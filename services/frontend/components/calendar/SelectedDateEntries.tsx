import Link from 'next/link';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { JournalEntryCard } from '@/components/journal/JournalEntryCard';

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

interface SelectedDateEntriesProps {
    selectedDate: Date;
    entries: JournalEntry[];
}

export function SelectedDateEntries({ selectedDate, entries }: SelectedDateEntriesProps) {
    const formattedDate = selectedDate.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
    });

    const isToday = selectedDate.toDateString() === new Date().toDateString();
    const isPastDate = selectedDate < new Date(new Date().setHours(0, 0, 0, 0));

    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-900">
                        {isToday ? 'Today' : formattedDate}
                    </h2>
                    {/* Only show Add Entry button for today */}
                    {entries.length === 0 && isToday && (
                        <Link href="/journal/create">
                            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm">
                                Add Entry
                            </button>
                        </Link>
                    )}
                </div>
                <p className="text-gray-600 text-sm">
                    {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
                </p>
            </CardHeader>

            <CardContent>
                {entries.length === 0 ? (
                    <div className="text-center py-8">
                        {isToday ? (
                            <>
                                <p className="text-gray-500 mb-4">No entries for today yet</p>
                                <Link href="/journal/create">
                                    <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                                        Create Todays Entry
                                    </button>
                                </Link>
                            </>
                        ) : isPastDate ? (
                            <div>
                                <p className="text-gray-500 mb-2">No entries for this date</p>
                                <p className="text-xs text-gray-400">Past entries cannot be added</p>
                            </div>
                        ) : (
                            <div>
                                <p className="text-gray-500 mb-2">No entries for this date</p>
                                <p className="text-xs text-gray-400">Future entries cannot be created</p>
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
                            <div className="pt-4 border-t border-gray-100">
                                <Link href="/journal/create" className="block">
                                    <button className="w-full text-blue-600 hover:text-blue-800 py-3 text-sm font-medium border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
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