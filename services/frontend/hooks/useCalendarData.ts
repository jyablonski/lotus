import { useMemo, useState } from 'react';
import { useJournalData } from './useJournalData';

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export function useCalendarData() {
    const { journals, loading } = useJournalData();
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [currentMonth, setCurrentMonth] = useState<Date>(new Date());

    const calendarData = useMemo(() => {
        // Group entries by date (YYYY-MM-DD)
        const entriesByDate = journals.reduce((acc, journal) => {
            const date = new Date(journal.createdAt).toISOString().split('T')[0];
            if (!acc[date]) {
                acc[date] = [];
            }
            acc[date].push(journal);
            return acc;
        }, {} as Record<string, JournalEntry[]>);

        // Get entries for selected date
        const selectedDateString = selectedDate.toISOString().split('T')[0];
        const selectedDateEntries = entriesByDate[selectedDateString] || [];

        // Generate calendar grid for current month
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();

        // First day of the month
        const firstDay = new Date(year, month, 1);

        // Start from the first Sunday before or on the first day
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - startDate.getDay());

        // Generate 42 days (6 weeks) for the calendar grid
        const calendarDays = [];
        const currentDate = new Date(startDate);

        for (let i = 0; i < 42; i++) {
            const dateString = currentDate.toISOString().split('T')[0];
            const entries = entriesByDate[dateString] || [];

            calendarDays.push({
                date: new Date(currentDate),
                dateString,
                entries,
                isCurrentMonth: currentDate.getMonth() === month,
                isToday: dateString === new Date().toISOString().split('T')[0],
                isSelected: dateString === selectedDateString,
                entryCount: entries.length,
                avgMood: entries.length > 0
                    ? entries.reduce((sum, entry) => sum + parseInt(entry.userMood), 0) / entries.length
                    : 0
            });

            currentDate.setDate(currentDate.getDate() + 1);
        }

        return {
            calendarDays,
            entriesByDate,
            selectedDateEntries
        };
    }, [journals, selectedDate, currentMonth]);

    const navigateMonth = (direction: 'prev' | 'next') => {
        setCurrentMonth(prev => {
            const newDate = new Date(prev);
            if (direction === 'prev') {
                newDate.setMonth(newDate.getMonth() - 1);
            } else {
                newDate.setMonth(newDate.getMonth() + 1);
            }
            return newDate;
        });
    };

    const goToToday = () => {
        const today = new Date();
        setCurrentMonth(today);
        setSelectedDate(today);
    };

    return {
        ...calendarData,
        selectedDate,
        setSelectedDate,
        currentMonth,
        navigateMonth,
        goToToday,
        loading
    };
}