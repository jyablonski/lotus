import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import { getMoodConfigByInt } from "@/lib/utils/moodMapping";

interface ProfileInsightsProps {
  averageMood: number;
  mostActiveDay: string;
  favoriteModCategory: string;
}

export function ProfileInsights({
  averageMood,
  mostActiveDay,
  favoriteModCategory,
}: ProfileInsightsProps) {
  const moodConfig = getMoodConfigByInt(Math.round(averageMood));

  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold text-dark-50">Your Insights</h2>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Average Mood */}
        <div className="insight-row">
          <div>
            <p className="text-sm font-medium text-dark-400">Average Mood</p>
            <p className="text-lg font-semibold text-dark-50">
              {averageMood > 0 ? `${averageMood}/8` : "No data"}
            </p>
          </div>
          {averageMood > 0 && (
            <div className="text-right">
              <div className="text-2xl">{moodConfig.emoji}</div>
              <p className="text-sm text-dark-400">{moodConfig.label}</p>
            </div>
          )}
        </div>

        {/* Most Active Day */}
        <div className="insight-row">
          <div>
            <p className="text-sm font-medium text-dark-400">Most Active Day</p>
            <p className="text-lg font-semibold text-dark-50">
              {mostActiveDay}
            </p>
          </div>
          <div className="text-2xl">📅</div>
        </div>

        {/* Favorite Mood Category */}
        <div className="insight-row">
          <div>
            <p className="text-sm font-medium text-dark-400">
              Most Common Mood
            </p>
            <p className="text-lg font-semibold text-dark-50">
              {favoriteModCategory}
            </p>
          </div>
          <div className="text-2xl">
            {favoriteModCategory === "Positive"
              ? "😊"
              : favoriteModCategory === "Negative"
                ? "😔"
                : "😐"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
