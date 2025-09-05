import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { moodToInt } from '@/utils/moodMapping';

export function useCreateJournal() {
    const [entry, setEntry] = useState('');
    const [mood, setMood] = useState('neutral'); // Start with neutral as default
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { data: session } = useSession();
    const router = useRouter();

    const resetForm = () => {
        setEntry('');
        setMood('neutral');
        setSuccess(false);
        setError(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!entry.trim()) {
            setError('Please write something in your journal entry.');
            return;
        }

        const userId = session?.user?.id;
        if (!userId) {
            setError('User not authenticated. Please try again.');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:8080/v1/journals', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    journal_text: entry,
                    user_mood: moodToInt(mood).toString(), // Convert to int then string for API
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} ${errorText}`);
            }

            setSuccess(true);

            setTimeout(() => {
                router.push('/journal/home');
            }, 2000);

        } catch (error) {
            console.error('Failed to submit journal entry:', error);
            setError('Something went wrong. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return {
        entry,
        setEntry,
        mood,
        setMood,
        isSubmitting,
        success,
        error,
        handleSubmit,
        resetForm
    };
}