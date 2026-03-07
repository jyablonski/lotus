import { render, screen, fireEvent } from "@testing-library/react";
import { CalendarHeader } from "@/components/calendar/CalendarHeader";

jest.mock("lucide-react", () => ({
  ChevronLeft: () => <svg data-testid="chevron-left" />,
  ChevronRight: () => <svg data-testid="chevron-right" />,
  Calendar: () => <svg data-testid="calendar-icon" />,
}));

describe("CalendarHeader", () => {
  const defaultProps = {
    currentMonth: new Date(2025, 5, 1), // June 2025
    onNavigateMonth: jest.fn(),
    onGoToToday: jest.fn(),
    timezone: "UTC",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders 'Journal Calendar' heading", () => {
    render(<CalendarHeader {...defaultProps} />);
    expect(screen.getByText("Journal Calendar")).toBeInTheDocument();
  });

  it("renders the month and year", () => {
    render(<CalendarHeader {...defaultProps} />);
    expect(screen.getByText("June 2025")).toBeInTheDocument();
  });

  it("renders different months correctly", () => {
    render(
      <CalendarHeader {...defaultProps} currentMonth={new Date(2025, 0, 1)} />,
    );
    expect(screen.getByText("January 2025")).toBeInTheDocument();
  });

  it("renders 'Today' button", () => {
    render(<CalendarHeader {...defaultProps} />);
    expect(screen.getByText("Today")).toBeInTheDocument();
  });

  it("calls onGoToToday when Today button is clicked", () => {
    const onGoToToday = jest.fn();
    render(<CalendarHeader {...defaultProps} onGoToToday={onGoToToday} />);
    fireEvent.click(screen.getByText("Today"));
    expect(onGoToToday).toHaveBeenCalled();
  });

  it("calls onNavigateMonth with 'prev' when left arrow is clicked", () => {
    const onNavigateMonth = jest.fn();
    render(
      <CalendarHeader {...defaultProps} onNavigateMonth={onNavigateMonth} />,
    );
    // ChevronLeft is the first navigation button
    const prevButton = screen.getByTestId("chevron-left").closest("button")!;
    fireEvent.click(prevButton);
    expect(onNavigateMonth).toHaveBeenCalledWith("prev");
  });

  it("calls onNavigateMonth with 'next' when right arrow is clicked", () => {
    const onNavigateMonth = jest.fn();
    render(
      <CalendarHeader {...defaultProps} onNavigateMonth={onNavigateMonth} />,
    );
    const nextButton = screen.getByTestId("chevron-right").closest("button")!;
    fireEvent.click(nextButton);
    expect(onNavigateMonth).toHaveBeenCalledWith("next");
  });

  it("shows total entries when provided", () => {
    render(<CalendarHeader {...defaultProps} totalEntries={42} />);
    expect(
      screen.getByText("View your 42 entries by date"),
    ).toBeInTheDocument();
  });

  it("shows singular 'entry' for 1 entry", () => {
    render(<CalendarHeader {...defaultProps} totalEntries={1} />);
    expect(screen.getByText("View your 1 entry by date")).toBeInTheDocument();
  });

  it("shows generic text when totalEntries not provided", () => {
    render(<CalendarHeader {...defaultProps} />);
    expect(screen.getByText("View your entries by date")).toBeInTheDocument();
  });
});
