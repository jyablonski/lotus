import "server-only";

import { UserJournalSummary } from "@/types/analytics";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

/**
 * Fetch user analytics from the backend (server-side only)
 * This calls the Go backend directly, bypassing the API route
 */
export async function fetchUserAnalytics(
  userId: string,
): Promise<UserJournalSummary | null> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/analytics/users/${userId}/journal-summary`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        // Cache for 60 seconds, revalidate in background
        next: { revalidate: 60 },
      },
    );

    if (!response.ok) {
      // User may not have any analytics yet (new user)
      if (response.status === 404) {
        return null;
      }
      console.error(`Backend analytics error: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const summary = data.summary;

    return {
      userId: summary.userId,
      userEmail: summary.userEmail,
      userRole: summary.userRole,
      userTimezone: summary.userTimezone,
      userCreatedAt: summary.userCreatedAt,
      totalJournals: summary.totalJournals || 0,
      activeDays: summary.activeDays || 0,
      avgMoodScore: summary.avgMoodScore ?? null,
      minMoodScore: summary.minMoodScore ?? null,
      maxMoodScore: summary.maxMoodScore ?? null,
      moodScoreStddev: summary.moodScoreStddev ?? null,
      positiveEntries: summary.positiveEntries || 0,
      negativeEntries: summary.negativeEntries || 0,
      neutralEntries: summary.neutralEntries || 0,
      avgSentimentScore: summary.avgSentimentScore ?? null,
      avgJournalLength: summary.avgJournalLength ?? null,
      firstJournalAt: summary.firstJournalAt ?? null,
      lastJournalAt: summary.lastJournalAt ?? null,
      lastModifiedAt: summary.lastModifiedAt ?? null,
      totalJournals30d: summary.totalJournals_30d || 0,
      avgMoodScore30d: summary.avgMoodScore_30d ?? null,
      minMoodScore30d: summary.minMoodScore_30d ?? null,
      maxMoodScore30d: summary.maxMoodScore_30d ?? null,
      dailyStreak: summary.dailyStreak || 0,
      positivePercentage: summary.positivePercentage ?? null,
      daysSinceLastJournal: summary.daysSinceLastJournal ?? null,
      daysBetweenFirstAndLastJournal:
        summary.daysBetweenFirstAndLastJournal ?? null,
      journalsPerActiveDay: summary.journalsPerActiveDay ?? null,
    };
  } catch (error) {
    console.error("Error fetching analytics:", error);
    return null;
  }
}
