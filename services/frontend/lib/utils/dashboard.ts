import { JournalEntry } from "@/types/journal";
import { calculateCurrentStreak } from "@/lib/utils/profileStats";
import { formatShortDate, toTimezoneDateString } from "@/lib/utils/datetime";

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

/**
 * Calculate current streak. Delegates to shared implementation.
 */
export function calculateStreak(
  journals: JournalEntry[],
  timezone: string = "UTC",
): number {
  return calculateCurrentStreak(journals, timezone);
}

/**
 * Calculate average mood score from recent journal entries.
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

  return (
    recentEntries.reduce((sum, entry) => sum + entry.userMood, 0) /
    recentEntries.length
  );
}

/** Mood category from average score (capitalized for display). */
export function getSentimentFromMood(avgMood: number): string {
  if (avgMood >= 7) return "Positive";
  if (avgMood >= 4) return "Neutral";
  return "Negative";
}

/** Mood category from a single mood int (lowercase for data). */
export function getSentimentFromMoodInt(
  mood: number,
): "positive" | "neutral" | "negative" {
  if (mood >= 7) return "positive";
  if (mood >= 4) return "neutral";
  return "negative";
}

export function generateTitle(text: string): string {
  const trimmed = text.trim();
  const words = trimmed.split(" ");
  if (words.length <= 4) return trimmed;
  return words.slice(0, 4).join(" ") + "...";
}

/**
 * Format date as absolute string (safe for SSR).
 * Use this for server-rendered content to avoid hydration mismatches.
 */
export function formatAbsoluteDate(
  dateString: string,
  timezone: string = "UTC",
): string {
  return toTimezoneDateString(new Date(dateString), timezone);
}

/**
 * Format date as relative string (client-side only).
 * WARNING: Do not use in server-rendered components - causes hydration mismatch.
 */
export function formatRelativeDate(
  dateString: string,
  timezone: string = "UTC",
): string {
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

  return formatShortDate(dateString, timezone);
}

export function formatRecentEntries(
  journals: JournalEntry[],
  count: number = 3,
): DashboardEntry[] {
  return journals.slice(0, count).map((entry) => ({
    id: parseInt(entry.journalId),
    title: generateTitle(entry.journalText),
    date: entry.createdAt,
    preview: entry.journalText,
    sentiment: getSentimentFromMoodInt(entry.userMood),
  }));
}
