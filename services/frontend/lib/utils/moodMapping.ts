export interface MoodConfig {
  value: number;
  label: string;
  emoji: string;
  color: string;
}

export const MOOD_CONFIGS: Record<string, MoodConfig> = {
  excited: {
    value: 8,
    label: "Excited",
    emoji: "🤩",
    color: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  },
  happy: {
    value: 7,
    label: "Happy",
    emoji: "😊",
    color: "bg-green-500/20 text-green-300 border-green-500/30",
  },
  content: {
    value: 6,
    label: "Content",
    emoji: "😌",
    color: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  },
  neutral: {
    value: 5,
    label: "Neutral",
    emoji: "😐",
    color: "bg-dark-500/20 text-dark-300 border-dark-500/30",
  },
  tired: {
    value: 4,
    label: "Tired",
    emoji: "😴",
    color: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  },
  sad: {
    value: 3,
    label: "Sad",
    emoji: "😢",
    color: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  },
  anxious: {
    value: 2,
    label: "Anxious",
    emoji: "😰",
    color: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  },
  angry: {
    value: 1,
    label: "Angry",
    emoji: "😠",
    color: "bg-red-500/20 text-red-300 border-red-500/30",
  },
};

// Convert string mood to integer for API
export function moodToInt(moodKey: string): number {
  return MOOD_CONFIGS[moodKey]?.value || 5; // Default to neutral
}

// Convert integer mood to string for frontend
export function intToMood(moodInt: number): string {
  const moodEntry = Object.entries(MOOD_CONFIGS).find(
    ([, config]) => config.value === moodInt,
  );
  return moodEntry?.[0] || "neutral"; // Default to neutral
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
    ...config,
  }));
}
