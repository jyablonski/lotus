import { intToMood, getMoodConfigByInt } from '@/utils/moodMapping';

export type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string; // integer as string
    createdAt: string;
};

export type MoodOption = {
    key: string;
    label: string;
    emoji: string;
};

export function filterJournalsBySearch(journals: JournalEntry[], searchTerm: string): JournalEntry[] {
    if (!searchTerm.trim()) return journals;

    return journals.filter(journal =>
        journal.journalText.toLowerCase().includes(searchTerm.toLowerCase())
    );
}

export function filterJournalsByMood(journals: JournalEntry[], selectedMood: string): JournalEntry[] {
    if (selectedMood === 'all') return journals;

    return journals.filter(journal => {
        const journalMoodKey = intToMood(parseInt(journal.userMood));
        return journalMoodKey === selectedMood;
    });
}

export function filterJournals(
    journals: JournalEntry[],
    searchTerm: string,
    selectedMood: string
): JournalEntry[] {
    let filtered = journals;

    // Apply search filter
    filtered = filterJournalsBySearch(filtered, searchTerm);

    // Apply mood filter
    filtered = filterJournalsByMood(filtered, selectedMood);

    return filtered;
}

export function getUniqueMoodsFromJournals(journals: JournalEntry[]): MoodOption[] {
    const moodInts = Array.from(new Set(journals.map(j => parseInt(j.userMood))));

    return moodInts.map(moodInt => {
        const moodKey = intToMood(moodInt);
        const config = getMoodConfigByInt(moodInt);
        return {
            key: moodKey,
            label: config.label,
            emoji: config.emoji
        };
    }).sort((a, b) => a.label.localeCompare(b.label)); // Sort alphabetically
}