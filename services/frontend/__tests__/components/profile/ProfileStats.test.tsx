import { render, screen } from "@testing-library/react";
import { ProfileStats } from "@/components/profile/ProfileStats";

jest.mock("lucide-react", () => ({
  BookOpen: () => <svg data-testid="icon-book" />,
  TrendingUp: () => <svg data-testid="icon-trending" />,
  Flame: () => <svg data-testid="icon-flame" />,
  Calendar: () => <svg data-testid="icon-calendar" />,
  Clock: () => <svg data-testid="icon-clock" />,
  PenTool: () => <svg data-testid="icon-pen" />,
}));

describe("ProfileStats", () => {
  const defaultProps = {
    totalEntries: 42,
    thisMonth: 8,
    thisWeek: 3,
    currentStreak: 5,
    longestStreak: 12,
    totalWords: 15234,
  };

  it("renders all 6 stat cards", () => {
    render(<ProfileStats {...defaultProps} />);
    expect(screen.getByText("Total Entries")).toBeInTheDocument();
    expect(screen.getByText("This Month")).toBeInTheDocument();
    expect(screen.getByText("This Week")).toBeInTheDocument();
    expect(screen.getByText("Current Streak")).toBeInTheDocument();
    expect(screen.getByText("Longest Streak")).toBeInTheDocument();
    expect(screen.getByText("Total Words")).toBeInTheDocument();
  });

  it("renders correct values", () => {
    render(<ProfileStats {...defaultProps} />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("5 days")).toBeInTheDocument();
    expect(screen.getByText("12 days")).toBeInTheDocument();
    expect(screen.getByText("15,234")).toBeInTheDocument();
  });

  it("shows 'Keep writing!' trend for total entries > 0", () => {
    render(<ProfileStats {...defaultProps} />);
    expect(screen.getByText("Keep writing!")).toBeInTheDocument();
  });

  it("shows 'Start your journey' when totalEntries is 0", () => {
    render(<ProfileStats {...defaultProps} totalEntries={0} />);
    expect(screen.getByText("Start your journey")).toBeInTheDocument();
  });

  it("shows 'Keep it up!' when currentStreak > 0", () => {
    render(<ProfileStats {...defaultProps} />);
    expect(screen.getByText("Keep it up!")).toBeInTheDocument();
  });

  it("shows 'Start your streak' when currentStreak is 0", () => {
    render(<ProfileStats {...defaultProps} currentStreak={0} />);
    expect(screen.getByText("Start your streak")).toBeInTheDocument();
  });

  it("shows 'Personal best!' when longestStreak > 0", () => {
    render(<ProfileStats {...defaultProps} />);
    expect(screen.getByText("Personal best!")).toBeInTheDocument();
  });
});
