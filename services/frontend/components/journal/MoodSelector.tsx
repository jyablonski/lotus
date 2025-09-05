import { getAllMoodOptions } from '@/utils/moodMapping';

interface MoodSelectorProps {
    selectedMood: string;
    onMoodChange: (mood: string) => void;
}

export function MoodSelector({ selectedMood, onMoodChange }: MoodSelectorProps) {
    const moods = getAllMoodOptions();

    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
                How are you feeling?
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {moods.map((mood) => (
                    <button
                        key={mood.key}
                        type="button"
                        onClick={() => onMoodChange(mood.key)}
                        className={`
              p-3 rounded-lg border-2 transition-all duration-200 text-center
              ${selectedMood === mood.key
                                ? `${mood.color} border-opacity-100 shadow-md scale-105`
                                : 'bg-white border-gray-200 hover:bg-gray-50'
                            }
            `}
                    >
                        <div className="text-2xl mb-1">{mood.emoji}</div>
                        <div className="text-xs font-medium">{mood.label}</div>
                    </button>
                ))}
            </div>
        </div>
    );
}