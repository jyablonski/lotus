import { render, screen, fireEvent } from "@testing-library/react";
import { JournalFilters } from "@/components/journal/JournalFilters";

jest.mock("lucide-react", () => ({
  Search: () => <svg data-testid="search-icon" />,
  Filter: () => <svg data-testid="filter-icon" />,
}));

const mockMoods = [
  { key: "happy", label: "Happy", emoji: "😊" },
  { key: "sad", label: "Sad", emoji: "😢" },
  { key: "excited", label: "Excited", emoji: "🤩" },
];

describe("JournalFilters", () => {
  const defaultProps = {
    searchTerm: "",
    setSearchTerm: jest.fn(),
    selectedMood: "all",
    setSelectedMood: jest.fn(),
    uniqueMoods: mockMoods,
    totalEntries: 20,
    filteredCount: 20,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders search input", () => {
    render(<JournalFilters {...defaultProps} />);
    expect(
      screen.getByPlaceholderText("Search your entries..."),
    ).toBeInTheDocument();
  });

  it("renders mood dropdown with 'All Moods' default", () => {
    render(<JournalFilters {...defaultProps} />);
    const select = screen.getByRole("combobox");
    expect(select).toHaveValue("all");
  });

  it("renders mood options in dropdown", () => {
    render(<JournalFilters {...defaultProps} />);
    expect(screen.getByText("😊 Happy")).toBeInTheDocument();
    expect(screen.getByText("😢 Sad")).toBeInTheDocument();
    expect(screen.getByText("🤩 Excited")).toBeInTheDocument();
  });

  it("calls setSearchTerm on search input change", () => {
    const setSearchTerm = jest.fn();
    render(<JournalFilters {...defaultProps} setSearchTerm={setSearchTerm} />);
    fireEvent.change(screen.getByPlaceholderText("Search your entries..."), {
      target: { value: "gratitude" },
    });
    expect(setSearchTerm).toHaveBeenCalledWith("gratitude");
  });

  it("calls setSelectedMood on dropdown change", () => {
    const setSelectedMood = jest.fn();
    render(
      <JournalFilters {...defaultProps} setSelectedMood={setSelectedMood} />,
    );
    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "happy" },
    });
    expect(setSelectedMood).toHaveBeenCalledWith("happy");
  });

  describe("filter summary", () => {
    it("does not show summary when no filters are active", () => {
      render(<JournalFilters {...defaultProps} />);
      expect(screen.queryByText("Clear filters")).not.toBeInTheDocument();
    });

    it("shows summary with search term badge", () => {
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="gratitude"
          filteredCount={5}
        />,
      );
      expect(screen.getByText("Showing 5 of 20 entries")).toBeInTheDocument();
      expect(screen.getByText(/Text: gratitude/)).toBeInTheDocument();
    });

    it("shows summary with mood badge", () => {
      render(
        <JournalFilters
          {...defaultProps}
          selectedMood="happy"
          filteredCount={8}
        />,
      );
      expect(screen.getByText("Showing 8 of 20 entries")).toBeInTheDocument();
      expect(screen.getByText(/Mood:.*Happy/)).toBeInTheDocument();
    });

    it("shows both badges when both filters are active", () => {
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="morning"
          selectedMood="excited"
          filteredCount={2}
        />,
      );
      expect(screen.getByText(/Text: morning/)).toBeInTheDocument();
      expect(screen.getByText(/Mood:.*Excited/)).toBeInTheDocument();
    });

    it("shows 'Clear filters' button when filters are active", () => {
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="test"
          filteredCount={3}
        />,
      );
      expect(screen.getByText("Clear filters")).toBeInTheDocument();
    });

    it("calls onClearFilters when provided and Clear filters is clicked", () => {
      const onClearFilters = jest.fn();
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="test"
          filteredCount={3}
          onClearFilters={onClearFilters}
        />,
      );
      fireEvent.click(screen.getByText("Clear filters"));
      expect(onClearFilters).toHaveBeenCalled();
    });

    it("calls setSearchTerm and setSelectedMood directly when no onClearFilters", () => {
      const setSearchTerm = jest.fn();
      const setSelectedMood = jest.fn();
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="test"
          filteredCount={3}
          setSearchTerm={setSearchTerm}
          setSelectedMood={setSelectedMood}
        />,
      );
      fireEvent.click(screen.getByText("Clear filters"));
      expect(setSearchTerm).toHaveBeenCalledWith("");
      expect(setSelectedMood).toHaveBeenCalledWith("all");
    });
  });
});
