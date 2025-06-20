'use client';

import { useEffect, useState } from 'react';
import { useSession } from "next-auth/react";

import { JournalEntryCard } from '@/components/JournalEntryCard';


type JournalEntry = {
    journalId: string;
    userId: string;
    journalText: string;
    userMood: string;
    createdAt: string; // ISO 8601 (RFC3339) timestamp
};

export default function JournalPage() {
    const { data: session } = useSession();
    const [journals, setJournals] = useState<JournalEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!session?.user?.id) return; // Wait for session to be ready

        async function fetchJournals() {
            console.log('Fetching journals for user:', session.user.id);
            try {
                const res = await fetch(`http://localhost:8080/v1/journals?user_id=${session.user.id}`);
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
    }, [session]); // <- rerun when session updates

    if (loading) return <p>Loading journals...</p>;

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <h1 className="text-2xl font-semibold mb-6 text-center">My Journal Entries</h1>

            {journals.length === 0 ? (
                <p>No journal entries found.</p>
            ) : (
                <ul className="space-y-4">
                    {journals.map((entry) => (
                        <JournalEntryCard key={entry.journalId} entry={entry} />
                    ))}
                </ul>
            )}
        </div>
    );
}
