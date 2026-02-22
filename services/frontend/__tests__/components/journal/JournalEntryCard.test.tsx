import { render, screen, fireEvent } from "@testing-library/react";
import { JournalEntryCard } from "@/components/journal/JournalEntryCard";
import { JournalEntry } from "@/types/journal";

describe("JournalEntryCard", () => {
  const shortEntry: JournalEntry = {
    journalId: "1",
    userId: "user-1",
    journalText: "A short journal entry.",
    userMood: 7, // happy
    createdAt: "2025-06-15T14:30:00Z",
  };

  const longEntry: JournalEntry = {
    journalId: "2",
    userId: "user-1",
    journalText: "A".repeat(250),
    userMood: 3, // sad
    createdAt: "2025-01-01T09:05:00Z",
  };

  it("renders the journal text", () => {
    render(<JournalEntryCard entry={shortEntry} />);
    expect(screen.getByText("A short journal entry.")).toBeInTheDocument();
  });

  it("renders the formatted date", () => {
    render(<JournalEntryCard entry={shortEntry} />);
    // Date formatting is locale-dependent based on the component's custom formatter
    // Just check that some date text is rendered
    const dateElement = screen.getByText(/2025|June|January/i, {
      exact: false,
    });
    expect(dateElement).toBeInTheDocument();
  });

  it("renders mood badge with emoji and label", () => {
    render(<JournalEntryCard entry={shortEntry} />);
    // Happy mood: emoji 😊, label "Happy"
    expect(screen.getByText("😊")).toBeInTheDocument();
    expect(screen.getByText("Happy")).toBeInTheDocument();
  });

  it("renders sad mood correctly", () => {
    render(<JournalEntryCard entry={longEntry} />);
    expect(screen.getByText("😢")).toBeInTheDocument();
    expect(screen.getByText("Sad")).toBeInTheDocument();
  });

  describe("text truncation", () => {
    it("does not show 'Read more' for short entries", () => {
      render(<JournalEntryCard entry={shortEntry} />);
      expect(screen.queryByText("Read more")).not.toBeInTheDocument();
    });

    it("truncates text longer than 200 characters", () => {
      render(<JournalEntryCard entry={longEntry} />);
      // Should show truncated text with "..."
      const displayedText = screen.getByText(/\.\.\.$/);
      expect(displayedText).toBeInTheDocument();
    });

    it("shows 'Read more' for long entries", () => {
      render(<JournalEntryCard entry={longEntry} />);
      expect(screen.getByText("Read more")).toBeInTheDocument();
    });

    it("expands text when 'Read more' is clicked", () => {
      render(<JournalEntryCard entry={longEntry} />);
      fireEvent.click(screen.getByText("Read more"));
      // Full text should now be visible (no "...")
      expect(screen.getByText("A".repeat(250))).toBeInTheDocument();
      expect(screen.getByText("Show less")).toBeInTheDocument();
    });

    it("collapses text when 'Show less' is clicked", () => {
      render(<JournalEntryCard entry={longEntry} />);
      // Expand
      fireEvent.click(screen.getByText("Read more"));
      // Collapse
      fireEvent.click(screen.getByText("Show less"));
      expect(screen.getByText("Read more")).toBeInTheDocument();
      expect(screen.queryByText("A".repeat(250))).not.toBeInTheDocument();
    });
  });

  it("does not truncate text exactly at 200 characters", () => {
    const exactEntry: JournalEntry = {
      ...shortEntry,
      journalText: "B".repeat(200),
    };
    render(<JournalEntryCard entry={exactEntry} />);
    expect(screen.queryByText("Read more")).not.toBeInTheDocument();
    expect(screen.getByText("B".repeat(200))).toBeInTheDocument();
  });
});
