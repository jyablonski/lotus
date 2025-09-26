export type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export interface CreateJournalParams {
    entry: string;
    mood: string;
}

export interface PaginationParams {
    limit?: number;
    offset?: number;
}

export interface JournalsResponse {
    journals: JournalEntry[];
    totalCount: number;
    hasMore: boolean;
}

// Updated function - now calls Next.js API instead of Go backend directly
export async function fetchJournalsByUserId({
    limit = 10,
    offset = 0
}: PaginationParams): Promise<JournalsResponse> {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
    });

    // Now calls Next.js API route instead of Go backend directly
    const response = await fetch(`/api/journals?${params}`);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error: ${response.status} ${errorText}`);
    }

    const data: {
        journals: JournalEntry[];
        totalCount: string;
        hasMore: boolean;
    } = await response.json();

    return {
        journals: data.journals,
        totalCount: parseInt(data.totalCount),
        hasMore: data.hasMore,
    };
}

// Updated function - now calls Next.js API
export async function createJournalEntry({ entry, mood }: CreateJournalParams) {
    const response = await fetch('/api/journals', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            journal_text: entry,
            user_mood: mood,
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error: ${response.status} ${errorText}`);
    }

    return response.json();
}

// Helper function for load more functionality
export async function fetchMoreJournals({
    currentJournals,
    limit = 10
}: {
    currentJournals: JournalEntry[];
    limit?: number;
}): Promise<JournalsResponse> {
    return fetchJournalsByUserId({
        limit,
        offset: currentJournals.length,
    });
}

// Legacy function for backwards compatibility (if needed)
export async function fetchAllJournalsByUserId(): Promise<JournalEntry[]> {
    const response = await fetchJournalsByUserId({
        limit: 1000 // Large number to get "all" results
    });
    return response.journals;
}