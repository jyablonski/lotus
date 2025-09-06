import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';

interface CalendarHeaderProps {
    currentMonth: Date;
    onNavigateMonth: (direction: 'prev' | 'next') => void;
    onGoToToday: () => void;
}

export function CalendarHeader({ currentMonth, onNavigateMonth, onGoToToday }: CalendarHeaderProps) {
    const monthYear = currentMonth.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    return (
        <div className="flex items-center justify-between mb-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Journal Calendar</h1>
                <p className="text-gray-600 mt-1">View your entries by date</p>
            </div>

            <div className="flex items-center space-x-4">
                <button
                    onClick={onGoToToday}
                    className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors flex items-center space-x-2"
                >
                    <Calendar size={16} />
                    <span>Today</span>
                </button>

                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => onNavigateMonth('prev')}
                        className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronLeft size={20} />
                    </button>

                    <h2 className="text-xl font-semibold text-gray-900 min-w-[200px] text-center">
                        {monthYear}
                    </h2>

                    <button
                        onClick={() => onNavigateMonth('next')}
                        className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
}