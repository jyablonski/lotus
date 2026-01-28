"use client";

import Link from "next/link";
import {
  BookOpen,
  Calendar,
  TrendingUp,
  Flame,
  Smile,
  BarChart3,
  Edit3,
  User,
} from "lucide-react";
import { JournalEntry } from "@/types/journal";
import { UserJournalSummary } from "@/types/analytics";
import {
  getSentimentFromMood,
  formatRecentEntries,
  DashboardEntry,
} from "@/lib/utils/dashboard";
import { RelativeDate } from "@/components/ui/RelativeDate";

interface LoggedInDashboardProps {
  analytics: UserJournalSummary | null;
  recentJournals: JournalEntry[];
  userName?: string;
}

export const LoggedInDashboard = ({
  analytics,
  recentJournals,
  userName,
}: LoggedInDashboardProps) => {
  // Derive display values from analytics (or use defaults for new users)
  const totalEntries = analytics?.totalJournals ?? 0;
  const entriesLast30Days = analytics?.totalJournals30d ?? 0;
  const currentStreak = analytics?.dailyStreak ?? 0;
  const activeDays = analytics?.activeDays ?? 0;
  const avgMood = analytics?.avgMoodScore30d ?? analytics?.avgMoodScore ?? 0;
  const avgMoodRounded = avgMood ? Math.round(avgMood * 10) / 10 : 0;
  const positivePct = analytics?.positivePercentage ?? null;
  const daysSinceLastJournal = analytics?.daysSinceLastJournal ?? null;

  const sentimentTrend =
    avgMood > 0 ? getSentimentFromMood(avgMood) : "No Data";

  // Format recent entries for display
  const recentEntries: DashboardEntry[] = formatRecentEntries(
    recentJournals,
    3,
  );

  const getTrendIndicator = (trend: string) => {
    switch (trend) {
      case "Positive":
        return "Good vibes";
      case "Negative":
        return "Tough times";
      default:
        return "Steady";
    }
  };

  const getStreakMessage = () => {
    if (daysSinceLastJournal === 0) return "Keep it up!";
    if (daysSinceLastJournal === 1) return "Write today to continue!";
    if (daysSinceLastJournal !== null && daysSinceLastJournal > 1)
      return `${daysSinceLastJournal} days since last entry`;
    return currentStreak > 0 ? "Keep it up!" : "Start your streak!";
  };

  const greeting = userName ? `Welcome back, ${userName}!` : "Welcome back!";

  return (
    <div className="page-container">
      <div className="content-container space-y-8">
        {/* Welcome Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="heading-1">{greeting}</h1>
            <p className="text-muted-dark mt-1">
              Here&apos;s what&apos;s happening with your journal
            </p>
          </div>
          <Link href="/journal/create">
            <button className="btn-primary flex items-center space-x-2">
              <Edit3 size={16} />
              <span>New Entry</span>
            </button>
          </Link>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-muted-dark text-sm">Last 30 Days</p>
                <p className="text-2xl font-bold text-primary-dark">
                  {entriesLast30Days}
                </p>
              </div>
              <BookOpen size={24} className="text-lotus-400" />
            </div>
            <p className="text-xs text-muted-dark">
              {entriesLast30Days > 0
                ? `${entriesLast30Days} entries`
                : "Start writing!"}
            </p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-muted-dark text-sm">Current Streak</p>
                <p className="text-2xl font-bold text-primary-dark">
                  {currentStreak > 0 ? `${currentStreak}` : "0"}
                  <span className="text-sm font-normal text-muted-dark ml-1">
                    days
                  </span>
                </p>
              </div>
              <Flame size={24} className="text-orange-400" />
            </div>
            <p className="text-xs text-muted-dark">{getStreakMessage()}</p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-muted-dark text-sm">Mood Trend</p>
                <p className="text-2xl font-bold text-primary-dark">
                  {sentimentTrend}
                </p>
              </div>
              <Smile size={24} className="text-green-400" />
            </div>
            <p className="text-xs text-muted-dark">
              {sentimentTrend !== "No Data"
                ? getTrendIndicator(sentimentTrend)
                : "Write to see trends"}
            </p>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-muted-dark text-sm">Total Entries</p>
                <p className="text-2xl font-bold text-primary-dark">
                  {totalEntries}
                </p>
              </div>
              <BarChart3 size={24} className="text-lotus-400" />
            </div>
            <p className="text-xs text-muted-dark">
              {avgMoodRounded > 0
                ? `Avg mood: ${avgMoodRounded}/10`
                : "No data yet"}
            </p>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Recent Entries */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <div className="p-6 border-b border-dark-600">
                <h2 className="text-xl font-semibold text-primary-dark">
                  Recent Entries
                </h2>
              </div>
              <div className="p-6 space-y-4">
                {recentEntries.length > 0 ? (
                  <>
                    {recentEntries.map((entry) => (
                      <div key={entry.id} className="journal-entry">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-medium text-primary-dark">
                            {entry.title}
                          </h3>
                          <div className="flex items-center space-x-2">
                            <div
                              className={`mood-indicator mood-${entry.sentiment}`}
                            ></div>
                            <RelativeDate
                              date={entry.date}
                              className="text-xs text-muted-dark"
                            />
                          </div>
                        </div>
                        <p className="text-muted-dark text-sm line-clamp-2">
                          {entry.preview}
                        </p>
                        <Link
                          href={`/journal/${entry.id}`}
                          className="inline-block mt-2"
                        >
                          <span className="text-lotus-400 text-sm hover:text-lotus-300 transition-colors">
                            Read more →
                          </span>
                        </Link>
                      </div>
                    ))}
                    <Link href="/journal/home" className="block">
                      <div className="text-center py-4 text-lotus-400 hover:text-lotus-300 font-medium transition-colors">
                        View all entries →
                      </div>
                    </Link>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-dark mb-4">No entries yet</p>
                    <Link href="/journal/create">
                      <button className="btn-primary">
                        Create Your First Entry
                      </button>
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Quick Actions & Insights */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="card">
              <div className="p-6 border-b border-dark-600">
                <h2 className="text-lg font-semibold text-primary-dark">
                  Quick Actions
                </h2>
              </div>
              <div className="p-6 space-y-3">
                <Link
                  href="/journal/calendar"
                  className="nav-link flex items-center space-x-3 p-3 rounded-lg"
                >
                  <Calendar size={20} className="text-lotus-400" />
                  <div>
                    <p className="font-medium text-primary-dark">
                      View Calendar
                    </p>
                    <p className="text-sm text-muted-dark">
                      See entries by date
                    </p>
                  </div>
                </Link>
                <Link
                  href="/journal/insights"
                  className="nav-link flex items-center space-x-3 p-3 rounded-lg"
                >
                  <TrendingUp size={20} className="text-green-400" />
                  <div>
                    <p className="font-medium text-primary-dark">Insights</p>
                    <p className="text-sm text-muted-dark">
                      Analyze your patterns
                    </p>
                  </div>
                </Link>
                <Link
                  href="/profile"
                  className="nav-link flex items-center space-x-3 p-3 rounded-lg"
                >
                  <User size={20} className="text-muted-dark" />
                  <div>
                    <p className="font-medium text-primary-dark">Settings</p>
                    <p className="text-sm text-muted-dark">
                      Manage your account
                    </p>
                  </div>
                </Link>
              </div>
            </div>

            {/* Writing Stats */}
            <div className="card">
              <div className="p-6 border-b border-dark-600">
                <h2 className="text-lg font-semibold text-primary-dark">
                  Writing Stats
                </h2>
              </div>
              <div className="p-6">
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-dark">Total entries:</span>
                    <span className="font-medium text-primary-dark">
                      {totalEntries}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-dark">Active days:</span>
                    <span className="font-medium text-primary-dark">
                      {activeDays}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-dark">Current streak:</span>
                    <span className="font-medium text-primary-dark">
                      {currentStreak} days
                    </span>
                  </div>
                  {avgMoodRounded > 0 && (
                    <div className="flex justify-between">
                      <span className="text-muted-dark">Avg mood:</span>
                      <span className="font-medium text-primary-dark">
                        {avgMoodRounded}/10
                      </span>
                    </div>
                  )}
                  {positivePct !== null && positivePct !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-dark">Positive entries:</span>
                      <span className="font-medium text-primary-dark">
                        {Math.round(positivePct)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
