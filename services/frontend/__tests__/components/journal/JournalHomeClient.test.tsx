import { render, screen, fireEvent } from "@testing-library/react";
import { JournalHomeClient } from "@/components/journal/JournalHomeClient";
import { JournalEntry } from "@/types/journal";

// Mock server actions (pulls in next-auth which Jest can't parse)
jest.mock("@/actions/journals", () => ({
  searchJournals: jest.fn().mockResolvedValue({ results: [] }),
}));

// Mock child components to test orchestration
jest.mock("@/components/journal/JournalHeader", () => ({
  JournalHeader: ({ totalEntries }: { totalEntries: number }) => (
    <div data-testid="journal-header">Total: {totalEntries}</div>
  ),
}));

jest.mock("@/components/journal/JournalFilters", () => ({
  JournalFilters: ({
    searchTerm,
    setSearchTerm,
    selectedMood,
    setSelectedMood,
    selectedTag = "all",
    setSelectedTag,
    filteredCount,
    onClearFilters,
  }: {
    searchTerm: string;
    setSearchTerm: (t: string) => void;
    selectedMood: string;
    setSelectedMood: (m: string) => void;
    selectedTag?: string;
    setSelectedTag?: (t: string) => void;
    filteredCount: number;
    onClearFilters?: () => void;
  }) => (
    <div data-testid="journal-filters">
      <span data-testid="search-term">{searchTerm}</span>
      <span data-testid="selected-mood">{selectedMood}</span>
      <span data-testid="selected-tag">{selectedTag}</span>
      <span data-testid="filtered-count">{filteredCount}</span>
      <button onClick={() => setSearchTerm("Journal entry")}>Set Search</button>
      <button onClick={() => setSelectedMood("7")}>Set Mood</button>
      {setSelectedTag && (
        <button onClick={() => setSelectedTag("work")}>Set Tag</button>
      )}
      {onClearFilters && (
        <button onClick={onClearFilters}>Clear Filters</button>
      )}
    </div>
  ),
}));

jest.mock("@/components/journal/JournalEmptyState", () => ({
  JournalEmptyState: ({ hasEntries }: { hasEntries: boolean }) => (
    <div data-testid="journal-empty-state">
      {hasEntries ? "Filtered empty" : "No entries"}
    </div>
  ),
}));

jest.mock("@/components/journal/JournalList", () => ({
  JournalList: ({ entries }: { entries: JournalEntry[] }) => (
    <div data-testid="journal-list">
      {entries.map((e) => (
        <div key={e.journalId} data-testid={`entry-${e.journalId}`}>
          {e.journalText}
        </div>
      ))}
    </div>
  ),
}));

jest.mock("@/components/journal/JournalPagination", () => ({
  JournalPagination: ({
    currentPage,
    totalPages,
    onPageChange,
  }: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  }) => (
    <div data-testid="journal-pagination">
      <span data-testid="current-page">{currentPage}</span>
      <span data-testid="total-pages">{totalPages}</span>
      <button onClick={() => onPageChange(2)}>Go to page 2</button>
    </div>
  ),
}));

function makeEntries(count: number): JournalEntry[] {
  return Array.from({ length: count }, (_, i) => ({
    journalId: String(i + 1),
    userId: "user-1",
    journalText: `Journal entry number ${i + 1}`,
    userMood: 7, // happy
    createdAt: `2025-01-${String(i + 1).padStart(2, "0")}T10:00:00Z`,
  }));
}

describe("JournalHomeClient", () => {
  it("renders header with total count", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(5)}
        totalCount={5}
        timezone="UTC"
      />,
    );
    expect(screen.getByTestId("journal-header")).toHaveTextContent("Total: 5");
  });

  it("renders filters", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(5)}
        totalCount={5}
        timezone="UTC"
      />,
    );
    expect(screen.getByTestId("journal-filters")).toBeInTheDocument();
  });

  it("renders journal list with entries", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(3)}
        totalCount={3}
        timezone="UTC"
      />,
    );
    expect(screen.getByTestId("journal-list")).toBeInTheDocument();
    expect(screen.getByTestId("entry-1")).toBeInTheDocument();
    expect(screen.getByTestId("entry-2")).toBeInTheDocument();
    expect(screen.getByTestId("entry-3")).toBeInTheDocument();
  });

  it("shows empty state when no entries", () => {
    render(<JournalHomeClient journals={[]} totalCount={0} timezone="UTC" />);
    expect(screen.getByTestId("journal-empty-state")).toHaveTextContent(
      "No entries",
    );
  });

  it("does not show pagination when entries fit on one page", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(5)}
        totalCount={5}
        timezone="UTC"
      />,
    );
    expect(screen.queryByTestId("journal-pagination")).not.toBeInTheDocument();
  });

  it("shows pagination when entries exceed one page", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(15)}
        totalCount={15}
        timezone="UTC"
      />,
    );
    expect(screen.getByTestId("journal-pagination")).toBeInTheDocument();
  });

  it("only shows 10 entries per page", () => {
    render(
      <JournalHomeClient
        journals={makeEntries(15)}
        totalCount={15}
        timezone="UTC"
      />,
    );
    const list = screen.getByTestId("journal-list");
    const entries = list.querySelectorAll("[data-testid^='entry-']");
    expect(entries).toHaveLength(10);
  });

  describe("search filtering", () => {
    it("resets to page 1 when search changes", () => {
      render(
        <JournalHomeClient
          journals={makeEntries(15)}
          totalCount={15}
          timezone="UTC"
        />,
      );
      // Go to page 2 first
      fireEvent.click(screen.getByText("Go to page 2"));
      expect(screen.getByTestId("current-page")).toHaveTextContent("2");

      // Now set search — should reset to page 1
      fireEvent.click(screen.getByText("Set Search"));
      expect(screen.getByTestId("current-page")).toHaveTextContent("1");
    });
  });

  describe("mood filtering", () => {
    it("resets to page 1 when mood changes", () => {
      render(
        <JournalHomeClient
          journals={makeEntries(15)}
          totalCount={15}
          timezone="UTC"
        />,
      );
      fireEvent.click(screen.getByText("Go to page 2"));
      fireEvent.click(screen.getByText("Set Mood"));
      expect(screen.getByTestId("current-page")).toHaveTextContent("1");
    });
  });

  describe("clear filters", () => {
    it("shows clear filters button when filters are active", () => {
      render(
        <JournalHomeClient
          journals={makeEntries(5)}
          totalCount={5}
          timezone="UTC"
        />,
      );
      // Activate a filter
      fireEvent.click(screen.getByText("Set Search"));
      expect(screen.getByText("Clear Filters")).toBeInTheDocument();
    });

    it("resets search, mood, and tag when clear filters is clicked", () => {
      const entriesWithTags = makeEntries(3).map((e, i) =>
        i === 0 ? { ...e, topicNames: ["work"] as string[] } : e,
      );
      render(
        <JournalHomeClient
          journals={entriesWithTags}
          totalCount={3}
          timezone="UTC"
          showTags={true}
        />,
      );
      fireEvent.click(screen.getByText("Set Search"));
      fireEvent.click(screen.getByText("Set Mood"));
      fireEvent.click(screen.getByText("Set Tag"));
      expect(screen.getByTestId("selected-tag")).toHaveTextContent("work");
      fireEvent.click(screen.getByText("Clear Filters"));
      expect(screen.getByTestId("search-term")).toHaveTextContent("");
      expect(screen.getByTestId("selected-mood")).toHaveTextContent("all");
      expect(screen.getByTestId("selected-tag")).toHaveTextContent("all");
    });
  });
});
