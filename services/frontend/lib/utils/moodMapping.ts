/**
 * Mood is a simple 1-10 scale (no emoji). Used for create form, filters, and display.
 */

export const MOOD_MIN = 1;
export const MOOD_MAX = 10;
export const MOOD_DEFAULT = 5;

export type MoodOption = {
  key: string;
  label: string;
};

/** Clamp value to valid mood range. */
export function clampMood(value: number): number {
  if (Number.isNaN(value)) return MOOD_DEFAULT;
  return Math.max(MOOD_MIN, Math.min(MOOD_MAX, Math.round(value)));
}

/** Convert mood number to string key (for filter dropdown). */
export function intToMood(moodInt: number): string {
  const n = clampMood(moodInt);
  return String(n);
}

/** Get display label and optional color for a mood value (e.g. for JournalEntryCard badge). */
export function getMoodConfigByInt(moodInt: number): {
  label: string;
  color: string;
} {
  const n = clampMood(moodInt);
  // Simple color scale: low = red, mid = yellow, high = green
  const color =
    n >= 7
      ? "bg-green-500/20 text-green-300 border-green-500/30"
      : n >= 4
        ? "bg-dark-500/20 text-dark-300 border-dark-500/30"
        : "bg-red-500/20 text-red-300 border-red-500/30";
  return { label: String(n), color };
}

/** All mood options for filter dropdown (1-10). */
export function getAllMoodOptions(): MoodOption[] {
  return Array.from({ length: MOOD_MAX - MOOD_MIN + 1 }, (_, i) => {
    const n = MOOD_MIN + i;
    return { key: String(n), label: String(n) };
  });
}
