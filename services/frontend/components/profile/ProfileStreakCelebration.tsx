"use client";

import { useEffect } from "react";
import { toast } from "sonner";

const MILESTONE_DAYS = [7, 30, 100] as const;
const STORAGE_PREFIX = "lotus_streak_milestone_";

type ProfileStreakCelebrationProps = {
  currentStreak: number;
};

/**
 * One-time toasts when the user reaches streak milestones (persisted in localStorage).
 */
export function ProfileStreakCelebration({
  currentStreak,
}: ProfileStreakCelebrationProps) {
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    for (const m of [...MILESTONE_DAYS].sort((a, b) => b - a)) {
      if (currentStreak < m) {
        continue;
      }
      const key = `${STORAGE_PREFIX}${m}`;
      if (localStorage.getItem(key)) {
        continue;
      }
      localStorage.setItem(key, "1");
      toast.success(`You reached a ${m}-day journaling streak. Keep going!`, {
        duration: 6000,
      });
      break;
    }
  }, [currentStreak]);

  return null;
}
