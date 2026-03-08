import { getMoodConfigByInt } from "@/lib/utils/moodMapping";
import type { CalendarDay } from "@/lib/utils/calendar";

interface CalendarGridProps {
  calendarDays: CalendarDay[];
  onDateSelect: (date: Date) => void;
}

export function CalendarGrid({
  calendarDays,
  onDateSelect,
}: CalendarGridProps) {
  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const getMoodIndicator = (avgMood: number, entryCount: number) => {
    if (entryCount === 0) return null;

    const moodConfig = getMoodConfigByInt(Math.round(avgMood));
    return {
      label: moodConfig.label,
      color:
        avgMood >= 7
          ? "bg-green-500/20"
          : avgMood >= 4
            ? "bg-yellow-500/20"
            : "bg-red-500/20",
    };
  };

  return (
    <div
      className="rounded-lg border border-dark-600 overflow-hidden"
      style={{ background: "rgba(30, 41, 59, 0.8)" }}
    >
      {/* Week day headers */}
      <div className="grid grid-cols-7 border-b border-dark-600">
        {weekDays.map((day) => (
          <div
            key={day}
            className="p-4 text-center text-sm font-medium text-dark-300 bg-dark-800/50"
          >
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
                relative p-4 h-24 border-r border-b border-dark-700/50 text-left hover:bg-dark-700/50 transition-colors
                ${!day.isCurrentMonth ? "text-dark-600 bg-dark-800/30" : ""}
                ${day.isToday ? "bg-lotus-500/10 border-lotus-500/30" : ""}
                ${day.isSelected ? "bg-lotus-500/20 border-lotus-500/40" : ""}
                ${index % 7 === 6 ? "border-r-0" : ""}
                ${index >= 35 ? "border-b-0" : ""}
              `}
            >
              {/* Date number */}
              <div
                className={`
                text-sm font-medium
                ${day.isToday ? "text-lotus-300" : day.isCurrentMonth ? "text-dark-200" : "text-dark-600"}
              `}
              >
                {day.date.getDate()}
              </div>

              {/* Entry indicators */}
              {day.entryCount > 0 && (
                <div className="mt-1 space-y-1">
                  {/* Entry count */}
                  <div className="text-xs text-dark-400">
                    {day.entryCount}{" "}
                    {day.entryCount === 1 ? "entry" : "entries"}
                  </div>

                  {/* Mood indicator (1-10 scale) */}
                  {moodIndicator && (
                    <div
                      className={`inline-block px-2 py-1 rounded-full text-xs ${moodIndicator.color}`}
                    >
                      {moodIndicator.label}
                    </div>
                  )}
                </div>
              )}

              {/* Today indicator */}
              {day.isToday && (
                <div className="absolute bottom-1 right-1">
                  <div className="w-2 h-2 bg-lotus-500 rounded-full"></div>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
