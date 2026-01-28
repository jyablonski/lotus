"use client";

import { ProfileHeader } from "./ProfileHeader";
import { ProfileStats } from "./ProfileStats";
import { ProfileInsights } from "./ProfileInsights";
import { ProfileActions } from "./ProfileActions";
import type { ProfileStats as ProfileStatsType } from "@/lib/server/profile";

interface ProfilePageClientProps {
  name: string;
  email: string;
  image: string | null;
  signupDate: string;
  stats: ProfileStatsType;
}

export function ProfilePageClient({
  name,
  email,
  image,
  signupDate,
  stats,
}: ProfilePageClientProps) {
  const {
    totalEntries,
    thisMonth,
    thisWeek,
    averageMood,
    currentStreak,
    longestStreak,
    mostActiveDay,
    firstEntryDate,
    favoriteModCategory,
    totalWords,
  } = stats;

  return (
    <div className="page-container">
      <div className="content-container space-y-8">
        {/* Profile Header */}
        <ProfileHeader
          name={name}
          email={email}
          image={image}
          signupDate={signupDate}
          firstEntryDate={firstEntryDate ? new Date(firstEntryDate) : null}
        />

        {/* Statistics Section */}
        <div>
          <h2 className="heading-2 mb-6">Your Journal Statistics</h2>
          <ProfileStats
            totalEntries={totalEntries}
            thisMonth={thisMonth}
            thisWeek={thisWeek}
            currentStreak={currentStreak}
            longestStreak={longestStreak}
            totalWords={totalWords}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProfileInsights
            averageMood={averageMood}
            mostActiveDay={mostActiveDay}
            favoriteModCategory={favoriteModCategory}
          />

          <ProfileActions />
        </div>
      </div>
    </div>
  );
}
