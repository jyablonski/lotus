import { render, screen, act } from "@testing-library/react";
import { SelectedDateEntries } from "@/components/calendar/SelectedDateEntries";
import { JournalEntry } from "@/types/journal";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

// Mock JournalEntryCard since it's tested separately
jest.mock("@/components/journal/JournalEntryCard", () => ({
  JournalEntryCard: ({ entry }: { entry: JournalEntry }) => (
    <div data-testid={`entry-card-${entry.journalId}`}>{entry.journalText}</div>
  ),
}));

const mockEntry: JournalEntry = {
  journalId: "1",
  userId: "user-1",
  journalText: "Test journal entry",
  userMood: 7,
  createdAt: "2025-06-15T10:00:00Z",
};

describe("SelectedDateEntries", () => {
  describe("with a past date and no entries", () => {
    const pastDate = new Date(2024, 0, 15); // Jan 15, 2024

    it("renders the formatted date", () => {
      render(
        <SelectedDateEntries
          selectedDate={pastDate}
          entries={[]}
          timezone="UTC"
        />,
      );
      expect(screen.getByText(/January 15, 2024/)).toBeInTheDocument();
    });

    it("shows '0 entries' count", () => {
      render(
        <SelectedDateEntries
          selectedDate={pastDate}
          entries={[]}
          timezone="UTC"
        />,
      );
      expect(screen.getByText("0 entries")).toBeInTheDocument();
    });

    it("shows 'No entries for this date'", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={pastDate}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(screen.getByText("No entries for this date")).toBeInTheDocument();
    });

    it("shows 'Past entries cannot be created' after effect", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={pastDate}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.getByText("Past entries cannot be created"),
      ).toBeInTheDocument();
    });
  });

  describe("with a future date and no entries", () => {
    // Use a date far in the future to ensure it's always future
    const futureDate = new Date(2099, 11, 25); // Dec 25, 2099

    it("shows 'Future entries cannot be created' after effect", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={futureDate}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.getByText("Future entries cannot be created"),
      ).toBeInTheDocument();
    });

    it("does not show 'Add Entry' button", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={futureDate}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.queryByRole("button", { name: "Add Entry" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("with today's date and no entries", () => {
    const today = new Date();

    it("shows 'Today' as the header after effect", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={today}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(screen.getByText("Today")).toBeInTheDocument();
    });

    it("shows 'No entries for today yet'", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={today}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(screen.getByText("No entries for today yet")).toBeInTheDocument();
    });

    it("shows 'Create Todays Entry' button", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={today}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.getByRole("button", { name: "Create Todays Entry" }),
      ).toBeInTheDocument();
    });

    it("shows 'Add Entry' button in header when no entries today", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={today}
            entries={[]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.getByRole("button", { name: "Add Entry" }),
      ).toBeInTheDocument();
    });
  });

  describe("with entries", () => {
    const pastDate = new Date(2025, 5, 15);
    const entries = [
      mockEntry,
      { ...mockEntry, journalId: "2", journalText: "Second entry" },
    ];

    it("shows entry count", () => {
      render(
        <SelectedDateEntries
          selectedDate={pastDate}
          entries={entries}
          timezone="UTC"
        />,
      );
      expect(screen.getByText("2 entries")).toBeInTheDocument();
    });

    it("shows singular 'entry' for single entry", () => {
      render(
        <SelectedDateEntries
          selectedDate={pastDate}
          entries={[mockEntry]}
          timezone="UTC"
        />,
      );
      expect(screen.getByText("1 entry")).toBeInTheDocument();
    });

    it("renders JournalEntryCard for each entry", () => {
      render(
        <SelectedDateEntries
          selectedDate={pastDate}
          entries={entries}
          timezone="UTC"
        />,
      );
      expect(screen.getByTestId("entry-card-1")).toBeInTheDocument();
      expect(screen.getByTestId("entry-card-2")).toBeInTheDocument();
    });

    it("shows 'Add Another Entry for Today' when viewing today with entries", async () => {
      const today = new Date();
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={today}
            entries={[mockEntry]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.getByRole("button", { name: "Add Another Entry for Today" }),
      ).toBeInTheDocument();
    });

    it("does not show 'Add Another Entry' for past dates", async () => {
      await act(async () => {
        render(
          <SelectedDateEntries
            selectedDate={pastDate}
            entries={[mockEntry]}
            timezone="UTC"
          />,
        );
      });
      expect(
        screen.queryByRole("button", {
          name: "Add Another Entry for Today",
        }),
      ).not.toBeInTheDocument();
    });
  });
});
