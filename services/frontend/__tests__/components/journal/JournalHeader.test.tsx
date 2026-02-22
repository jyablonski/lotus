import { render, screen } from "@testing-library/react";
import { JournalHeader } from "@/components/journal/JournalHeader";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("lucide-react", () => ({
  Plus: () => <svg data-testid="plus-icon" />,
}));

describe("JournalHeader", () => {
  it("renders 'My Journal' heading", () => {
    render(<JournalHeader totalEntries={5} />);
    expect(screen.getByText("My Journal")).toBeInTheDocument();
  });

  it("shows entry count with plural", () => {
    render(<JournalHeader totalEntries={5} />);
    expect(screen.getByText("5 entries total")).toBeInTheDocument();
  });

  it("shows entry count with singular", () => {
    render(<JournalHeader totalEntries={1} />);
    expect(screen.getByText("1 entry total")).toBeInTheDocument();
  });

  it("shows 'New Entry' link to /journal/create", () => {
    render(<JournalHeader totalEntries={5} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/journal/create");
    expect(screen.getByText("New Entry")).toBeInTheDocument();
  });

  describe("with filters active", () => {
    it("shows filtered count", () => {
      render(
        <JournalHeader totalEntries={10} filteredCount={3} hasFilters={true} />,
      );
      expect(
        screen.getByText("3 of 10 entries (filtered)"),
      ).toBeInTheDocument();
    });

    it("shows pagination hint", () => {
      render(
        <JournalHeader totalEntries={10} filteredCount={3} hasFilters={true} />,
      );
      expect(
        screen.getByText(
          "Use pagination controls below to navigate filtered results",
        ),
      ).toBeInTheDocument();
    });
  });

  describe("with pagination", () => {
    it("shows page info when totalPages > 1", () => {
      render(
        <JournalHeader totalEntries={25} currentPage={2} totalPages={3} />,
      );
      expect(
        screen.getByText("25 entries total • Page 2 of 3"),
      ).toBeInTheDocument();
    });

    it("does not show page info when totalPages is 1", () => {
      render(<JournalHeader totalEntries={5} currentPage={1} totalPages={1} />);
      expect(screen.getByText("5 entries total")).toBeInTheDocument();
    });
  });
});
