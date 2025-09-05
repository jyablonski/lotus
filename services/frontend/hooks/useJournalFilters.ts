import { useState, useMemo } from 'react';
import { intToMood, getMoodConfigByInt } from '@/utils/moodMapping';

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string; // integer as string
    createdAt: string;
};

export function useJournalFilters(journals: JournalEntry[]) {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedMood, setSelectedMood] = useState<string>('all');

    const filteredJournals = useMemo(() => {
        return journals.filter(journal => {
            const matchesSearch = journal.journalText.toLowerCase().includes(searchTerm.toLowerCase());

            let matchesMood = true;
            if (selectedMood !== 'all') {
                const journalMoodKey = intToMood(parseInt(journal.userMood));
                matchesMood = journalMoodKey === selectedMood;
            }

            return matchesSearch && matchesMood;
        });
    }, [journals, searchTerm, selectedMood]);

    // Get unique moods for filter (converted to readable names)
    const uniqueMoods = useMemo(() => {
        const moodInts = Array.from(new Set(journals.map(j => parseInt(j.userMood))));
        return moodInts.map(moodInt => {
            const moodKey = intToMood(moodInt);
            const config = getMoodConfigByInt(moodInt);
            return {
                key: moodKey,
                label: config.label,
                emoji: config.emoji
            };
        });
    }, [journals]);

    return {
        searchTerm,
        setSearchTerm,
        selectedMood,
        setSelectedMood,
        filteredJournals,
        uniqueMoods
    };
}
