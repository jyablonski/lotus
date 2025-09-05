'use client';

import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { CalendarHeader } from '@/components/calendar/CalendarHeader';
import { CalendarGrid } from '@/components/calendar/CalendarGrid';
import { SelectedDateEntries } from '@/components/calendar/SelectedDateEntries';
import { useCalendarData } from '@/hooks/useCalendarData';

export default function CalendarPage() {
    const {
        calendarDays,
        selectedDate,
        setSelectedDate,
        selectedDateEntries,
        currentMonth,
        navigateMonth,
        goToToday,
        loading
    } = useCalendarData();

    if (loading) return <LoadingSpinner />;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <CalendarHeader
                currentMonth={currentMonth}
                onNavigateMonth={navigateMonth}
                onGoToToday={goToToday}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Calendar Grid */}
                <div className="lg:col-span-2">
                    <CalendarGrid
                        calendarDays={calendarDays}
                        onDateSelect={setSelectedDate}
                    />
                </div>

                {/* Selected Date Entries */}
                <div>
                    <SelectedDateEntries
                        selectedDate={selectedDate}
                        entries={selectedDateEntries}
                    />
                </div>
            </div>
        </div>
    );
}