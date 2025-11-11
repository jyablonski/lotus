import { JournalEntry } from "@/types/journal";

export type DashboardEntry = {
  id: number;
  title: string;
  date: string;
  preview: string;
  sentiment: "positive" | "neutral" | "negative";
};

export function calculateEntriesThisWeek(journals: JournalEntry[]): number {
  const now = new Date();
  const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  return journals.filter((journal) => new Date(journal.createdAt) >= oneWeekAgo)
    .length;
}

export function calculateStreak(journals: JournalEntry[]): number {
  if (!journals.length) return 0;

  // Group entries by date (YYYY-MM-DD)
  const entriesByDate = journals.reduce((acc, journal) => {
    const date = new Date(journal.createdAt).toISOString().split("T")[0];
    acc.add(date);
    return acc;
  }, new Set<string>());

  const sortedDates = Array.from(entriesByDate).sort().reverse();

  let streak = 0;
  const today = new Date().toISOString().split("T")[0];
  let currentDate = today;

  // Check if there's an entry today or yesterday to start streak
  if (!sortedDates.includes(today)) {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0];
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

/**
 * Calculate average mood score from recent journal entries
 * Mood scores: excited=8, happy=7, content=6, neutral=5, tired=4, sad=3, anxious=2, angry=1
 */
export function calculateAverageMood(
  journals: JournalEntry[],
  days: number = 7,
): number {
  const now = new Date();
  const daysAgo = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

  const recentEntries = journals.filter(
    (journal) => new Date(journal.createdAt) >= daysAgo,
  );

  if (recentEntries.length === 0) return 0;

  // userMood is already a number, no need to parseInt
  return (
    recentEntries.reduce((sum, entry) => sum + entry.userMood, 0) /
    recentEntries.length
  );
}

export function getSentimentFromMood(avgMood: number): string {
  if (avgMood >= 7) return "Positive";
  if (avgMood >= 4) return "Neutral";
  return "Negative";
}

export function getSentimentFromMoodInt(
  mood: number,
): "positive" | "neutral" | "negative" {
  if (mood >= 7) return "positive";
  if (mood >= 4) return "neutral";
  return "negative";
}

export function generateTitle(text: string): string {
  const words = text.trim().split(" ");
  if (words.length <= 4) return text;
  return words.slice(0, 4).join(" ") + "...";
}

export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor(
    (now.getTime() - date.getTime()) / (1000 * 60 * 60),
  );

  if (diffInHours < 1) return "Just now";
  if (diffInHours < 24) return `${diffInHours} hours ago`;

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays === 1) return "1 day ago";
  if (diffInDays < 7) return `${diffInDays} days ago`;

  return date.toLocaleDateString();
}

export function formatRecentEntries(
  journals: JournalEntry[],
  count: number = 3,
): DashboardEntry[] {
  return journals.slice(0, count).map((entry) => ({
    id: parseInt(entry.journalId),
    title: generateTitle(entry.journalText),
    date: formatRelativeDate(entry.createdAt),
    preview: entry.journalText,
    // userMood is already a number, no need to parseInt
    sentiment: getSentimentFromMoodInt(entry.userMood),
  }));
}
