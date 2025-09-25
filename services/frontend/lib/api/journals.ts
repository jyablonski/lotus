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

// New pagination interfaces
export interface PaginationParams {
    limit?: number;
    offset?: number;
}

export interface JournalsResponse {
    journals: JournalEntry[];
    totalCount: number;
    hasMore: boolean;
}

export interface FetchJournalsParams extends PaginationParams {
    userId: string;
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

// Updated function with pagination support
export async function fetchJournalsByUserId({
    userId,
    limit = 10,
    offset = 0
}: FetchJournalsParams): Promise<JournalsResponse> {
    const params = new URLSearchParams({
        user_id: userId,
        limit: limit.toString(),
        offset: offset.toString(),
    });

    const response = await fetch(`http://localhost:8080/v1/journals?${params}`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data: {
        journals: JournalEntry[];
        totalCount: string; // Backend returns as string
        hasMore: boolean;   // Backend uses camelCase
    } = await response.json();

    return {
        journals: data.journals, // Backend already sorts by created_at DESC
        totalCount: parseInt(data.totalCount), // Convert string to number
        hasMore: data.hasMore,
    };
}

// Legacy function for backwards compatibility (if needed)
export async function fetchAllJournalsByUserId(userId: string): Promise<JournalEntry[]> {
    const response = await fetchJournalsByUserId({
        userId,
        limit: 1000 // Large number to get "all" results
    });
    return response.journals;
}

// Helper function for infinite scroll/load more scenarios
export async function fetchMoreJournals({
    userId,
    currentJournals,
    limit = 10
}: {
    userId: string;
    currentJournals: JournalEntry[];
    limit?: number;
}): Promise<JournalsResponse> {
    return fetchJournalsByUserId({
        userId,
        limit,
        offset: currentJournals.length,
    });
}