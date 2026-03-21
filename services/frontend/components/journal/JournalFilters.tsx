import { Search, Filter, Tag } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import type { MoodOption } from "@/lib/utils/moodMapping";

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
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400"
              size={20}
            />
            <input
              type="text"
              placeholder="Search your entries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-primary pl-10"
            />
          </div>

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
              <span className="badge-filter-blue">Text: {searchTerm}</span>
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
