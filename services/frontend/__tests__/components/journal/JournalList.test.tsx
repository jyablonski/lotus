import { render, screen } from "@testing-library/react";
import { JournalList } from "@/components/journal/JournalList";
import { JournalEntry } from "@/types/journal";

// Mock JournalEntryCard since it's tested separately
jest.mock("@/components/journal/JournalEntryCard", () => ({
  JournalEntryCard: ({ entry }: { entry: JournalEntry }) => (
    <div data-testid={`journal-card-${entry.journalId}`}>
      {entry.journalText}
    </div>
  ),
}));

describe("JournalList", () => {
  const mockEntries: JournalEntry[] = [
    {
      journalId: "1",
      userId: "user-1",
      journalText: "First entry",
      userMood: 7,
      createdAt: "2025-01-15T10:00:00Z",
    },
    {
      journalId: "2",
      userId: "user-1",
      journalText: "Second entry",
      userMood: 5,
      createdAt: "2025-01-16T10:00:00Z",
    },
    {
      journalId: "3",
      userId: "user-1",
      journalText: "Third entry",
      userMood: 3,
      createdAt: "2025-01-17T10:00:00Z",
    },
  ];

  it("renders a card for each entry", () => {
    render(<JournalList entries={mockEntries} timezone="UTC" />);
    expect(screen.getByTestId("journal-card-1")).toBeInTheDocument();
    expect(screen.getByTestId("journal-card-2")).toBeInTheDocument();
    expect(screen.getByTestId("journal-card-3")).toBeInTheDocument();
  });

  it("renders entries in order", () => {
    render(<JournalList entries={mockEntries} timezone="UTC" />);
    const cards = screen.getAllByTestId(/^journal-card-/);
    expect(cards).toHaveLength(3);
    expect(cards[0]).toHaveTextContent("First entry");
    expect(cards[1]).toHaveTextContent("Second entry");
    expect(cards[2]).toHaveTextContent("Third entry");
  });

  it("renders empty list without errors", () => {
    const { container } = render(<JournalList entries={[]} timezone="UTC" />);
    expect(container.querySelector(".space-y-6")).toBeInTheDocument();
    expect(screen.queryByTestId(/^journal-card-/)).not.toBeInTheDocument();
  });
});
