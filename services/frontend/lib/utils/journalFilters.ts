import { JournalEntry } from "@/types/journal";
import { type MoodOption } from "@/lib/utils/moodMapping";

export type { MoodOption };

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
 * Filter journals by mood (1-10 scale).
 */
export function filterJournalsByMood(
  journals: JournalEntry[],
  selectedMood: string,
): JournalEntry[] {
  if (selectedMood === "all") return journals;

  const moodNum = parseInt(selectedMood, 10);
  if (Number.isNaN(moodNum)) return journals;

  return journals.filter((journal) => journal.userMood === moodNum);
}

/**
 * Filter journals by topic tag (entry must have the selected topic in topicNames).
 */
export function filterJournalsByTag(
  journals: JournalEntry[],
  selectedTag: string,
): JournalEntry[] {
  if (selectedTag === "all") return journals;

  return journals.filter(
    (journal) => journal.topicNames?.includes(selectedTag) ?? false,
  );
}

export function filterJournals(
  journals: JournalEntry[],
  searchTerm: string,
  selectedMood: string,
  selectedTag: string = "all",
): JournalEntry[] {
  let filtered = journals;

  // Apply search filter
  filtered = filterJournalsBySearch(filtered, searchTerm);

  // Apply mood filter
  filtered = filterJournalsByMood(filtered, selectedMood);

  // Apply tag filter
  filtered = filterJournalsByTag(filtered, selectedTag);

  return filtered;
}

/**
 * Get unique topic names from journals (for tag filter dropdown).
 * Returns sorted array of tag strings; use as-is for filtering (e.g. with underscores).
 */
export function getUniqueTagsFromJournals(journals: JournalEntry[]): string[] {
  const set = new Set<string>();
  for (const j of journals) {
    for (const tag of j.topicNames ?? []) {
      set.add(tag);
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b));
}

export function getUniqueMoodsFromJournals(
  journals: JournalEntry[],
): MoodOption[] {
  const moodInts = Array.from(new Set(journals.map((j) => j.userMood)));

  return moodInts
    .map((n) => ({ key: String(n), label: String(n) }))
    .sort((a, b) => Number(a.key) - Number(b.key));
}
