'use client';

import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ProfileHeader } from './ProfileHeader';
import { ProfileStats } from './ProfileStats';
import { ProfileInsights } from './ProfileInsights';
import { ProfileActions } from './ProfileActions';
import { useProfileData } from '@/hooks/useProfileData';

interface ProfilePageClientProps {
    name: string;
    email: string;
    image: string | null; // Add this line
    signupDate: string;
}

export function ProfilePageClient({ name, email, image, signupDate }: ProfilePageClientProps) {
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
        loading
    } = useProfileData();

    if (loading) return <LoadingSpinner />;

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

            {/* Profile Header */}
            <ProfileHeader
                name={name}
                email={email}
                image={image} // Pass image to header
                signupDate={signupDate}
                firstEntryDate={firstEntryDate}
            />

            {/* Rest of your component remains the same */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Journal Statistics</h2>
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
    );
}