import { render, screen } from "@testing-library/react";
import { StatCard } from "@/components/ui/StatCard";

describe("StatCard", () => {
  const defaultProps = {
    title: "Total Entries",
    value: 42,
    icon: <span data-testid="mock-icon">icon</span>,
  };

  it("renders the title", () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByText("Total Entries")).toBeInTheDocument();
  });

  it("renders numeric value", () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders string value", () => {
    render(<StatCard {...defaultProps} value="5 days" />);
    expect(screen.getByText("5 days")).toBeInTheDocument();
  });

  it("renders the icon", () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByTestId("mock-icon")).toBeInTheDocument();
  });

  it("renders trend text when provided", () => {
    render(<StatCard {...defaultProps} trend="Keep it up!" />);
    expect(screen.getByText("Keep it up!")).toBeInTheDocument();
  });

  it("does not render trend when not provided", () => {
    const { container } = render(<StatCard {...defaultProps} />);
    const trendElements = container.querySelectorAll(".text-xs");
    expect(trendElements).toHaveLength(0);
  });

  it("applies custom trendClassName", () => {
    render(
      <StatCard
        {...defaultProps}
        trend="Trending"
        trendClassName="text-green-400"
      />,
    );
    const trendEl = screen.getByText("Trending");
    expect(trendEl.className).toContain("text-green-400");
  });

  it("applies default trendClassName", () => {
    render(<StatCard {...defaultProps} trend="Default trend" />);
    const trendEl = screen.getByText("Default trend");
    expect(trendEl.className).toContain("text-lotus-400");
  });
});
