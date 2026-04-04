"use client";

import { useEffect, useRef } from "react";
import { ProfileHeader } from "./ProfileHeader";
import { ProfileStats } from "./ProfileStats";
import { ProfileInsights } from "./ProfileInsights";
import { ProfileActions } from "./ProfileActions";
import { trackEvent } from "@/lib/analytics";
import type { ProfileStats as ProfileStatsType } from "@/lib/server/profile";
import type { JournalEntry } from "@/types/journal";
import { ProfileMoodChart } from "./ProfileMoodChart";
import { ProfileStreakCelebration } from "./ProfileStreakCelebration";
import { ProfileAchievements } from "./ProfileAchievements";

interface ProfilePageClientProps {
  name: string;
  email: string;
  image: string | null;
  signupDate: string;
  stats: ProfileStatsType;
  journals: JournalEntry[];
  isAdmin?: boolean;
  timezone: string;
}

export function ProfilePageClient({
  name,
  email,
  image,
  signupDate,
  stats,
  journals,
  isAdmin = false,
  timezone,
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

  // §3d: insights_viewed — fire once when the profile/insights page loads
  const hasFiredInsights = useRef(false);
  useEffect(() => {
    if (!hasFiredInsights.current) {
      hasFiredInsights.current = true;
      trackEvent("insights_viewed");
    }
  }, []);

  return (
    <div className="page-container">
      <ProfileStreakCelebration currentStreak={currentStreak} />
      <div className="content-container space-y-8">
        {/* Profile Header */}
        <ProfileHeader
          name={name}
          email={email}
          image={image}
          signupDate={signupDate}
          firstEntryDate={firstEntryDate ?? null}
          isAdmin={isAdmin}
          timezone={timezone}
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

        <ProfileMoodChart journals={journals} timezone={timezone} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProfileInsights
            averageMood={averageMood}
            mostActiveDay={mostActiveDay}
            favoriteModCategory={favoriteModCategory}
          />

          <ProfileActions isAdmin={isAdmin} />
        </div>

        <ProfileAchievements
          totalEntries={totalEntries}
          longestStreak={longestStreak}
        />
      </div>
    </div>
  );
}
