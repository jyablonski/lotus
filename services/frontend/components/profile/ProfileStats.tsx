import {
  BookOpen,
  TrendingUp,
  Flame,
  Calendar,
  Clock,
  PenTool,
} from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";

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
  totalWords,
}: ProfileStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatCard
        title="Total Entries"
        value={totalEntries}
        icon={<BookOpen size={20} className="text-lotus-400" />}
        trend={totalEntries > 0 ? "Keep writing!" : "Start your journey"}
        iconContainerClassName="p-2 bg-lotus-500/10 rounded-lg"
      />

      <StatCard
        title="This Month"
        value={thisMonth}
        icon={<Calendar size={20} className="text-green-400" />}
        trend={thisMonth > 0 ? `${thisMonth} entries` : "No entries yet"}
        trendClassName="text-green-400"
        iconContainerClassName="p-2 bg-green-500/10 rounded-lg"
      />

      <StatCard
        title="This Week"
        value={thisWeek}
        icon={<Clock size={20} className="text-lotus-400" />}
        trend={thisWeek > 0 ? `${thisWeek} entries` : "Start writing"}
        iconContainerClassName="p-2 bg-lotus-500/10 rounded-lg"
      />

      <StatCard
        title="Current Streak"
        value={`${currentStreak} days`}
        icon={<Flame size={20} className="text-orange-400" />}
        trend={currentStreak > 0 ? "Keep it up!" : "Start your streak"}
        trendClassName="text-orange-400"
        iconContainerClassName="p-2 bg-orange-500/10 rounded-lg"
      />

      <StatCard
        title="Longest Streak"
        value={`${longestStreak} days`}
        icon={<TrendingUp size={20} className="text-rose-400" />}
        trend={longestStreak > 0 ? "Personal best!" : "Not set yet"}
        trendClassName="text-rose-400"
        iconContainerClassName="p-2 bg-rose-500/10 rounded-lg"
      />

      <StatCard
        title="Total Words"
        value={totalWords.toLocaleString()}
        icon={<PenTool size={20} className="text-lotus-300" />}
        trend={totalWords > 0 ? "Keep expressing!" : "Start writing"}
        trendClassName="text-lotus-300"
        iconContainerClassName="p-2 bg-lotus-500/10 rounded-lg"
      />
    </div>
  );
}
