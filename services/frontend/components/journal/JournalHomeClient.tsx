"use client";

import { useState, useMemo, useCallback } from "react";
import { JournalHeader } from "@/components/journal/JournalHeader";
import { JournalFilters } from "@/components/journal/JournalFilters";
import { JournalEmptyState } from "@/components/journal/JournalEmptyState";
import { JournalList } from "@/components/journal/JournalList";
import { JournalPagination } from "@/components/journal/JournalPagination";
import { JournalEntry } from "@/types/journal";
import {
  filterJournals,
  getUniqueMoodsFromJournals,
} from "@/lib/utils/journalFilters";

interface JournalHomeClientProps {
  journals: JournalEntry[];
  totalCount: number;
}

export function JournalHomeClient({
  journals,
  totalCount,
}: JournalHomeClientProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedMood, setSelectedMood] = useState<string>("all");
  const itemsPerPage = 10;

  // Extract unique moods from journals using existing utility
  const uniqueMoods = useMemo(() => {
    return getUniqueMoodsFromJournals(journals);
  }, [journals]);

  // Filter journals based on search term and mood using existing utility
  const filteredJournals = useMemo(() => {
    return filterJournals(journals, searchTerm, selectedMood);
  }, [journals, searchTerm, selectedMood]);

  const hasActiveFilters = searchTerm.trim() !== "" || selectedMood !== "all";

  // Paginate filtered results
  const paginatedJournals = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredJournals.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredJournals, currentPage]);

  const displayTotalCount = hasActiveFilters
    ? filteredJournals.length
    : totalCount;
  const totalPages = Math.ceil(displayTotalCount / itemsPerPage);

  // Reset to page 1 when filters change
  const handleSearchChange = useCallback((term: string) => {
    setSearchTerm(term);
    setCurrentPage(1);
  }, []);

  const handleMoodChange = useCallback((mood: string) => {
    setSelectedMood(mood);
    setCurrentPage(1);
  }, []);

  const handleClearFilters = useCallback(() => {
    setSearchTerm("");
    setSelectedMood("all");
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  return (
    <div className="page-container">
      <div className="content-container">
        <JournalHeader totalEntries={totalCount} />

        <JournalFilters
          searchTerm={searchTerm}
          setSearchTerm={handleSearchChange}
          selectedMood={selectedMood}
          setSelectedMood={handleMoodChange}
          uniqueMoods={uniqueMoods}
          totalEntries={totalCount}
          filteredCount={filteredJournals.length}
          onClearFilters={hasActiveFilters ? handleClearFilters : undefined}
        />

        {paginatedJournals.length === 0 ? (
          <JournalEmptyState hasEntries={totalCount > 0} />
        ) : (
          <>
            <JournalList entries={paginatedJournals} />

            {totalPages > 1 && (
              <JournalPagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={displayTotalCount}
                itemsPerPage={itemsPerPage}
                onPageChange={handlePageChange}
                hasFilters={hasActiveFilters}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
