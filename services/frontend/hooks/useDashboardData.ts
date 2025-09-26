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
    // Load ALL journals for dashboard calculations
    // Dashboard needs complete data for accurate stats
    // this could be optimized with dedicated data pipelines & endpoints
    // to serve the pre-aggregated stats later on
    const { journals, loading, error } = useJournalData({
        initialLimit: 1000, // Large number to get all entries
        autoLoad: true
    });

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
        error,
        totalEntries: journals.length
    };
}