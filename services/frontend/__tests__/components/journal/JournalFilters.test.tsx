import { render, screen, fireEvent } from "@testing-library/react";
import { JournalFilters } from "@/components/journal/JournalFilters";

jest.mock("lucide-react", () => ({
  Search: () => <svg data-testid="search-icon" />,
  Filter: () => <svg data-testid="filter-icon" />,
  Tag: () => <svg data-testid="tag-icon" />,
}));

const mockMoods = [
  { key: "5", label: "5" },
  { key: "7", label: "7" },
  { key: "8", label: "8" },
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
    showTagFilter: false,
    selectedTag: "all",
    setSelectedTag: jest.fn(),
    uniqueTags: [] as string[],
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
    const comboboxes = screen.getAllByRole("combobox");
    const moodSelect = comboboxes[0];
    expect(moodSelect).toHaveValue("all");
  });

  it("renders mood options in dropdown", () => {
    render(<JournalFilters {...defaultProps} />);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
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
    const moodSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(moodSelect, { target: { value: "7" } });
    expect(setSelectedMood).toHaveBeenCalledWith("7");
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
        <JournalFilters {...defaultProps} selectedMood="7" filteredCount={8} />,
      );
      expect(screen.getByText("Showing 8 of 20 entries")).toBeInTheDocument();
      expect(screen.getByText(/Mood:.*7/)).toBeInTheDocument();
    });

    it("shows both badges when both filters are active", () => {
      render(
        <JournalFilters
          {...defaultProps}
          searchTerm="morning"
          selectedMood="8"
          filteredCount={2}
        />,
      );
      expect(screen.getByText(/Text: morning/)).toBeInTheDocument();
      expect(screen.getByText(/Mood:.*8/)).toBeInTheDocument();
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

  describe("tag filter", () => {
    it("does not render tag dropdown when showTagFilter is false", () => {
      render(
        <JournalFilters {...defaultProps} uniqueTags={["work", "goals"]} />,
      );
      expect(screen.queryByText("All Topics")).not.toBeInTheDocument();
    });

    it("does not render tag dropdown when uniqueTags is empty", () => {
      render(<JournalFilters {...defaultProps} showTagFilter={true} />);
      expect(screen.queryByText("All Topics")).not.toBeInTheDocument();
    });

    it("renders tag dropdown when showTagFilter and uniqueTags provided", () => {
      render(
        <JournalFilters
          {...defaultProps}
          showTagFilter={true}
          uniqueTags={["work_stress", "goals"]}
        />,
      );
      expect(screen.getByText("All Topics")).toBeInTheDocument();
      expect(screen.getByText("work stress")).toBeInTheDocument();
      expect(screen.getByText("goals")).toBeInTheDocument();
    });

    it("shows Topic badge in summary when tag selected", () => {
      render(
        <JournalFilters
          {...defaultProps}
          showTagFilter={true}
          uniqueTags={["work", "goals"]}
          selectedTag="work"
          filteredCount={5}
        />,
      );
      expect(screen.getByText(/Topic: work/)).toBeInTheDocument();
    });

    it("calls setSelectedTag when tag dropdown changes", () => {
      const setSelectedTag = jest.fn();
      render(
        <JournalFilters
          {...defaultProps}
          showTagFilter={true}
          uniqueTags={["work", "goals"]}
          setSelectedTag={setSelectedTag}
        />,
      );
      const comboboxes = screen.getAllByRole("combobox");
      const tagSelect = comboboxes[comboboxes.length - 1];
      fireEvent.change(tagSelect, { target: { value: "goals" } });
      expect(setSelectedTag).toHaveBeenCalledWith("goals");
    });

    it("calls setSelectedTag('all') when Clear filters clicked and no onClearFilters", () => {
      const setSelectedTag = jest.fn();
      render(
        <JournalFilters
          {...defaultProps}
          showTagFilter={true}
          uniqueTags={["work"]}
          selectedTag="work"
          filteredCount={3}
          setSearchTerm={jest.fn()}
          setSelectedMood={jest.fn()}
          setSelectedTag={setSelectedTag}
        />,
      );
      fireEvent.click(screen.getByText("Clear filters"));
      expect(setSelectedTag).toHaveBeenCalledWith("all");
    });
  });
});
