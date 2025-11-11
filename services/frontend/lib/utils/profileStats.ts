import { JournalEntry } from "@/types/journal";

export type ProfileStats = {
  totalEntries: number;
  thisMonth: number;
  thisWeek: number;
  averageMood: number;
  longestStreak: number;
  currentStreak: number;
  mostActiveDay: string;
  firstEntryDate: Date | null;
  favoriteModCategory: string;
  totalWords: number;
};

export function calculateBasicCounts(journals: JournalEntry[]) {
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const startOfWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  return {
    totalEntries: journals.length,
    thisMonth: journals.filter((j) => new Date(j.createdAt) >= startOfMonth)
      .length,
    thisWeek: journals.filter((j) => new Date(j.createdAt) >= startOfWeek)
      .length,
  };
}

/**
 * Calculate average mood score
 * Mood scores: excited=8, happy=7, content=6, neutral=5, tired=4, sad=3, anxious=2, angry=1
 */
export function calculateAverageMood(journals: JournalEntry[]): number {
  if (!journals.length) return 0;
  // userMood is already a number, no need to parseInt
  return journals.reduce((sum, j) => sum + j.userMood, 0) / journals.length;
}

export function getFirstEntryDate(journals: JournalEntry[]): Date | null {
  if (!journals.length) return null;
  return new Date(journals[journals.length - 1].createdAt);
}

export function getMostActiveDay(journals: JournalEntry[]): string {
  if (!journals.length) return "No data";

  const dayCount = journals.reduce(
    (acc, journal) => {
      const day = new Date(journal.createdAt).toLocaleDateString("en-US", {
        weekday: "long",
      });
      acc[day] = (acc[day] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const mostActive = Object.entries(dayCount).reduce((a, b) =>
    dayCount[a[0]] > dayCount[b[0]] ? a : b,
  );

  return mostActive?.[0] || "No data";
}

export function getFavoriteMoodCategory(journals: JournalEntry[]): string {
  if (!journals.length) return "No data";

  const moodCount = journals.reduce(
    (acc, journal) => {
      // userMood is already a number, no need to parseInt
      const category =
        journal.userMood >= 7
          ? "Positive"
          : journal.userMood >= 4
            ? "Neutral"
            : "Negative";
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const favorite = Object.entries(moodCount).reduce((a, b) =>
    moodCount[a[0]] > moodCount[b[0]] ? a : b,
  );

  return favorite?.[0] || "No data";
}

export function calculateTotalWords(journals: JournalEntry[]): number {
  return journals.reduce((sum, journal) => {
    return (
      sum +
      journal.journalText.split(/\s+/).filter((word) => word.length > 0).length
    );
  }, 0);
}

export function calculateCurrentStreak(journals: JournalEntry[]): number {
  if (!journals.length) return 0;

  const entriesByDate = journals.reduce((acc, journal) => {
    const date = new Date(journal.createdAt).toISOString().split("T")[0];
    acc.add(date);
    return acc;
  }, new Set<string>());

  const sortedDates: string[] = Array.from(entriesByDate).sort().reverse();
  let streak = 0;
  const today = new Date().toISOString().split("T")[0];
  let currentDate = today;

  if (!sortedDates.includes(today)) {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0];
    if (!sortedDates.includes(yesterday)) return 0;
    currentDate = yesterday;
  }

  for (const date of sortedDates) {
    if (date === currentDate) {
      streak++;
      const prevDate = new Date(
        new Date(currentDate).getTime() - 24 * 60 * 60 * 1000,
      );
      currentDate = prevDate.toISOString().split("T")[0];
    } else {
      break;
    }
  }

  return streak;
}

export function calculateLongestStreak(journals: JournalEntry[]): number {
  if (!journals.length) return 0;

  const entriesByDate = journals.reduce((acc, journal) => {
    const date = new Date(journal.createdAt).toISOString().split("T")[0];
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

      const diffInDays = Math.round(
        (currDate.getTime() - prevDate.getTime()) / (1000 * 60 * 60 * 24),
      );

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

export function calculateProfileStats(journals: JournalEntry[]): ProfileStats {
  if (!journals.length) {
    return {
      totalEntries: 0,
      thisMonth: 0,
      thisWeek: 0,
      averageMood: 0,
      longestStreak: 0,
      currentStreak: 0,
      mostActiveDay: "No data",
      firstEntryDate: null,
      favoriteModCategory: "No data",
      totalWords: 0,
    };
  }

  const basicCounts = calculateBasicCounts(journals);
  const averageMood = calculateAverageMood(journals);
  const firstEntryDate = getFirstEntryDate(journals);
  const mostActiveDay = getMostActiveDay(journals);
  const favoriteModCategory = getFavoriteMoodCategory(journals);
  const totalWords = calculateTotalWords(journals);
  const currentStreak = calculateCurrentStreak(journals);
  const longestStreak = calculateLongestStreak(journals);

  return {
    ...basicCounts,
    averageMood: Math.round(averageMood * 10) / 10,
    longestStreak,
    currentStreak,
    mostActiveDay,
    firstEntryDate,
    favoriteModCategory,
    totalWords,
  };
}
