import { JournalEntry } from "@/types/journal";
import { intToMood, getMoodConfigByInt } from "@/utils/moodMapping";

export type MoodOption = {
  key: string;
  label: string;
  emoji: string;
};

export function filterJournalsBySearch(
  journals: JournalEntry[],
  searchTerm: string,
): JournalEntry[] {
  if (!searchTerm.trim()) return journals;

  return journals.filter((journal) =>
    journal.journalText.toLowerCase().includes(searchTerm.toLowerCase()),
  );
}

/**
 * Filter journals by mood
 * Mood scores: excited=8, happy=7, content=6, neutral=5, tired=4, sad=3, anxious=2, angry=1
 */
export function filterJournalsByMood(
  journals: JournalEntry[],
  selectedMood: string,
): JournalEntry[] {
  if (selectedMood === "all") return journals;

  return journals.filter((journal) => {
    // userMood is already a number, no need to parseInt
    const journalMoodKey = intToMood(journal.userMood);
    return journalMoodKey === selectedMood;
  });
}

export function filterJournals(
  journals: JournalEntry[],
  searchTerm: string,
  selectedMood: string,
): JournalEntry[] {
  let filtered = journals;

  // Apply search filter
  filtered = filterJournalsBySearch(filtered, searchTerm);

  // Apply mood filter
  filtered = filterJournalsByMood(filtered, selectedMood);

  return filtered;
}

export function getUniqueMoodsFromJournals(
  journals: JournalEntry[],
): MoodOption[] {
  // userMood is already a number, no need to parseInt
  const moodInts = Array.from(new Set(journals.map((j) => j.userMood)));

  return moodInts
    .map((moodInt) => {
      const moodKey = intToMood(moodInt);
      const config = getMoodConfigByInt(moodInt);
      return {
        key: moodKey,
        label: config.label,
        emoji: config.emoji,
      };
    })
    .sort((a, b) => a.label.localeCompare(b.label)); // Sort alphabetically
}
