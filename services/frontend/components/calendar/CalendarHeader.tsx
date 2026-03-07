import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
import { formatMonthYear } from "@/lib/utils/datetime";

interface CalendarHeaderProps {
  currentMonth: Date;
  onNavigateMonth: (direction: "prev" | "next") => void;
  onGoToToday: () => void;
  totalEntries?: number;
  timezone: string;
}

export function CalendarHeader({
  currentMonth,
  onNavigateMonth,
  onGoToToday,
  totalEntries,
  timezone,
}: CalendarHeaderProps) {
  const monthYear = formatMonthYear(currentMonth, timezone);

  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50">Journal Calendar</h1>
        <p className="text-dark-400 mt-1">
          {totalEntries !== undefined
            ? `View your ${totalEntries} ${totalEntries === 1 ? "entry" : "entries"} by date`
            : "View your entries by date"}
        </p>
      </div>

      <div className="flex items-center space-x-4">
        <button
          onClick={onGoToToday}
          className="px-4 py-2 text-sm font-medium text-lotus-400 bg-lotus-500/20 rounded-lg hover:bg-lotus-500/30 transition-colors flex items-center space-x-2"
        >
          <Calendar size={16} />
          <span>Today</span>
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onNavigateMonth("prev")}
            className="p-2 text-dark-400 hover:text-dark-200 hover:bg-dark-700/50 rounded-lg transition-colors"
          >
            <ChevronLeft size={20} />
          </button>

          <h2 className="text-xl font-semibold text-dark-50 min-w-[200px] text-center">
            {monthYear}
          </h2>

          <button
            onClick={() => onNavigateMonth("next")}
            className="p-2 text-dark-400 hover:text-dark-200 hover:bg-dark-700/50 rounded-lg transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
