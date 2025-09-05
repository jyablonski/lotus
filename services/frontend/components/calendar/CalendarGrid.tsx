import { getMoodConfigByInt } from '@/utils/moodMapping';
import { JournalEntry } from '@/types/journal';

type CalendarDay = {
    date: Date;
    dateString: string;
    entries: JournalEntry[];
    isCurrentMonth: boolean;
    isToday: boolean;
    isSelected: boolean;
    entryCount: number;
    avgMood: number;
};

interface CalendarGridProps {
    calendarDays: CalendarDay[];
    onDateSelect: (date: Date) => void;
}

export function CalendarGrid({ calendarDays, onDateSelect }: CalendarGridProps) {
    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const getMoodIndicator = (avgMood: number, entryCount: number) => {
        if (entryCount === 0) return null;

        const moodConfig = getMoodConfigByInt(Math.round(avgMood));
        return {
            emoji: moodConfig.emoji,
            color: avgMood >= 7 ? 'bg-green-200' : avgMood >= 4 ? 'bg-yellow-200' : 'bg-red-200'
        };
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* Week day headers */}
            <div className="grid grid-cols-7 border-b border-gray-200">
                {weekDays.map((day) => (
                    <div key={day} className="p-4 text-center text-sm font-medium text-gray-700 bg-gray-50">
                        {day}
                    </div>
                ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7">
                {calendarDays.map((day, index) => {
                    const moodIndicator = getMoodIndicator(day.avgMood, day.entryCount);

                    return (
                        <button
                            key={day.dateString}
                            onClick={() => onDateSelect(day.date)}
                            className={`
                relative p-4 h-24 border-r border-b border-gray-100 text-left hover:bg-gray-50 transition-colors
                ${!day.isCurrentMonth ? 'text-gray-300 bg-gray-50' : ''}
                ${day.isToday ? 'bg-blue-50 border-blue-200' : ''}
                ${day.isSelected ? 'bg-blue-100 border-blue-300' : ''}
                ${index % 7 === 6 ? 'border-r-0' : ''}
                ${index >= 35 ? 'border-b-0' : ''}
              `}
                        >
                            {/* Date number */}
                            <div className={`
                text-sm font-medium
                ${day.isToday ? 'text-blue-900' : day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
              `}>
                                {day.date.getDate()}
                            </div>

                            {/* Entry indicators */}
                            {day.entryCount > 0 && (
                                <div className="mt-1 space-y-1">
                                    {/* Entry count */}
                                    <div className="text-xs text-gray-600">
                                        {day.entryCount} {day.entryCount === 1 ? 'entry' : 'entries'}
                                    </div>

                                    {/* Mood indicator */}
                                    {moodIndicator && (
                                        <div className={`inline-block px-2 py-1 rounded-full text-xs ${moodIndicator.color}`}>
                                            {moodIndicator.emoji}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Today indicator */}
                            {day.isToday && (
                                <div className="absolute bottom-1 right-1">
                                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                                </div>
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}