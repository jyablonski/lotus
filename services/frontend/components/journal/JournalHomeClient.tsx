"use client";

import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { JournalHeader } from "@/components/journal/JournalHeader";
import { JournalFilters } from "@/components/journal/JournalFilters";
import { JournalEmptyState } from "@/components/journal/JournalEmptyState";
import { JournalList } from "@/components/journal/JournalList";
import { JournalPagination } from "@/components/journal/JournalPagination";
import { JournalEntry } from "@/types/journal";
import {
  filterJournals,
  getUniqueMoodsFromJournals,
  getUniqueTagsFromJournals,
} from "@/lib/utils/journalFilters";
import { trackEvent } from "@/lib/analytics";

interface JournalHomeClientProps {
  journals: JournalEntry[];
  totalCount: number;
  timezone: string;
  /** When true, show OpenAI topic tags on each entry (gated by frontend_show_tags). */
  showTags?: boolean;
}

export function JournalHomeClient({
  journals,
  totalCount,
  timezone,
  showTags = false,
}: JournalHomeClientProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedMood, setSelectedMood] = useState<string>("all");
  const [selectedTag, setSelectedTag] = useState<string>("all");
  const itemsPerPage = 10;

  // §3c: entries_browsed — fire once when the browse page is viewed
  const hasFiredBrowse = useRef(false);
  useEffect(() => {
    if (!hasFiredBrowse.current) {
      hasFiredBrowse.current = true;
      trackEvent("entries_browsed", { entries_count: totalCount });
    }
  }, [totalCount]);

  // §3c: search_used — fire when the user stops typing (debounce 800ms)
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Extract unique moods and tags from journals
  const uniqueMoods = useMemo(
    () => getUniqueMoodsFromJournals(journals),
    [journals],
  );
  const uniqueTags = useMemo(
    () => getUniqueTagsFromJournals(journals),
    [journals],
  );

  // Filter journals by search, mood, and tag
  const filteredJournals = useMemo(() => {
    return filterJournals(journals, searchTerm, selectedMood, selectedTag);
  }, [journals, searchTerm, selectedMood, selectedTag]);

  const hasActiveFilters =
    searchTerm.trim() !== "" || selectedMood !== "all" || selectedTag !== "all";

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

    // §3c: search_used — debounced so we fire once the user pauses typing
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    if (term.trim()) {
      searchDebounceRef.current = setTimeout(() => {
        trackEvent("search_used", { query_length: term.trim().length });
      }, 800);
    }
  }, []);

  const handleMoodChange = useCallback((mood: string) => {
    setSelectedMood(mood);
    setCurrentPage(1);
  }, []);

  const handleTagChange = useCallback((tag: string) => {
    setSelectedTag(tag);
    setCurrentPage(1);
  }, []);

  const handleClearFilters = useCallback(() => {
    setSearchTerm("");
    setSelectedMood("all");
    setSelectedTag("all");
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
          showTagFilter={showTags}
          selectedTag={selectedTag}
          setSelectedTag={handleTagChange}
          uniqueTags={uniqueTags}
        />

        {paginatedJournals.length === 0 ? (
          <JournalEmptyState hasEntries={totalCount > 0} />
        ) : (
          <>
            <JournalList
              entries={paginatedJournals}
              timezone={timezone}
              showTags={showTags}
            />

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
