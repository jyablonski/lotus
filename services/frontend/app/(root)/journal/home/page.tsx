'use client';

import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { JournalHeader } from '@/components/journal/JournalHeader';
import { JournalFilters } from '@/components/journal/JournalFilters';
import { JournalEmptyState } from '@/components/journal/JournalEmptyState';
import { JournalList } from '@/components/journal/JournalList';
import { useJournalData } from '@/hooks/useJournalData';
import { useJournalFilters } from '@/hooks/useJournalFilters';

export default function JournalHomePage() {
    const { journals, loading } = useJournalData();
    const {
        searchTerm,
        setSearchTerm,
        selectedMood,
        setSelectedMood,
        filteredJournals,
        uniqueMoods
    } = useJournalFilters(journals);

    if (loading) return <LoadingSpinner />;

    return (
        <div className="page-container">
            <div className="content-container">
                <JournalHeader totalEntries={journals.length} />

                <JournalFilters
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                    selectedMood={selectedMood}
                    setSelectedMood={setSelectedMood}
                    uniqueMoods={uniqueMoods}
                    totalEntries={journals.length}
                    filteredCount={filteredJournals.length}
                />

                {filteredJournals.length === 0 ? (
                    <JournalEmptyState hasEntries={journals.length > 0} />
                ) : (
                    <JournalList entries={filteredJournals} />
                )}
            </div>
        </div>
    );
}