"use client";

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
            <div className="page-container">
                <div className="content-container">
                    <div className="animate-pulse">
                        <div className="h-8 bg-dark-700 rounded w-1/3 mb-4"></div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="h-24 bg-dark-700 rounded"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const getTrendIndicator = (trend: string) => {
        switch (trend) {
            case 'Positive': return 'Good vibes';
            case 'Negative': return 'Tough times';
            default: return 'Steady';
        }
    };

    return (
        <div className="page-container">
            <div className="content-container space-y-8">

                {/* Welcome Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="heading-1">Welcome back!</h1>
                        <p className="text-muted-dark mt-1">Here&apos;s what&apos;s happening with your journal</p>
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
                                <p className="text-muted-dark text-sm">This Week</p>
                                <p className="text-2xl font-bold text-primary-dark">{entriesThisWeek}</p>
                            </div>
                            <BookOpen size={24} className="text-lotus-400" />
                        </div>
                        <p className="text-xs text-muted-dark">
                            {entriesThisWeek > 0 ? `${entriesThisWeek} entries` : 'Start writing!'}
                        </p>
                    </div>

                    <div className="card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-muted-dark text-sm">Current Streak</p>
                                <p className="text-2xl font-bold text-primary-dark">
                                    {currentStreak > 0 ? `${currentStreak}` : '0'}
                                    <span className="text-sm font-normal text-muted-dark ml-1">days</span>
                                </p>
                            </div>
                            <Flame size={24} className="text-orange-400" />
                        </div>
                        <p className="text-xs text-muted-dark">
                            {currentStreak > 0 ? 'Keep it up!' : 'Start your streak!'}
                        </p>
                    </div>

                    <div className="card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-muted-dark text-sm">Mood Trend</p>
                                <p className="text-2xl font-bold text-primary-dark">{sentimentTrend}</p>
                            </div>
                            <Smile size={24} className="text-green-400" />
                        </div>
                        <p className="text-xs text-muted-dark">
                            {sentimentTrend !== 'No Data' ? getTrendIndicator(sentimentTrend) : 'Write to see trends'}
                        </p>
                    </div>

                    <div className="card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-muted-dark text-sm">Total Entries</p>
                                <p className="text-2xl font-bold text-primary-dark">{totalEntries}</p>
                            </div>
                            <BarChart3 size={24} className="text-lotus-400" />
                        </div>
                        <p className="text-xs text-muted-dark">
                            {avgMood > 0 ? `Avg mood: ${avgMood}/10` : 'No data yet'}
                        </p>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Left Column - Recent Entries */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="card">
                            <div className="p-6 border-b border-dark-600">
                                <h2 className="text-xl font-semibold text-primary-dark">Recent Entries</h2>
                            </div>
                            <div className="p-6 space-y-4">
                                {recentEntries.length > 0 ? (
                                    <>
                                        {recentEntries.map((entry) => (
                                            <div key={entry.id} className="journal-entry">
                                                <div className="flex items-start justify-between mb-2">
                                                    <h3 className="font-medium text-primary-dark">{entry.title}</h3>
                                                    <div className="flex items-center space-x-2">
                                                        <div className={`mood-indicator mood-${entry.sentiment}`}></div>
                                                        <span className="text-xs text-muted-dark">{entry.date}</span>
                                                    </div>
                                                </div>
                                                <p className="text-muted-dark text-sm line-clamp-2">{entry.preview}</p>
                                                <Link href={`/journal/${entry.id}`} className="inline-block mt-2">
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
                                <h2 className="text-lg font-semibold text-primary-dark">Quick Actions</h2>
                            </div>
                            <div className="p-6 space-y-3">
                                <Link href="/journal/calendar" className="nav-link flex items-center space-x-3 p-3 rounded-lg">
                                    <Calendar size={20} className="text-lotus-400" />
                                    <div>
                                        <p className="font-medium text-primary-dark">View Calendar</p>
                                        <p className="text-sm text-muted-dark">See entries by date</p>
                                    </div>
                                </Link>
                                <Link href="/journal/insights" className="nav-link flex items-center space-x-3 p-3 rounded-lg">
                                    <TrendingUp size={20} className="text-green-400" />
                                    <div>
                                        <p className="font-medium text-primary-dark">Insights</p>
                                        <p className="text-sm text-muted-dark">Analyze your patterns</p>
                                    </div>
                                </Link>
                                <Link href="/profile" className="nav-link flex items-center space-x-3 p-3 rounded-lg">
                                    <User size={20} className="text-muted-dark" />
                                    <div>
                                        <p className="font-medium text-primary-dark">Settings</p>
                                        <p className="text-sm text-muted-dark">Manage your account</p>
                                    </div>
                                </Link>
                            </div>
                        </div>

                        {/* Writing Stats */}
                        <div className="card">
                            <div className="p-6 border-b border-dark-600">
                                <h2 className="text-lg font-semibold text-primary-dark">Writing Stats</h2>
                            </div>
                            <div className="p-6">
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-muted-dark">Total entries:</span>
                                        <span className="font-medium text-primary-dark">{totalEntries}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-dark">This week:</span>
                                        <span className="font-medium text-primary-dark">{entriesThisWeek}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-dark">Current streak:</span>
                                        <span className="font-medium text-primary-dark">{currentStreak} days</span>
                                    </div>
                                    {avgMood > 0 && (
                                        <div className="flex justify-between">
                                            <span className="text-muted-dark">Avg mood:</span>
                                            <span className="font-medium text-primary-dark">{avgMood}/10</span>
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