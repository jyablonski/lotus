import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { getMoodConfigByInt } from '@/utils/moodMapping';

interface ProfileInsightsProps {
    averageMood: number;
    mostActiveDay: string;
    favoriteModCategory: string;
}

export function ProfileInsights({ averageMood, mostActiveDay, favoriteModCategory }: ProfileInsightsProps) {
    const moodConfig = getMoodConfigByInt(Math.round(averageMood));

    return (
        <Card>
            <CardHeader>
                <h2 className="text-xl font-semibold text-gray-900">Your Insights</h2>
            </CardHeader>
            <CardContent className="space-y-6">

                {/* Average Mood */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                        <p className="text-sm font-medium text-gray-600">Average Mood</p>
                        <p className="text-lg font-semibold text-gray-900">
                            {averageMood > 0 ? `${averageMood}/10` : 'No data'}
                        </p>
                    </div>
                    {averageMood > 0 && (
                        <div className="text-right">
                            <div className="text-2xl">{moodConfig.emoji}</div>
                            <p className="text-sm text-gray-600">{moodConfig.label}</p>
                        </div>
                    )}
                </div>

                {/* Most Active Day */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                        <p className="text-sm font-medium text-gray-600">Most Active Day</p>
                        <p className="text-lg font-semibold text-gray-900">{mostActiveDay}</p>
                    </div>
                    <div className="text-2xl">📅</div>
                </div>

                {/* Favorite Mood Category */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                        <p className="text-sm font-medium text-gray-600">Most Common Mood</p>
                        <p className="text-lg font-semibold text-gray-900">{favoriteModCategory}</p>
                    </div>
                    <div className="text-2xl">
                        {favoriteModCategory === 'Positive' ? '😊' :
                            favoriteModCategory === 'Negative' ? '😔' : '😐'}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}