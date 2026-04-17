import { render, screen, fireEvent } from "@testing-library/react";
import { CalendarClient } from "@/components/calendar/CalendarClient";
import { JournalEntry } from "@/types/journal";

jest.mock("@/components/calendar/CalendarHeader", () => ({
  CalendarHeader: ({
    currentMonth,
    onNavigateMonth,
    onGoToToday,
    totalEntries,
  }: {
    currentMonth: Date;
    onNavigateMonth: (direction: "prev" | "next") => void;
    onGoToToday: () => void;
    totalEntries?: number;
  }) => (
    <div data-testid="calendar-header">
      <span data-testid="current-month">
        {currentMonth.getMonth() + 1}/{currentMonth.getFullYear()}
      </span>
      <span data-testid="total-entries">{totalEntries}</span>
      <button onClick={() => onNavigateMonth("prev")}>Prev Month</button>
      <button onClick={() => onNavigateMonth("next")}>Next Month</button>
      <button onClick={onGoToToday}>Go to Today</button>
    </div>
  ),
}));

jest.mock("@/components/calendar/CalendarGrid", () => ({
  CalendarGrid: ({
    calendarDays,
    onDateSelect,
  }: {
    calendarDays: Array<{ dateString: string; date: Date }>;
    onDateSelect: (date: Date) => void;
  }) => (
    <div data-testid="calendar-grid">
      <span data-testid="day-count">{calendarDays.length}</span>
      {calendarDays.slice(0, 3).map((day) => (
        <button
          key={day.dateString}
          data-testid={`day-${day.dateString}`}
          onClick={() => onDateSelect(day.date)}
        >
          {day.dateString}
        </button>
      ))}
    </div>
  ),
}));

jest.mock("@/components/calendar/SelectedDateEntries", () => ({
  SelectedDateEntries: ({
    selectedDate,
    entries,
  }: {
    selectedDate: Date;
    entries: JournalEntry[];
  }) => (
    <div data-testid="selected-date-entries">
      <span data-testid="selected-date">
        {selectedDate.getFullYear()}-{selectedDate.getMonth() + 1}-
        {selectedDate.getDate()}
      </span>
      <span data-testid="entry-count">{entries.length}</span>
    </div>
  ),
}));

describe("CalendarClient", () => {
  const mockJournals: JournalEntry[] = [
    {
      journalId: "1",
      userId: "user-1",
      journalText: "Test entry",
      userMood: 7,
      createdAt: "2025-06-15T10:00:00Z",
    },
  ];

  const defaultProps = {
    journals: mockJournals,
    totalEntries: 1,
    serverDate: "2025-06-15",
    timezone: "UTC",
  };

  it("renders CalendarHeader", () => {
    render(<CalendarClient {...defaultProps} />);
    expect(screen.getByTestId("calendar-header")).toBeInTheDocument();
  });

  it("renders CalendarGrid with 42 days", () => {
    render(<CalendarClient {...defaultProps} />);
    expect(screen.getByTestId("day-count")).toHaveTextContent("42");
  });

  it("renders SelectedDateEntries for the server date", () => {
    render(<CalendarClient {...defaultProps} />);
    expect(screen.getByTestId("selected-date-entries")).toBeInTheDocument();
    expect(screen.getByTestId("selected-date")).toHaveTextContent("2025-6-15");
  });

  it("passes totalEntries to header", () => {
    render(<CalendarClient {...defaultProps} totalEntries={42} />);
    expect(screen.getByTestId("total-entries")).toHaveTextContent("42");
  });

  it("shows current month in header", () => {
    render(<CalendarClient {...defaultProps} />);
    expect(screen.getByTestId("current-month")).toHaveTextContent("6/2025");
  });

  it("navigates to previous month", () => {
    render(<CalendarClient {...defaultProps} />);
    fireEvent.click(screen.getByText("Prev Month"));
    expect(screen.getByTestId("current-month")).toHaveTextContent("5/2025");
  });

  it("navigates to next month", () => {
    render(<CalendarClient {...defaultProps} />);
    fireEvent.click(screen.getByText("Next Month"));
    expect(screen.getByTestId("current-month")).toHaveTextContent("7/2025");
  });

  it("shows entries for the selected date", () => {
    render(<CalendarClient {...defaultProps} />);
    expect(screen.getByTestId("entry-count")).toHaveTextContent("1");
  });

  it("shows 0 entries for dates without journals", () => {
    render(<CalendarClient {...defaultProps} serverDate="2025-06-01" />);
    expect(screen.getByTestId("entry-count")).toHaveTextContent("0");
  });
});
