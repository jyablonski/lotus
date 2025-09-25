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
        loading,
        error,
        totalEntries
    } = useCalendarData();

    if (loading) return <LoadingSpinner />;
    if (error) return <div className="text-red-500">Error loading calendar: {error}</div>;

    return (
        <div className="page-container">
            <div className="content-container">
                <CalendarHeader
                    currentMonth={currentMonth}
                    onNavigateMonth={navigateMonth}
                    onGoToToday={goToToday}
                    totalEntries={totalEntries}
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
        </div>
    );
}