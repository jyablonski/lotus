import { useMemo } from 'react';
import { useJournalData } from './useJournalData';
import { calculateProfileStats } from '@/lib/utils/profileStats';

export function useProfileData() {
    const { journals, loading } = useJournalData();

    const profileStats = useMemo(() => {
        return calculateProfileStats(journals);
    }, [journals]);

    return {
        ...profileStats,
        loading
    };
}