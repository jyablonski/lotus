import Link from 'next/link';
import {
    BookOpen,
    Calendar,
    TrendingUp,
    Flame,
    Smile,
    BarChart3,
    Edit3,
    User
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { QuickAction } from './QuickAction';
import { RecentEntry } from './RecentEntry';
import { useDashboardData } from '@/hooks/useDashboardData';

export const LoggedInDashboard = () => {
    const {
        entriesThisWeek,
        currentStreak,
        sentimentTrend,
        avgMood,
        recentEntries,
        loading,
        totalEntries
    } = useDashboardData();

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-24 bg-gray-200 rounded"></div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // Determine trend colors and indicators
    const getTrendColor = (trend: string) => {
        switch (trend) {
            case 'Positive': return 'green';
            case 'Negative': return 'red';
            default: return 'blue';
        }
    };

    const getTrendIndicator = (trend: string) => {
        switch (trend) {
            case 'Positive': return '↗️ Good vibes';
            case 'Negative': return '↘️ Tough times';
            default: return '→ Steady';
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

            {/* Welcome Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Welcome back!</h1>
                    <p className="text-gray-600 mt-1">Heres whats happening with your journal</p>
                </div>
                <Link href="/journal/create">
                    <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                        <Edit3 size={16} />
                        <span>New Entry</span>
                    </button>
                </Link>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="This Week"
                    value={entriesThisWeek}
                    icon={<BookOpen size={20} className="text-blue-600" />}
                    trend={entriesThisWeek > 0 ? `${entriesThisWeek} entries` : 'Start writing!'}
                    color="blue"
                />
                <StatCard
                    title="Current Streak"
                    value={currentStreak > 0 ? `${currentStreak} days` : '0 days'}
                    icon={<Flame size={20} className="text-orange-600" />}
                    trend={currentStreak > 0 ? 'Keep it up!' : 'Start your streak!'}
                    color="orange"
                />
                <StatCard
                    title="Mood Trend"
                    value={sentimentTrend}
                    icon={<Smile size={20} className="text-green-600" />}
                    trend={sentimentTrend !== 'No Data' ? getTrendIndicator(sentimentTrend) : 'Write to see trends'}
                    color={getTrendColor(sentimentTrend)}
                />
                <StatCard
                    title="Total Entries"
                    value={totalEntries}
                    icon={<BarChart3 size={20} className="text-purple-600" />}
                    trend={avgMood > 0 ? `Avg mood: ${avgMood}/10` : 'No data yet'}
                    color="purple"
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left Column - Recent Entries */}
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardHeader>
                            <h2 className="text-xl font-semibold text-gray-900">Recent Entries</h2>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {recentEntries.length > 0 ? (
                                <>
                                    {recentEntries.map((entry) => (
                                        <RecentEntry
                                            key={entry.id}
                                            title={entry.title}
                                            date={entry.date}
                                            preview={entry.preview}
                                            sentiment={entry.sentiment}
                                            href={`/journal/${entry.id}`}
                                        />
                                    ))}
                                    <Link href="/journal/home" className="block">
                                        <div className="text-center py-4 text-blue-600 hover:text-blue-800 font-medium">
                                            View all entries →
                                        </div>
                                    </Link>
                                </>
                            ) : (
                                <div className="text-center py-8">
                                    <p className="text-gray-500 mb-4">No entries yet</p>
                                    <Link href="/journal/create">
                                        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                                            Create Your First Entry
                                        </button>
                                    </Link>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column - Quick Actions & Insights */}
                <div className="space-y-6">

                    {/* Quick Actions */}
                    <Card>
                        <CardHeader>
                            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <QuickAction
                                title="View Calendar"
                                href="/journal/calendar"
                                icon={<Calendar size={20} className="text-blue-600" />}
                                description="See entries by date"
                            />
                            <QuickAction
                                title="Insights"
                                href="/journal/insights"
                                icon={<TrendingUp size={20} className="text-green-600" />}
                                description="Analyze your patterns"
                            />
                            <QuickAction
                                title="Settings"
                                href="/profile"
                                icon={<User size={20} className="text-gray-600" />}
                                description="Manage your account"
                            />
                        </CardContent>
                    </Card>

                    {/* Writing Stats */}
                    <Card>
                        <CardHeader>
                            <h2 className="text-lg font-semibold text-gray-900">Writing Stats</h2>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Total entries:</span>
                                    <span className="font-medium">{totalEntries}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">This week:</span>
                                    <span className="font-medium">{entriesThisWeek}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Current streak:</span>
                                    <span className="font-medium">{currentStreak} days</span>
                                </div>
                                {avgMood > 0 && (
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Avg mood:</span>
                                        <span className="font-medium">{avgMood}/10</span>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};