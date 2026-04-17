import { render, screen, fireEvent } from "@testing-library/react";
import { JournalPagination } from "@/components/journal/JournalPagination";

jest.mock("lucide-react", () => ({
  ChevronLeft: () => <svg data-testid="chevron-left" />,
  ChevronRight: () => <svg data-testid="chevron-right" />,
}));

describe("JournalPagination", () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    totalItems: 50,
    itemsPerPage: 10,
    onPageChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders 'Showing X-Y of Z entries'", () => {
    render(<JournalPagination {...defaultProps} />);
    expect(screen.getByText(/Showing 1-10 of 50 entries/)).toBeInTheDocument();
  });

  it("renders correct range on middle page", () => {
    render(<JournalPagination {...defaultProps} currentPage={3} />);
    expect(screen.getByText(/Showing 21-30 of 50 entries/)).toBeInTheDocument();
  });

  it("caps end item at totalItems on last page", () => {
    render(
      <JournalPagination {...defaultProps} currentPage={5} totalItems={47} />,
    );
    expect(screen.getByText(/Showing 41-47 of 47 entries/)).toBeInTheDocument();
  });

  it("shows '(filtered)' when hasFilters is true", () => {
    render(<JournalPagination {...defaultProps} hasFilters={true} />);
    expect(screen.getByText("(filtered)")).toBeInTheDocument();
  });

  it("does not show '(filtered)' by default", () => {
    render(<JournalPagination {...defaultProps} />);
    expect(screen.queryByText("(filtered)")).not.toBeInTheDocument();
  });

  describe("Previous button", () => {
    it("is disabled on first page", () => {
      render(<JournalPagination {...defaultProps} currentPage={1} />);
      const prevButton = screen.getByText("Previous").closest("button");
      expect(prevButton).toBeDisabled();
    });

    it("is enabled on non-first page", () => {
      render(<JournalPagination {...defaultProps} currentPage={2} />);
      const prevButton = screen.getByText("Previous").closest("button");
      expect(prevButton).not.toBeDisabled();
    });

    it("calls onPageChange with currentPage - 1", () => {
      const onPageChange = jest.fn();
      render(
        <JournalPagination
          {...defaultProps}
          currentPage={3}
          onPageChange={onPageChange}
        />,
      );
      fireEvent.click(screen.getByText("Previous"));
      expect(onPageChange).toHaveBeenCalledWith(2);
    });
  });

  describe("Next button", () => {
    it("is disabled on last page", () => {
      render(<JournalPagination {...defaultProps} currentPage={5} />);
      const nextButton = screen.getByText("Next").closest("button");
      expect(nextButton).toBeDisabled();
    });

    it("is enabled on non-last page", () => {
      render(<JournalPagination {...defaultProps} currentPage={1} />);
      const nextButton = screen.getByText("Next").closest("button");
      expect(nextButton).not.toBeDisabled();
    });

    it("calls onPageChange with currentPage + 1", () => {
      const onPageChange = jest.fn();
      render(
        <JournalPagination
          {...defaultProps}
          currentPage={2}
          onPageChange={onPageChange}
        />,
      );
      fireEvent.click(screen.getByText("Next"));
      expect(onPageChange).toHaveBeenCalledWith(3);
    });
  });

  describe("page number buttons", () => {
    it("renders page number buttons", () => {
      render(<JournalPagination {...defaultProps} currentPage={1} />);
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("calls onPageChange when a page number is clicked", () => {
      const onPageChange = jest.fn();
      render(
        <JournalPagination {...defaultProps} onPageChange={onPageChange} />,
      );
      fireEvent.click(screen.getByText("3"));
      expect(onPageChange).toHaveBeenCalledWith(3);
    });

    it("shows ellipsis for gaps in page range", () => {
      render(
        <JournalPagination
          {...defaultProps}
          totalPages={20}
          totalItems={200}
          currentPage={1}
        />,
      );
      expect(screen.getByText("...")).toBeInTheDocument();
    });
  });
});
