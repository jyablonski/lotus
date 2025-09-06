import { useMemo } from 'react';
import { useJournalData } from './useJournalData';
import {
    calculateEntriesThisWeek,
    calculateStreak,
    calculateAverageMood,
    getSentimentFromMood,
    formatRecentEntries
} from '@/lib/utils/dashboard';

export function useDashboardData() {
    const { journals, loading } = useJournalData();

    const dashboardStats = useMemo(() => {
        if (!journals.length) {
            return {
                entriesThisWeek: 0,
                currentStreak: 0,
                sentimentTrend: 'No Data',
                avgMood: 0,
                recentEntries: []
            };
        }

        const entriesThisWeek = calculateEntriesThisWeek(journals);
        const currentStreak = calculateStreak(journals);
        const avgMood = calculateAverageMood(journals, 7);
        const sentimentTrend = getSentimentFromMood(avgMood);
        const recentEntries = formatRecentEntries(journals, 3);

        return {
            entriesThisWeek,
            currentStreak,
            sentimentTrend,
            avgMood: Math.round(avgMood * 10) / 10, // Round to 1 decimal
            recentEntries
        };
    }, [journals]);

    return {
        ...dashboardStats,
        loading,
        totalEntries: journals.length
    };
}