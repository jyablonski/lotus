'use client';

import { useState, useEffect } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { JournalHeader } from '@/components/journal/JournalHeader';
import { JournalFilters } from '@/components/journal/JournalFilters';
import { JournalEmptyState } from '@/components/journal/JournalEmptyState';
import { JournalList } from '@/components/journal/JournalList';
import { JournalPagination } from '@/components/journal/JournalPagination';
import { useJournalData } from '@/hooks/useJournalData';
import { useJournalFilters } from '@/hooks/useJournalFilters';

export default function JournalHomePage() {
    const [currentPage, setCurrentPage] = useState(1);
    const [hasFilters, setHasFilters] = useState(false);
    const itemsPerPage = 10;

    // Load paginated data from backend
    const { 
        journals: paginatedJournals, 
        loading: paginatedLoading,
        totalCount: backendTotalCount,
        loadInitial,
        error
    } = useJournalData({ 
        initialLimit: itemsPerPage,
        autoLoad: true 
    });

    // Load ALL journals for filtering (only when filters are active)
    const { 
        journals: allJournals, 
        loading: allJournalsLoading 
    } = useJournalData({ 
        initialLimit: 1000, // Large number to get all
        autoLoad: false  // Don't auto-load, we'll trigger manually
    });

    // Set up filters - use available journals for unique moods
    const journalsForFilters = allJournals.length > 0 ? allJournals : paginatedJournals;
    const {
        searchTerm,
        setSearchTerm,
        selectedMood,
        setSelectedMood,
        filteredJournals,
        uniqueMoods,
        clearFilters,
        hasActiveFilters
    } = useJournalFilters(journalsForFilters);

    // Track if we have active filters
    useEffect(() => {
        setHasFilters(hasActiveFilters);
        if (hasActiveFilters) {
            setCurrentPage(1); // Reset to page 1 when filters change
        }
    }, [hasActiveFilters]);

    // When filters become active, load all journals
    useEffect(() => {
        if (hasActiveFilters && allJournals.length === 0) {
            loadInitial({ limit: 1000 });
        }
    }, [hasActiveFilters, allJournals.length, loadInitial]);

    // Handle page changes for backend pagination
    const handlePageChange = async (page: number) => {
        if (hasFilters) {
            // Client-side pagination for filtered results
            setCurrentPage(page);
        } else {
            // Backend pagination for unfiltered results
            setCurrentPage(page);
            const offset = (page - 1) * itemsPerPage;
            await loadInitial({ limit: itemsPerPage, offset });
        }
    };

    // Clear filters and return to backend pagination
    const handleClearFilters = () => {
        clearFilters();
        setCurrentPage(1);
        // Reload first page from backend
        loadInitial({ limit: itemsPerPage, offset: 0 });
    };

    // Determine what data to show
    const getDisplayData = () => {
        if (hasFilters) {
            // Client-side pagination of filtered results
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            return {
                journals: filteredJournals.slice(startIndex, endIndex),
                totalCount: filteredJournals.length,
                loading: allJournalsLoading
            };
        } else {
            // Backend pagination of all results
            return {
                journals: paginatedJournals,
                totalCount: backendTotalCount,
                loading: paginatedLoading
            };
        }
    };

    const { journals: displayJournals, totalCount, loading } = getDisplayData();
    const totalPages = Math.ceil(totalCount / itemsPerPage);

    if (loading) return <LoadingSpinner />;
    if (error) return <div className="text-red-500">Error: {error}</div>;

    return (
        <div className="page-container">
            <div className="content-container">
                <JournalHeader totalEntries={totalCount} />

                <JournalFilters
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                    selectedMood={selectedMood}
                    setSelectedMood={setSelectedMood}
                    uniqueMoods={uniqueMoods}
                    totalEntries={hasFilters ? allJournals.length : backendTotalCount}
                    filteredCount={hasFilters ? filteredJournals.length : totalCount}
                    onClearFilters={hasFilters ? handleClearFilters : undefined}
                />

                {displayJournals.length === 0 ? (
                    <JournalEmptyState hasEntries={totalCount > 0} />
                ) : (
                    <>
                        <JournalList entries={displayJournals} />
                        
                        {totalPages > 1 && (
                            <JournalPagination
                                currentPage={currentPage}
                                totalPages={totalPages}
                                totalItems={totalCount}
                                itemsPerPage={itemsPerPage}
                                onPageChange={handlePageChange}
                                hasFilters={hasFilters}
                            />
                        )}
                    </>
                )}
            </div>
        </div>
    );
}