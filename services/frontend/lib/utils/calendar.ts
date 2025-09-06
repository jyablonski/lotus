export type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export type CalendarDay = {
    date: Date;
    dateString: string;
    entries: JournalEntry[];
    isCurrentMonth: boolean;
    isToday: boolean;
    isSelected: boolean;
    entryCount: number;
    avgMood: number;
};

export function groupJournalsByDate(journals: JournalEntry[]): Record<string, JournalEntry[]> {
    return journals.reduce((acc, journal) => {
        const date = new Date(journal.createdAt).toISOString().split('T')[0];
        if (!acc[date]) {
            acc[date] = [];
        }
        acc[date].push(journal);
        return acc;
    }, {} as Record<string, JournalEntry[]>);
}

export function generateCalendarDays(
    currentMonth: Date,
    entriesByDate: Record<string, JournalEntry[]>,
    selectedDate: Date
): CalendarDay[] {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    // First day of the month
    const firstDay = new Date(year, month, 1);

    // Start from the first Sunday before or on the first day
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - startDate.getDay());

    // Generate 42 days (6 weeks) for the calendar grid
    const calendarDays: CalendarDay[] = [];
    const currentDate = new Date(startDate);
    const selectedDateString = selectedDate.toISOString().split('T')[0];
    const todayString = new Date().toISOString().split('T')[0];

    for (let i = 0; i < 42; i++) {
        const dateString = currentDate.toISOString().split('T')[0];
        const entries = entriesByDate[dateString] || [];

        calendarDays.push({
            date: new Date(currentDate),
            dateString,
            entries,
            isCurrentMonth: currentDate.getMonth() === month,
            isToday: dateString === todayString,
            isSelected: dateString === selectedDateString,
            entryCount: entries.length,
            avgMood: entries.length > 0
                ? entries.reduce((sum, entry) => sum + parseInt(entry.userMood), 0) / entries.length
                : 0
        });

        currentDate.setDate(currentDate.getDate() + 1);
    }

    return calendarDays;
}