export interface UserJournalSummary {
  // User info
  userId: string;
  userEmail: string;
  userRole: string;
  userTimezone: string;
  userCreatedAt: string;

  // All-time metrics
  totalJournals: number;
  activeDays: number;
  avgMoodScore: number | null;
  minMoodScore: number | null;
  maxMoodScore: number | null;
  moodScoreStddev: number | null;

  // Sentiment metrics
  positiveEntries: number;
  negativeEntries: number;
  neutralEntries: number;
  avgSentimentScore: number | null;

  // Content metrics
  avgJournalLength: number | null;

  // Timestamps
  firstJournalAt: string | null;
  lastJournalAt: string | null;
  lastModifiedAt: string | null;

  // Last 30 days metrics
  totalJournals30d: number;
  avgMoodScore30d: number | null;
  minMoodScore30d: number | null;
  maxMoodScore30d: number | null;

  // Streak and calculated fields
  dailyStreak: number;
  positivePercentage: number | null;
  daysSinceLastJournal: number | null;
  daysBetweenFirstAndLastJournal: number | null;
  journalsPerActiveDay: number | null;
}
