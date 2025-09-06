import { moodToInt } from '@/utils/moodMapping';

export type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export interface CreateJournalParams {
    userId: string;
    entry: string;
    mood: string;
}

export async function createJournalEntry({ userId, entry, mood }: CreateJournalParams) {
    const response = await fetch('http://localhost:8080/v1/journals', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId,
            journal_text: entry,
            user_mood: moodToInt(mood).toString(),
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${response.status} ${errorText}`);
    }

    return response.json();
}

export async function fetchJournalsByUserId(userId: string): Promise<JournalEntry[]> {
    const response = await fetch(`http://localhost:8080/v1/journals?user_id=${userId}`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data: { journals: JournalEntry[] } = await response.json();

    // Sort by creation date (newest first)
    return data.journals.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
}