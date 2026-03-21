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
import { searchJournals, type SemanticSearchResult } from "@/actions/journals";

export type SearchMode = "exact" | "semantic";

interface JournalHomeClientProps {
  journals: JournalEntry[];
  totalCount: number;
  timezone: string;
  /** When true, show OpenAI topic tags on each entry (gated by frontend_show_tags). */
  showTags?: boolean;
  /** When true, show semantic search toggle (gated by semantic_search waffle flag). */
  semanticSearchEnabled?: boolean;
  /** When true, show similarity scores on semantic search results. */
  isAdmin?: boolean;
}

export function JournalHomeClient({
  journals,
  totalCount,
  timezone,
  showTags = false,
  semanticSearchEnabled = false,
  isAdmin = false,
}: JournalHomeClientProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedMood, setSelectedMood] = useState<string>("all");
  const [selectedTag, setSelectedTag] = useState<string>("all");
  const [searchMode, setSearchMode] = useState<SearchMode>("exact");
  const [semanticResults, setSemanticResults] = useState<
    SemanticSearchResult[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const semanticDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
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

  // Determine if we're in active semantic search mode with results
  const isSemanticActive =
    searchMode === "semantic" && searchTerm.trim() !== "";

  // Filter journals by search, mood, and tag (exact mode or no search term)
  const filteredJournals = useMemo(() => {
    if (isSemanticActive) {
      // In semantic mode, results come from the server — apply only mood/tag filters
      const entries = semanticResults.map((r) => r.journal);
      return filterJournals(entries, "", selectedMood, selectedTag);
    }
    return filterJournals(journals, searchTerm, selectedMood, selectedTag);
  }, [
    journals,
    searchTerm,
    selectedMood,
    selectedTag,
    isSemanticActive,
    semanticResults,
  ]);

  // Build a map of similarity scores by journal ID for rendering
  const similarityScores = useMemo(() => {
    if (!isSemanticActive) return new Map<string, number>();
    return new Map(
      semanticResults.map((r) => [r.journal.journalId, r.similarityScore]),
    );
  }, [isSemanticActive, semanticResults]);

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

  // Trigger semantic search (debounced)
  const triggerSemanticSearch = useCallback((query: string) => {
    if (semanticDebounceRef.current) {
      clearTimeout(semanticDebounceRef.current);
    }
    if (!query.trim()) {
      setSemanticResults([]);
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    semanticDebounceRef.current = setTimeout(async () => {
      const response = await searchJournals(query);
      setSemanticResults(response.results);
      setIsSearching(false);
      setCurrentPage(1);
    }, 300);
  }, []);

  // Reset to page 1 when filters change
  const handleSearchChange = useCallback(
    (term: string) => {
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

      // Trigger semantic search when in semantic mode
      if (searchMode === "semantic") {
        triggerSemanticSearch(term);
      }
    },
    [searchMode, triggerSemanticSearch],
  );

  const handleSearchModeChange = useCallback(
    (mode: SearchMode) => {
      setSearchMode(mode);
      setSemanticResults([]);
      setCurrentPage(1);
      // If switching to semantic with an existing search term, trigger search
      if (mode === "semantic" && searchTerm.trim()) {
        triggerSemanticSearch(searchTerm);
      }
    },
    [searchTerm, triggerSemanticSearch],
  );

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
    setSemanticResults([]);
    setIsSearching(false);
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
          semanticSearchEnabled={semanticSearchEnabled}
          searchMode={searchMode}
          onSearchModeChange={handleSearchModeChange}
          isSearching={isSearching}
        />

        {paginatedJournals.length === 0 ? (
          <JournalEmptyState hasEntries={totalCount > 0} />
        ) : (
          <>
            <JournalList
              entries={paginatedJournals}
              timezone={timezone}
              showTags={showTags}
              similarityScores={isAdmin ? similarityScores : undefined}
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
