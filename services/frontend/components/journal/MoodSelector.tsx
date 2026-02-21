import { getAllMoodOptions } from "@/lib/utils/moodMapping";

interface MoodSelectorProps {
  selectedMood: string;
  onMoodChange: (mood: string) => void;
}

export function MoodSelector({
  selectedMood,
  onMoodChange,
}: MoodSelectorProps) {
  const moods = getAllMoodOptions();

  return (
    <div>
      <label className="block text-sm font-medium text-dark-200 mb-3">
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
              ${
                selectedMood === mood.key
                  ? `${mood.color} border-opacity-100 shadow-md scale-105`
                  : "bg-dark-800/50 border-dark-600 hover:bg-dark-700/50 text-dark-200"
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
