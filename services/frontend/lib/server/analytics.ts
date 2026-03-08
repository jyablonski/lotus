import "server-only";

import { JournalEntry } from "@/types/journal";
import { UserJournalSummary } from "@/types/analytics";
import { fetchAllJournalsForUser } from "./journals";
import {
  getUniqueDateStrings,
  calculateCurrentStreak,
} from "@/lib/utils/profileStats";

/**
 * Compute a UserJournalSummary entirely from raw journal entries.
 * This replaces the previous approach that queried the gold.user_journal_summary
 * dbt-materialized table, removing the dependency on gold.* tables.
 */
function computeAnalyticsFromJournals(
  journals: JournalEntry[],
  userId: string,
): UserJournalSummary {
  if (journals.length === 0) {
    return emptyAnalytics(userId);
  }

  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

  // All-time metrics
  const totalJournals = journals.length;
  const uniqueDates = getUniqueDateStrings(journals);
  const activeDays = uniqueDates.size;

  const moodScores = journals.map((j) => j.userMood);
  const avgMoodScore =
    moodScores.reduce((sum, m) => sum + m, 0) / moodScores.length;
  const minMoodScore = Math.min(...moodScores);
  const maxMoodScore = Math.max(...moodScores);

  // Standard deviation
  const variance =
    moodScores.reduce((sum, m) => sum + Math.pow(m - avgMoodScore, 2), 0) /
    moodScores.length;
  const moodScoreStddev = Math.sqrt(variance);

  // Sentiment counts (mood >= 7 = positive, >= 4 = neutral, < 4 = negative)
  const positiveEntries = moodScores.filter((m) => m >= 7).length;
  const negativeEntries = moodScores.filter((m) => m < 4).length;
  const neutralEntries = moodScores.filter((m) => m >= 4 && m < 7).length;

  // Avg sentiment as a normalized -1..1 score based on mood (1-10 scale):
  // (mood - 5.5) / 4.5 maps 1 -> -1, 10 -> 1
  const avgSentimentScore =
    moodScores.reduce((sum, m) => sum + (m - 5.5) / 4.5, 0) / moodScores.length;

  // Content metrics
  const avgJournalLength =
    journals.reduce(
      (sum, j) =>
        sum + j.journalText.split(/\s+/).filter((w) => w.length > 0).length,
      0,
    ) / journals.length;

  // Timestamps
  const sortedByDate = [...journals].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
  );
  const firstJournalAt = sortedByDate[0].createdAt;
  const lastJournalAt = sortedByDate[sortedByDate.length - 1].createdAt;

  // 30-day metrics
  const recent30d = journals.filter(
    (j) => new Date(j.createdAt) >= thirtyDaysAgo,
  );
  const totalJournals30d = recent30d.length;
  const recentMoods = recent30d.map((j) => j.userMood);
  const avgMoodScore30d =
    recentMoods.length > 0
      ? recentMoods.reduce((sum, m) => sum + m, 0) / recentMoods.length
      : null;
  const minMoodScore30d =
    recentMoods.length > 0 ? Math.min(...recentMoods) : null;
  const maxMoodScore30d =
    recentMoods.length > 0 ? Math.max(...recentMoods) : null;

  // Streak
  const dailyStreak = calculateCurrentStreak(journals);

  // Calculated fields
  const positivePercentage =
    totalJournals > 0 ? (positiveEntries / totalJournals) * 100 : null;

  const lastJournalDate = new Date(lastJournalAt);
  const daysSinceLastJournal = Math.floor(
    (now.getTime() - lastJournalDate.getTime()) / (1000 * 60 * 60 * 24),
  );

  const firstDate = new Date(firstJournalAt);
  const daysBetweenFirstAndLastJournal = Math.floor(
    (lastJournalDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24),
  );

  const journalsPerActiveDay =
    activeDays > 0 ? totalJournals / activeDays : null;

  return {
    userId,
    userEmail: "",
    userRole: "",
    userTimezone: "",
    userCreatedAt: "",
    totalJournals,
    activeDays,
    avgMoodScore: round2(avgMoodScore),
    minMoodScore,
    maxMoodScore,
    moodScoreStddev: round2(moodScoreStddev),
    positiveEntries,
    negativeEntries,
    neutralEntries,
    avgSentimentScore: round2(avgSentimentScore),
    avgJournalLength: round2(avgJournalLength),
    firstJournalAt,
    lastJournalAt,
    lastModifiedAt: lastJournalAt,
    totalJournals30d,
    avgMoodScore30d: avgMoodScore30d !== null ? round2(avgMoodScore30d) : null,
    minMoodScore30d,
    maxMoodScore30d,
    dailyStreak,
    positivePercentage:
      positivePercentage !== null ? round2(positivePercentage) : null,
    daysSinceLastJournal,
    daysBetweenFirstAndLastJournal,
    journalsPerActiveDay:
      journalsPerActiveDay !== null ? round2(journalsPerActiveDay) : null,
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function emptyAnalytics(userId: string): UserJournalSummary {
  return {
    userId,
    userEmail: "",
    userRole: "",
    userTimezone: "",
    userCreatedAt: "",
    totalJournals: 0,
    activeDays: 0,
    avgMoodScore: null,
    minMoodScore: null,
    maxMoodScore: null,
    moodScoreStddev: null,
    positiveEntries: 0,
    negativeEntries: 0,
    neutralEntries: 0,
    avgSentimentScore: null,
    avgJournalLength: null,
    firstJournalAt: null,
    lastJournalAt: null,
    lastModifiedAt: null,
    totalJournals30d: 0,
    avgMoodScore30d: null,
    minMoodScore30d: null,
    maxMoodScore30d: null,
    dailyStreak: 0,
    positivePercentage: null,
    daysSinceLastJournal: null,
    daysBetweenFirstAndLastJournal: null,
    journalsPerActiveDay: null,
  };
}

/**
 * Fetch user analytics by computing from source journal entries.
 *
 * Previously this called GET /v1/analytics/users/{userId}/journal-summary
 * which queried the gold.user_journal_summary dbt table. Now it computes
 * everything from source.journals via the existing journals endpoint.
 */
export async function fetchUserAnalytics(
  userId: string,
): Promise<UserJournalSummary | null> {
  try {
    const { journals } = await fetchAllJournalsForUser(userId);

    if (journals.length === 0) {
      return null;
    }

    return computeAnalyticsFromJournals(journals, userId);
  } catch (error) {
    console.error("Error computing analytics:", error);
    return null;
  }
}
