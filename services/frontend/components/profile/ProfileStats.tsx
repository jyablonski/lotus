import { BookOpen, TrendingUp, Flame, Calendar, Clock, PenTool } from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';

interface ProfileStatsProps {
    totalEntries: number;
    thisMonth: number;
    thisWeek: number;
    currentStreak: number;
    longestStreak: number;
    totalWords: number;
}

export function ProfileStats({
    totalEntries,
    thisMonth,
    thisWeek,
    currentStreak,
    longestStreak,
    totalWords
}: ProfileStatsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard
                title="Total Entries"
                value={totalEntries}
                icon={<BookOpen size={20} className="text-blue-600" />}
                trend={totalEntries > 0 ? 'Keep writing!' : 'Start your journey'}
                color="blue"
            />

            <StatCard
                title="This Month"
                value={thisMonth}
                icon={<Calendar size={20} className="text-green-600" />}
                trend={thisMonth > 0 ? `${thisMonth} entries` : 'No entries yet'}
                color="green"
            />

            <StatCard
                title="This Week"
                value={thisWeek}
                icon={<Clock size={20} className="text-purple-600" />}
                trend={thisWeek > 0 ? `${thisWeek} entries` : 'Start writing'}
                color="purple"
            />

            <StatCard
                title="Current Streak"
                value={`${currentStreak} days`}
                icon={<Flame size={20} className="text-orange-600" />}
                trend={currentStreak > 0 ? 'Keep it up!' : 'Start your streak'}
                color="orange"
            />

            <StatCard
                title="Longest Streak"
                value={`${longestStreak} days`}
                icon={<TrendingUp size={20} className="text-red-600" />}
                trend={longestStreak > 0 ? 'Personal best!' : 'Not set yet'}
                color="red"
            />

            <StatCard
                title="Total Words"
                value={totalWords.toLocaleString()}
                icon={<PenTool size={20} className="text-indigo-600" />}
                trend={totalWords > 0 ? 'Keep expressing!' : 'Start writing'}
                color="indigo"
            />
        </div>
    );
}