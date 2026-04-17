import { render, screen } from "@testing-library/react";
import { ProfileInsights } from "@/components/profile/ProfileInsights";

describe("ProfileInsights", () => {
  const defaultProps = {
    averageMood: 7,
    mostActiveDay: "Monday",
    favoriteModCategory: "Positive",
  };

  it("renders 'Your Insights' heading", () => {
    render(<ProfileInsights {...defaultProps} />);
    expect(screen.getByText("Your Insights")).toBeInTheDocument();
  });

  it("renders average mood section", () => {
    render(<ProfileInsights {...defaultProps} />);
    expect(screen.getByText("Average Mood")).toBeInTheDocument();
    expect(screen.getByText("7/10")).toBeInTheDocument();
  });

  it("renders mood badge for average mood (1-10 scale)", () => {
    render(<ProfileInsights {...defaultProps} />);
    // Exact match avoids also matching the "7/10" text rendered elsewhere.
    expect(screen.getByText("7", { exact: true })).toBeInTheDocument();
  });

  it("shows 'No data' when averageMood is 0", () => {
    render(<ProfileInsights {...defaultProps} averageMood={0} />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders most active day", () => {
    render(<ProfileInsights {...defaultProps} />);
    expect(screen.getByText("Most Active Day")).toBeInTheDocument();
    expect(screen.getByText("Monday")).toBeInTheDocument();
  });

  it("renders calendar emoji for most active day", () => {
    render(<ProfileInsights {...defaultProps} />);
    expect(screen.getByText("📅")).toBeInTheDocument();
  });

  it("renders favorite mood category", () => {
    render(<ProfileInsights {...defaultProps} />);
    expect(screen.getByText("Most Common Mood")).toBeInTheDocument();
    expect(screen.getByText("Positive")).toBeInTheDocument();
  });

  it("shows happy emoji for Positive category", () => {
    render(
      <ProfileInsights {...defaultProps} favoriteModCategory="Positive" />,
    );
    // 😊 appears both for the Positive category and in the mood config, so match any occurrence.
    const moodCategoryEmojis = screen.getAllByText("😊");
    expect(moodCategoryEmojis.length).toBeGreaterThanOrEqual(1);
  });

  it("shows sad emoji for Negative category", () => {
    render(
      <ProfileInsights {...defaultProps} favoriteModCategory="Negative" />,
    );
    expect(screen.getByText("😔")).toBeInTheDocument();
  });

  it("shows neutral emoji for other categories", () => {
    render(<ProfileInsights {...defaultProps} favoriteModCategory="Mixed" />);
    expect(screen.getByText("😐")).toBeInTheDocument();
  });
});
