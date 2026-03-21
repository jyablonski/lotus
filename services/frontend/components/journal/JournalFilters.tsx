import { Search, Filter, Tag, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import type { MoodOption } from "@/lib/utils/moodMapping";
import type { SearchMode } from "@/components/journal/JournalHomeClient";

interface JournalFiltersProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  selectedMood: string;
  setSelectedMood: (mood: string) => void;
  uniqueMoods: MoodOption[];
  totalEntries: number;
  filteredCount: number;
  onClearFilters?: () => void;
  /** When true, show topic tag filter (requires uniqueTags). */
  showTagFilter?: boolean;
  selectedTag?: string;
  setSelectedTag?: (tag: string) => void;
  uniqueTags?: string[];
  /** When true, show the exact/semantic search mode toggle. */
  semanticSearchEnabled?: boolean;
  searchMode?: SearchMode;
  onSearchModeChange?: (mode: SearchMode) => void;
  isSearching?: boolean;
}

function formatTagLabel(tag: string): string {
  return tag.replace(/_/g, " ");
}

export function JournalFilters({
  searchTerm,
  setSearchTerm,
  selectedMood,
  setSelectedMood,
  uniqueMoods,
  totalEntries,
  filteredCount,
  onClearFilters,
  showTagFilter = false,
  selectedTag = "all",
  setSelectedTag,
  uniqueTags = [],
  semanticSearchEnabled = false,
  searchMode = "exact",
  onSearchModeChange,
  isSearching = false,
}: JournalFiltersProps) {
  const hasActiveFilters =
    searchTerm ||
    selectedMood !== "all" ||
    (showTagFilter && selectedTag !== "all");

  const handleClearFilters = () => {
    if (onClearFilters) {
      onClearFilters();
    } else {
      setSearchTerm("");
      setSelectedMood("all");
      setSelectedTag?.("all");
    }
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            {isSearching ? (
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-dark-400 border-t-transparent" />
              </div>
            ) : searchMode === "semantic" ? (
              <Sparkles
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-400"
                size={20}
              />
            ) : (
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400"
                size={20}
              />
            )}
            <input
              type="text"
              placeholder={
                searchMode === "semantic"
                  ? "Semantic search your entries..."
                  : "Search your entries..."
              }
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-primary pl-10"
            />
          </div>

          {/* Search Mode Toggle */}
          {semanticSearchEnabled && (
            <div className="flex rounded-lg border border-dark-600 overflow-hidden">
              <button
                onClick={() => onSearchModeChange?.("exact")}
                className={`px-3 py-2 text-xs font-medium transition-colors ${
                  searchMode === "exact"
                    ? "bg-dark-600 text-dark-100"
                    : "bg-dark-800 text-dark-400 hover:text-dark-200"
                }`}
              >
                Exact
              </button>
              <button
                onClick={() => onSearchModeChange?.("semantic")}
                className={`px-3 py-2 text-xs font-medium transition-colors ${
                  searchMode === "semantic"
                    ? "bg-purple-600/20 text-purple-300 border-l border-purple-500/30"
                    : "bg-dark-800 text-dark-400 hover:text-dark-200 border-l border-dark-600"
                }`}
              >
                Semantic
              </button>
            </div>
          )}

          {/* Mood Filter */}
          <div className="sm:w-48">
            <div className="relative">
              <Filter
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400 z-10"
                size={20}
              />
              <select
                value={selectedMood}
                onChange={(e) => setSelectedMood(e.target.value)}
                className="select-primary pl-10"
              >
                <option value="all">All Moods</option>
                {uniqueMoods.map((mood) => (
                  <option key={mood.key} value={mood.key}>
                    {mood.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tag Filter — only when tags are enabled and there are tags */}
          {showTagFilter && uniqueTags.length > 0 && (
            <div className="sm:w-48">
              <div className="relative">
                <Tag
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400 z-10"
                  size={20}
                />
                <select
                  value={selectedTag}
                  onChange={(e) => setSelectedTag?.(e.target.value)}
                  className="select-primary pl-10"
                >
                  <option value="all">All Topics</option>
                  {uniqueTags.map((tag) => (
                    <option key={tag} value={tag}>
                      {formatTagLabel(tag)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Filter summary */}
        {hasActiveFilters && (
          <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-muted-dark">
            <span>
              Showing {filteredCount} of {totalEntries} entries
            </span>
            {searchTerm && (
              <span className="badge-filter-blue">
                {searchMode === "semantic" ? "Semantic" : "Text"}: {searchTerm}
              </span>
            )}
            {selectedMood !== "all" && (
              <span className="badge-filter-green">
                Mood:{" "}
                {uniqueMoods.find((m) => m.key === selectedMood)?.label ||
                  selectedMood}
              </span>
            )}
            {showTagFilter && selectedTag !== "all" && (
              <span className="badge-filter-green">
                Topic: {formatTagLabel(selectedTag)}
              </span>
            )}
            <button onClick={handleClearFilters} className="link-lotus ml-2">
              Clear filters
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
