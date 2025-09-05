import { Card, CardContent } from '@/components/ui/Card';
import { MoodSelector } from './MoodSelector';
import { JournalTextEditor } from './JournalTextEditor';

interface CreateJournalFormProps {
    entry: string;
    setEntry: (entry: string) => void;
    mood: string;
    setMood: (mood: string) => void;
    onSubmit: (e: React.FormEvent) => void;
    isSubmitting: boolean;
    error: string | null;
}

export function CreateJournalForm({
    entry,
    setEntry,
    mood,
    setMood,
    onSubmit,
    isSubmitting,
    error
}: CreateJournalFormProps) {
    return (
        <Card>
            <CardContent className="p-6">
                <form onSubmit={onSubmit} className="space-y-6">
                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <p className="text-red-700 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Mood Selector */}
                    <MoodSelector selectedMood={mood} onMoodChange={setMood} />

                    {/* Journal Text Editor */}
                    <JournalTextEditor value={entry} onChange={setEntry} />

                    {/* Submit Buttons */}
                    <div className="flex gap-4 pt-4">
                        <button
                            type="submit"
                            disabled={isSubmitting || !entry.trim() || !mood}
                            className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
                        >
                            {isSubmitting ? 'Saving...' : 'Save Entry'}
                        </button>

                        <button
                            type="button"
                            onClick={() => {
                                setEntry('');
                                setMood('');
                            }}
                            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            Clear
                        </button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}