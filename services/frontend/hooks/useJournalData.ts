import { useEffect, useState, useCallback } from 'react';
import { useSession } from "next-auth/react";
import {
    fetchJournalsByUserId,
    fetchMoreJournals,
    type JournalEntry,
    type FetchJournalsParams
} from '@/lib/api/journals';

interface UseJournalDataOptions {
    initialLimit?: number;
    autoLoad?: boolean;
}

interface UseJournalDataReturn {
    journals: JournalEntry[];
    loading: boolean;
    loadingMore: boolean;
    error: string | null;
    totalCount: number;
    hasMore: boolean;
    loadMore: () => Promise<void>;
    refresh: () => Promise<void>;
    loadInitial: (params?: Partial<FetchJournalsParams>) => Promise<void>;
}

export function useJournalData(options: UseJournalDataOptions = {}): UseJournalDataReturn {
    const { initialLimit = 10, autoLoad = true } = options;
    const { data: session } = useSession();

    const [journals, setJournals] = useState<JournalEntry[]>([]);
    const [loading, setLoading] = useState(autoLoad);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [totalCount, setTotalCount] = useState(0);
    const [hasMore, setHasMore] = useState(true);

    const loadInitial = useCallback(async (params?: Partial<FetchJournalsParams>) => {
        const userId = session?.user?.id;
        if (!userId) return;

        setLoading(true);
        setError(null);

        try {
            console.log('Fetching initial journals for user:', userId);
            const response = await fetchJournalsByUserId({
                userId,
                limit: initialLimit,
                offset: 0,
                ...params,
            });

            setJournals(response.journals);
            setTotalCount(response.totalCount);
            setHasMore(response.hasMore);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch journals';
            console.error('Error fetching journals:', errorMessage);
            setError(errorMessage);
            setJournals([]);
        } finally {
            setLoading(false);
        }
    }, [session?.user?.id, initialLimit]);

    const loadMore = useCallback(async () => {
        const userId = session?.user?.id;
        if (!userId || loadingMore || !hasMore) return;

        setLoadingMore(true);
        setError(null);

        try {
            console.log('Loading more journals, current count:', journals.length);
            const response = await fetchMoreJournals({
                userId,
                currentJournals: journals,
                limit: initialLimit,
            });

            setJournals(prev => [...prev, ...response.journals]);
            setHasMore(response.hasMore);
            setTotalCount(response.totalCount);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to load more journals';
            console.error('Error loading more journals:', errorMessage);
            setError(errorMessage);
        } finally {
            setLoadingMore(false);
        }
    }, [session?.user?.id, journals, loadingMore, hasMore, initialLimit]);

    const refresh = useCallback(async () => {
        await loadInitial();
    }, [loadInitial]);

    // Auto-load initial data when session is available
    useEffect(() => {
        if (autoLoad && session?.user?.id) {
            loadInitial();
        }
    }, [session?.user?.id, autoLoad, loadInitial]);

    return {
        journals,
        loading,
        loadingMore,
        error,
        totalCount,
        hasMore,
        loadMore,
        refresh,
        loadInitial,
    };
}

// Alternative hook for simpler use cases (backwards compatible)
export function useJournalDataSimple() {
    const { journals, loading, error } = useJournalData({
        initialLimit: 1000, // Load "all" entries
        autoLoad: true
    });

    return { journals, loading, error };
}