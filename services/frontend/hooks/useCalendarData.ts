import { useMemo, useState } from 'react';
import { useJournalData } from './useJournalData';
import { groupJournalsByDate, generateCalendarDays} from '@/lib/utils/calendar';

export function useCalendarData() {
    const { journals, loading } = useJournalData();
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [currentMonth, setCurrentMonth] = useState<Date>(new Date());

    const calendarData = useMemo(() => {
        const entriesByDate = groupJournalsByDate(journals);
        const calendarDays = generateCalendarDays(currentMonth, entriesByDate, selectedDate);

        // Get entries for selected date
        const selectedDateString = selectedDate.toISOString().split('T')[0];
        const selectedDateEntries = entriesByDate[selectedDateString] || [];

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