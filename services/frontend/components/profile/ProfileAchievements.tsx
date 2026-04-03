"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/Card";

type ProfileAchievementsProps = {
  totalEntries: number;
  longestStreak: number;
};

export function ProfileAchievements({
  totalEntries,
  longestStreak,
}: ProfileAchievementsProps) {
  const items = [
    {
      id: "first",
      label: "First entry",
      description: "Write your first journal entry",
      unlocked: totalEntries >= 1,
    },
    {
      id: "streak7",
      label: "Week warrior",
      description: "Journal 7 days in a row (best streak)",
      unlocked: longestStreak >= 7,
    },
    {
      id: "streak30",
      label: "Monthly momentum",
      description: "Hit a 30-day streak at least once",
      unlocked: longestStreak >= 30,
    },
    {
      id: "volume50",
      label: "Dedicated writer",
      description: "50 journal entries",
      unlocked: totalEntries >= 50,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold text-dark-50">Achievements</h2>
        <p className="text-sm text-dark-400 font-normal mt-1">
          Milestones based on your history in Lotus.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className={`flex items-start justify-between gap-3 rounded-lg border px-3 py-2.5 ${
              item.unlocked
                ? "border-lotus-500/35 bg-lotus-950/15"
                : "border-dark-600 opacity-70"
            }`}
          >
            <div>
              <p className="text-sm font-medium text-dark-100">{item.label}</p>
              <p className="text-xs text-dark-400 mt-0.5">{item.description}</p>
            </div>
            <span
              className={`text-xs font-medium shrink-0 ${
                item.unlocked ? "text-lotus-300" : "text-dark-500"
              }`}
            >
              {item.unlocked ? "Unlocked" : "Locked"}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
