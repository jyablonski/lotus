export interface MoodConfig {
    value: number;
    label: string;
    emoji: string;
    color: string;
}

export const MOOD_CONFIGS: Record<string, MoodConfig> = {
    excited: { value: 8, label: 'Excited', emoji: '🤩', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
    happy: { value: 7, label: 'Happy', emoji: '😊', color: 'bg-green-100 text-green-800 border-green-300' },
    content: { value: 6, label: 'Content', emoji: '😌', color: 'bg-blue-100 text-blue-800 border-blue-300' },
    neutral: { value: 5, label: 'Neutral', emoji: '😐', color: 'bg-gray-100 text-gray-800 border-gray-300' },
    tired: { value: 4, label: 'Tired', emoji: '😴', color: 'bg-purple-100 text-purple-800 border-purple-300' },
    sad: { value: 3, label: 'Sad', emoji: '😢', color: 'bg-blue-100 text-blue-800 border-blue-300' },
    anxious: { value: 2, label: 'Anxious', emoji: '😰', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
    angry: { value: 1, label: 'Angry', emoji: '😠', color: 'bg-red-100 text-red-800 border-red-300' },
};

// Convert string mood to integer for API
export function moodToInt(moodKey: string): number {
    return MOOD_CONFIGS[moodKey]?.value || 5; // Default to neutral
}

// Convert integer mood to string for frontend
export function intToMood(moodInt: number): string {
    const moodEntry = Object.entries(MOOD_CONFIGS).find(([, config]) => config.value === moodInt);
    return moodEntry?.[0] || 'neutral'; // Default to neutral
}

// Get mood config by string key
export function getMoodConfig(moodKey: string): MoodConfig {
    return MOOD_CONFIGS[moodKey] || MOOD_CONFIGS.neutral;
}

// Get mood config by integer value
export function getMoodConfigByInt(moodInt: number): MoodConfig {
    const moodKey = intToMood(moodInt);
    return getMoodConfig(moodKey);
}

// Get all mood options for selectors
export function getAllMoodOptions() {
    return Object.entries(MOOD_CONFIGS).map(([key, config]) => ({
        key,
        ...config
    }));
}