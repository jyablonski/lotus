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
import { CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { ROUTES } from "@/lib/routes";

interface LoggedInDashboardProps {
  analytics: UserJournalSummary | null;
  recentJournals: JournalEntry[];
  userName?: string;
  timezone?: string;
}

export const LoggedInDashboard = ({
  analytics,
  recentJournals,
  userName,
  timezone,
}: LoggedInDashboardProps) => {
  // Derive display values from analytics (or use defaults for new users)
  const totalEntries = analytics?.totalJournals ?? 0;
  const entriesLast30Days = analytics?.totalJournals30d ?? 0;
  const currentStreak = analytics?.dailyStreak ?? 0;
  const activeDays = analytics?.activeDays ?? 0;
  // Use all-time avg mood so it matches profile page (profile uses calculateAverageMood over all journals)
  const avgMood = analytics?.avgMoodScore ?? 0;
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
          <Link href={ROUTES.journal.create}>
            <button className="btn-primary flex items-center space-x-2">
              <Edit3 size={16} />
              <span>New Entry</span>
            </button>
          </Link>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Last 30 Days"
            value={entriesLast30Days}
            icon={<BookOpen size={24} className="text-lotus-400" />}
            trend={
              entriesLast30Days > 0
                ? `${entriesLast30Days} entries`
                : "Start writing!"
            }
            iconContainerClassName="p-2 bg-lotus-500/10 rounded-lg"
          />

          <StatCard
            title="Current Streak"
            value={currentStreak > 0 ? `${currentStreak} days` : "0 days"}
            icon={<Flame size={24} className="text-orange-400" />}
            trend={getStreakMessage()}
            iconContainerClassName="p-2 bg-orange-500/10 rounded-lg"
          />

          <StatCard
            title="Mood Trend"
            value={sentimentTrend}
            icon={<Smile size={24} className="text-green-400" />}
            trend={
              sentimentTrend !== "No Data"
                ? getTrendIndicator(sentimentTrend)
                : "Write to see trends"
            }
            iconContainerClassName="p-2 bg-green-500/10 rounded-lg"
          />

          <StatCard
            title="Total Entries"
            value={totalEntries}
            icon={<BarChart3 size={24} className="text-lotus-400" />}
            trend={
              avgMoodRounded > 0
                ? `Avg mood: ${avgMoodRounded}/10`
                : "No data yet"
            }
            iconContainerClassName="p-2 bg-lotus-500/10 rounded-lg"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Recent Entries */}
          <div className="lg:col-span-2 flex flex-col">
            <div className="card flex-1 flex flex-col">
              <CardHeader>
                <h2 className="text-xl font-semibold text-primary-dark">
                  Recent Entries
                </h2>
              </CardHeader>
              <div className="p-6 space-y-4 flex-1 flex flex-col">
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
                              timezone={timezone ?? "UTC"}
                            />
                          </div>
                        </div>
                        <p className="text-muted-dark text-sm line-clamp-2">
                          {entry.preview}
                        </p>
                        <Link
                          href={ROUTES.journal.detail(entry.id)}
                          className="inline-block mt-2"
                        >
                          <span className="link-lotus text-sm">
                            Read more →
                          </span>
                        </Link>
                      </div>
                    ))}
                    <Link href={ROUTES.journal.home} className="block">
                      <div className="text-center py-4 link-lotus font-medium">
                        View all entries →
                      </div>
                    </Link>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-dark mb-4">No entries yet</p>
                    <Link href={ROUTES.journal.create}>
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
          <div className="flex flex-col space-y-6">
            {/* Quick Actions */}
            <div className="card">
              <CardHeader>
                <h2 className="text-lg font-semibold text-primary-dark">
                  Quick Actions
                </h2>
              </CardHeader>
              <div className="p-6 space-y-3">
                <Link
                  href={ROUTES.journal.calendar}
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
                  href={ROUTES.profile}
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
                  href={ROUTES.profileSettings}
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
            <div className="card flex-1 flex flex-col">
              <CardHeader>
                <h2 className="text-lg font-semibold text-primary-dark">
                  Writing Stats
                </h2>
              </CardHeader>
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
