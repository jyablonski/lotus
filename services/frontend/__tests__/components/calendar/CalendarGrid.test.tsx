import { render, screen, fireEvent } from "@testing-library/react";
import { CalendarGrid } from "@/components/calendar/CalendarGrid";
import type { CalendarDay } from "@/lib/utils/calendar";

function makeDay(overrides: Partial<CalendarDay> = {}): CalendarDay {
  return {
    date: new Date(2025, 5, 15),
    dateString: "2025-06-15",
    entries: [],
    isCurrentMonth: true,
    isToday: false,
    isSelected: false,
    entryCount: 0,
    avgMood: 0,
    ...overrides,
  };
}

function makeCalendarDays(count: number = 42): CalendarDay[] {
  return Array.from({ length: count }, (_, i) =>
    makeDay({
      date: new Date(2025, 5, i + 1),
      dateString: `2025-06-${String(i + 1).padStart(2, "0")}`,
    }),
  );
}

describe("CalendarGrid", () => {
  const defaultProps = {
    calendarDays: makeCalendarDays(),
    onDateSelect: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders weekday headers", () => {
    render(<CalendarGrid {...defaultProps} />);
    expect(screen.getByText("Sun")).toBeInTheDocument();
    expect(screen.getByText("Mon")).toBeInTheDocument();
    expect(screen.getByText("Tue")).toBeInTheDocument();
    expect(screen.getByText("Wed")).toBeInTheDocument();
    expect(screen.getByText("Thu")).toBeInTheDocument();
    expect(screen.getByText("Fri")).toBeInTheDocument();
    expect(screen.getByText("Sat")).toBeInTheDocument();
  });

  it("renders 42 day buttons", () => {
    render(<CalendarGrid {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(42);
  });

  it("calls onDateSelect when a day is clicked", () => {
    const onDateSelect = jest.fn();
    render(<CalendarGrid {...defaultProps} onDateSelect={onDateSelect} />);
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onDateSelect).toHaveBeenCalledWith(expect.any(Date));
  });

  it("shows entry count for days with entries", () => {
    const days = makeCalendarDays();
    days[5] = makeDay({
      ...days[5],
      entryCount: 3,
      avgMood: 7,
    });
    render(<CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />);
    expect(screen.getByText("3 entries")).toBeInTheDocument();
  });

  it("shows singular 'entry' for single entry", () => {
    const days = makeCalendarDays();
    days[5] = makeDay({
      ...days[5],
      entryCount: 1,
      avgMood: 5,
    });
    render(<CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />);
    expect(screen.getByText("1 entry")).toBeInTheDocument();
  });

  it("shows mood label for days with entries (1-10 scale)", () => {
    const days = makeCalendarDays();
    days[5] = makeDay({
      ...days[5],
      entryCount: 2,
      avgMood: 7,
    });
    render(<CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />);
    const dayCell = screen.getByRole("button", { name: /2 entries/ });
    expect(dayCell).toHaveTextContent("7");
  });

  it("applies today styling for today's date", () => {
    const days = makeCalendarDays();
    days[10] = makeDay({
      ...days[10],
      isToday: true,
    });
    render(<CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons[10].className).toContain("bg-lotus-500/10");
  });

  it("applies selected styling for selected date", () => {
    const days = makeCalendarDays();
    days[3] = makeDay({
      ...days[3],
      isSelected: true,
    });
    render(<CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons[3].className).toContain("bg-lotus-500/20");
  });

  it("renders today dot indicator", () => {
    const days = makeCalendarDays();
    days[10] = makeDay({
      ...days[10],
      isToday: true,
    });
    const { container } = render(
      <CalendarGrid calendarDays={days} onDateSelect={jest.fn()} />,
    );
    expect(
      container.querySelector(".bg-lotus-500.rounded-full"),
    ).toBeInTheDocument();
  });
});
