import { useMemo } from 'react';
import { useJournalData } from './useJournalData';

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

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

        const now = new Date();
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

        // 1. Entries this week
        const entriesThisWeek = journals.filter(journal =>
            new Date(journal.createdAt) >= oneWeekAgo
        ).length;

        // 2. Calculate current streak (consecutive days with entries)
        const currentStreak = calculateStreak(journals);

        // 3. Calculate sentiment trend from mood averages (last 7 days)
        const recentEntries = journals.filter(journal =>
            new Date(journal.createdAt) >= oneWeekAgo
        );

        const avgMood = recentEntries.length > 0
            ? recentEntries.reduce((sum, entry) => sum + parseInt(entry.userMood), 0) / recentEntries.length
            : 0;

        const sentimentTrend = getSentimentFromMood(avgMood);

        // 4. Recent entries for display (last 2-3)
        const recentForDisplay = journals.slice(0, 3).map(entry => ({
            id: parseInt(entry.journalId),
            title: generateTitle(entry.journalText),
            date: formatRelativeDate(entry.createdAt),
            preview: entry.journalText,
            sentiment: getSentimentFromMoodInt(parseInt(entry.userMood)) as 'positive' | 'neutral' | 'negative',
        }));

        return {
            entriesThisWeek,
            currentStreak,
            sentimentTrend,
            avgMood: Math.round(avgMood * 10) / 10, // Round to 1 decimal
            recentEntries: recentForDisplay
        };
    }, [journals]);

    return {
        ...dashboardStats,
        loading,
        totalEntries: journals.length
    };
}

// Helper function to calculate writing streak
function calculateStreak(journals: JournalEntry[]): number {
    if (!journals.length) return 0;

    // Group entries by date (YYYY-MM-DD)
    const entriesByDate = journals.reduce((acc, journal) => {
        const date = new Date(journal.createdAt).toISOString().split('T')[0];
        acc.add(date);
        return acc;
    }, new Set<string>());

    const sortedDates = Array.from(entriesByDate).sort().reverse();

    let streak = 0;
    const today = new Date().toISOString().split('T')[0];
    let currentDate = today;

    // Check if there's an entry today or yesterday to start streak
    if (!sortedDates.includes(today)) {
        const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        if (!sortedDates.includes(yesterday)) {
            return 0; // No recent entries
        }
        currentDate = yesterday;
    }

    // Count consecutive days
    for (const date of sortedDates) {
        if (date === currentDate) {
            streak++;
            // Move to previous day
            const prevDate = new Date(new Date(currentDate).getTime() - 24 * 60 * 60 * 1000);
            currentDate = prevDate.toISOString().split('T')[0];
        } else {
            break;
        }
    }

    return streak;
}

// Convert mood number to sentiment category
function getSentimentFromMood(avgMood: number): string {
    if (avgMood >= 7) return 'Positive';
    if (avgMood >= 4) return 'Neutral';
    return 'Negative';
}

function getSentimentFromMoodInt(mood: number): string {
    if (mood >= 7) return 'positive';
    if (mood >= 4) return 'neutral';
    return 'negative';
}

// Generate a title from journal text
function generateTitle(text: string): string {
    const words = text.trim().split(' ');
    if (words.length <= 4) return text;
    return words.slice(0, 4).join(' ') + '...';
}

// Format date as relative time
function formatRelativeDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return '1 day ago';
    if (diffInDays < 7) return `${diffInDays} days ago`;

    return date.toLocaleDateString();
}