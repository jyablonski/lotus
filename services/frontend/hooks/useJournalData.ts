import { useEffect, useState } from 'react';
import { useSession } from "next-auth/react";

type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string;
};

export function useJournalData() {
    const { data: session } = useSession();
    const [journals, setJournals] = useState<JournalEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const userId = session?.user?.id;
        if (!userId) return;

        async function fetchJournals() {
            console.log('Fetching journals for user:', userId);
            try {
                const res = await fetch(`http://localhost:8080/v1/journals?user_id=${userId}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);

                const data: { journals: JournalEntry[] } = await res.json();
                const sorted = data.journals.sort(
                    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
                );
                setJournals(sorted);
            } catch (e) {
                console.error('Error fetching journals:', e);
                setJournals([]);
            } finally {
                setLoading(false);
            }
        }

        fetchJournals();
    }, [session]);

    return { journals, loading };
}