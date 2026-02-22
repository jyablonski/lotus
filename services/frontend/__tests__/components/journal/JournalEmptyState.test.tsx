import { render, screen } from "@testing-library/react";
import { JournalEmptyState } from "@/components/journal/JournalEmptyState";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("JournalEmptyState", () => {
  describe("when user has no entries at all", () => {
    it("shows 'No journal entries yet' message", () => {
      render(<JournalEmptyState hasEntries={false} />);
      expect(screen.getByText("No journal entries yet")).toBeInTheDocument();
    });

    it("shows encouragement text", () => {
      render(<JournalEmptyState hasEntries={false} />);
      expect(
        screen.getByText(
          "Start your journaling journey by creating your first entry.",
        ),
      ).toBeInTheDocument();
    });

    it("renders a link to create first entry", () => {
      render(<JournalEmptyState hasEntries={false} />);
      const link = screen.getByRole("link");
      expect(link).toHaveAttribute("href", "/journal/create");
    });

    it("shows 'Create Your First Entry' button", () => {
      render(<JournalEmptyState hasEntries={false} />);
      expect(
        screen.getByRole("button", { name: "Create Your First Entry" }),
      ).toBeInTheDocument();
    });
  });

  describe("when user has entries but filters yield none", () => {
    it("shows 'No entries found' message", () => {
      render(<JournalEmptyState hasEntries={true} />);
      expect(screen.getByText("No entries found")).toBeInTheDocument();
    });

    it("shows filter adjustment suggestion", () => {
      render(<JournalEmptyState hasEntries={true} />);
      expect(
        screen.getByText("Try adjusting your search or filter criteria."),
      ).toBeInTheDocument();
    });

    it("does not render a create link", () => {
      render(<JournalEmptyState hasEntries={true} />);
      expect(screen.queryByRole("link")).not.toBeInTheDocument();
    });
  });
});
