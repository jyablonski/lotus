import { Card } from '@/components/ui/Card';
import { getMoodConfigByInt } from '@/utils/moodMapping';
import { JournalEntry } from '@/types/journal';

interface JournalEntryCardProps {
    entry: JournalEntry;
}

export function JournalEntryCard({ entry }: JournalEntryCardProps) {
    const formattedDate = new Date(entry.createdAt).toLocaleString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true,
    });

    // Convert the mood integer back to our mood config
    const moodInt = parseInt(entry.userMood);
    const moodConfig = getMoodConfigByInt(moodInt);

    const previewText = entry.journalText.length > 200
        ? entry.journalText.substring(0, 200) + '...'
        : entry.journalText;

    return (
        <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <p className="text-sm text-gray-500">{formattedDate}</p>
                        <p className="text-xs text-gray-400 mt-1">ID: {entry.journalId}</p>
                    </div>
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${moodConfig.color}`}>
                        {moodConfig.emoji} {moodConfig.label}
                    </span>
                </div>

                <div className="prose prose-sm max-w-none">
                    <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {previewText}
                    </p>
                </div>

                {entry.journalText.length > 200 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            Read more →
                        </button>
                    </div>
                )}
            </div>
        </Card>
    );
}
