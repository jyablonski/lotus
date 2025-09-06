import { useMemo } from 'react';
import { useJournalData } from './useJournalData';

// Define the journal entry type
type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export function useProfileData() {
    const { journals, loading } = useJournalData();

    const profileStats = useMemo(() => {
        if (!journals.length) {
            return {
                totalEntries: 0,
                thisMonth: 0,
                thisWeek: 0,
                averageMood: 0,
                longestStreak: 0,
                currentStreak: 0,
                mostActiveDay: 'No data',
                firstEntryDate: null,
                favoriteModCategory: 'No data',
                totalWords: 0
            };
        }

        const now = new Date();
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        const startOfWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

        // Basic counts
        const totalEntries = journals.length;
        const thisMonth = journals.filter(j => new Date(j.createdAt) >= startOfMonth).length;
        const thisWeek = journals.filter(j => new Date(j.createdAt) >= startOfWeek).length;

        // Average mood
        const averageMood = journals.reduce((sum, j) => sum + parseInt(j.userMood), 0) / journals.length;

        // First entry date
        const firstEntryDate = new Date(journals[journals.length - 1].createdAt);

        // Most active day of week
        const dayCount = journals.reduce((acc, journal) => {
            const day = new Date(journal.createdAt).toLocaleDateString('en-US', { weekday: 'long' });
            acc[day] = (acc[day] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const mostActiveDay = Object.entries(dayCount).reduce((a, b) =>
            dayCount[a[0]] > dayCount[b[0]] ? a : b
        )?.[0] || 'No data';

        // Favorite mood category
        const moodCount = journals.reduce((acc, journal) => {
            const moodInt = parseInt(journal.userMood);
            const category = moodInt >= 7 ? 'Positive' : moodInt >= 4 ? 'Neutral' : 'Negative';
            acc[category] = (acc[category] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const favoriteModCategory = Object.entries(moodCount).reduce((a, b) =>
            moodCount[a[0]] > moodCount[b[0]] ? a : b
        )?.[0] || 'No data';

        // Total words (rough estimate)
        const totalWords = journals.reduce((sum, journal) => {
            return sum + journal.journalText.split(/\s+/).filter(word => word.length > 0).length;
        }, 0);

        // Calculate streaks
        const currentStreak = calculateCurrentStreak(journals);
        const longestStreak = calculateLongestStreak(journals);

        return {
            totalEntries,
            thisMonth,
            thisWeek,
            averageMood: Math.round(averageMood * 10) / 10,
            longestStreak,
            currentStreak,
            mostActiveDay,
            firstEntryDate,
            favoriteModCategory,
            totalWords
        };
    }, [journals]);

    return {
        ...profileStats,
        loading
    };
}

// Helper functions for streak calculation with proper typing
function calculateCurrentStreak(journals: JournalEntry[]): number {
    if (!journals.length) return 0;

    const entriesByDate = journals.reduce((acc, journal) => {
        const date = new Date(journal.createdAt).toISOString().split('T')[0];
        acc.add(date);
        return acc;
    }, new Set<string>());

    const sortedDates: string[] = Array.from(entriesByDate).sort().reverse();
    let streak = 0;
    const today = new Date().toISOString().split('T')[0];
    let currentDate = today;

    if (!sortedDates.includes(today)) {
        const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        if (!sortedDates.includes(yesterday)) return 0;
        currentDate = yesterday;
    }

    for (const date of sortedDates) {
        if (date === currentDate) {
            streak++;
            const prevDate = new Date(new Date(currentDate).getTime() - 24 * 60 * 60 * 1000);
            currentDate = prevDate.toISOString().split('T')[0];
        } else {
            break;
        }
    }

    return streak;
}

function calculateLongestStreak(journals: JournalEntry[]): number {
    if (!journals.length) return 0;

    const entriesByDate = journals.reduce((acc, journal) => {
        const date = new Date(journal.createdAt).toISOString().split('T')[0];
        acc.add(date);
        return acc;
    }, new Set<string>());

    const sortedDates: string[] = Array.from(entriesByDate).sort();
    let longestStreak = 0;
    let currentStreak = 0;

    for (let i = 0; i < sortedDates.length; i++) {
        if (i === 0) {
            currentStreak = 1;
        } else {
            const prevDateString: string = sortedDates[i - 1];
            const currDateString: string = sortedDates[i];

            const prevDate = new Date(prevDateString);
            const currDate = new Date(currDateString);

            const diffInDays = Math.round((currDate.getTime() - prevDate.getTime()) / (1000 * 60 * 60 * 24));

            if (diffInDays === 1) {
                currentStreak++;
            } else {
                longestStreak = Math.max(longestStreak, currentStreak);
                currentStreak = 1;
            }
        }
    }

    return Math.max(longestStreak, currentStreak);
}