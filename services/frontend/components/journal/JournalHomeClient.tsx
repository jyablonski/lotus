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
import {
  searchJournals,
  keywordSearchJournals,
  type SemanticSearchResult,
  type KeywordSearchResult,
} from "@/actions/journals";

export type SearchMode = "exact" | "keyword" | "semantic";

interface JournalHomeClientProps {
  journals: JournalEntry[];
  totalCount: number;
  timezone: string;
  /** When true, show OpenAI topic tags on each entry (gated by frontend_show_tags). */
  showTags?: boolean;
  /** When true, show semantic search toggle (gated by semantic_search waffle flag). */
  semanticSearchEnabled?: boolean;
  /** When true, show keyword search toggle (gated by keyword_search waffle flag). */
  keywordSearchEnabled?: boolean;
  /** When true, show similarity scores on semantic search results. */
  isAdmin?: boolean;
}

export function JournalHomeClient({
  journals,
  totalCount,
  timezone,
  showTags = false,
  semanticSearchEnabled = false,
  keywordSearchEnabled = false,
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
  const [keywordResults, setKeywordResults] = useState<KeywordSearchResult[]>(
    [],
  );
  const [isSearching, setIsSearching] = useState(false);
  const semanticDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const keywordDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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

  const uniqueMoods = useMemo(
    () => getUniqueMoodsFromJournals(journals),
    [journals],
  );
  const uniqueTags = useMemo(
    () => getUniqueTagsFromJournals(journals),
    [journals],
  );

  const isSemanticActive =
    searchMode === "semantic" && searchTerm.trim() !== "";
  const isKeywordActive = searchMode === "keyword" && searchTerm.trim() !== "";
  const isServerSearchActive = isSemanticActive || isKeywordActive;

  // In server-search modes we use the ordered results from the backend; in
  // "exact" mode we apply the local text/mood/tag filter.
  const filteredJournals = useMemo(() => {
    if (isSemanticActive) {
      const entries = semanticResults.map((r) => r.journal);
      return filterJournals(entries, "", selectedMood, selectedTag);
    }
    if (isKeywordActive) {
      const entries = keywordResults.map((r) => r.journal);
      return filterJournals(entries, "", selectedMood, selectedTag);
    }
    return filterJournals(journals, searchTerm, selectedMood, selectedTag);
  }, [
    journals,
    searchTerm,
    selectedMood,
    selectedTag,
    isSemanticActive,
    isKeywordActive,
    semanticResults,
    keywordResults,
  ]);

  const similarityScores = useMemo(() => {
    if (isSemanticActive) {
      return new Map(
        semanticResults.map((r) => [r.journal.journalId, r.similarityScore]),
      );
    }
    if (isKeywordActive) {
      return new Map(keywordResults.map((r) => [r.journal.journalId, r.rank]));
    }
    return new Map<string, number>();
  }, [isSemanticActive, isKeywordActive, semanticResults, keywordResults]);

  const hasActiveFilters =
    searchTerm.trim() !== "" || selectedMood !== "all" || selectedTag !== "all";

  const paginatedJournals = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredJournals.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredJournals, currentPage]);

  const displayTotalCount = hasActiveFilters
    ? filteredJournals.length
    : totalCount;
  const totalPages = Math.ceil(displayTotalCount / itemsPerPage);

  const triggerSemanticSearch = useCallback((query: string) => {
    if (semanticDebounceRef.current) {
      clearTimeout(semanticDebounceRef.current);
    }
    const trimmed = query.trim();
    if (!trimmed) {
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

  const triggerKeywordSearch = useCallback((query: string) => {
    if (keywordDebounceRef.current) {
      clearTimeout(keywordDebounceRef.current);
    }
    const trimmed = query.trim();
    if (!trimmed) {
      setKeywordResults([]);
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    keywordDebounceRef.current = setTimeout(async () => {
      const response = await keywordSearchJournals(query);
      setKeywordResults(response.results);
      setIsSearching(false);
      setCurrentPage(1);
    }, 300);
  }, []);

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

      if (searchMode === "semantic") {
        triggerSemanticSearch(term);
      } else if (searchMode === "keyword") {
        triggerKeywordSearch(term);
      }
    },
    [searchMode, triggerSemanticSearch, triggerKeywordSearch],
  );

  const handleSearchModeChange = useCallback(
    (mode: SearchMode) => {
      setSearchMode(mode);
      setCurrentPage(1);
      if (mode === "semantic" && searchTerm.trim()) {
        triggerSemanticSearch(searchTerm);
      } else if (mode === "keyword" && searchTerm.trim()) {
        triggerKeywordSearch(searchTerm);
      } else if (mode === "exact") {
        setSemanticResults([]);
        setKeywordResults([]);
      }
    },
    [searchTerm, triggerSemanticSearch, triggerKeywordSearch],
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
    setKeywordResults([]);
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
          keywordSearchEnabled={keywordSearchEnabled}
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
              similarityScores={
                isAdmin && isSemanticActive ? similarityScores : undefined
              }
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
