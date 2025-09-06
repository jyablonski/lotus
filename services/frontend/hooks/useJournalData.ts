import { useEffect, useState } from 'react';
import { useSession } from "next-auth/react";
import { fetchJournalsByUserId, type JournalEntry } from '@/lib/api/journals';

export function useJournalData() {
    const { data: session } = useSession();
    const [journals, setJournals] = useState<JournalEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const userId = session?.user?.id;
        if (!userId) return;

        async function loadJournals() {
            console.log('Fetching journals for user:', userId);
            try {
                const sortedJournals = await fetchJournalsByUserId(userId);
                setJournals(sortedJournals);
            } catch (error) {
                console.error('Error fetching journals:', error);
                setJournals([]);
            } finally {
                setLoading(false);
            }
        }

        loadJournals();
    }, [session]);

    return { journals, loading };
}