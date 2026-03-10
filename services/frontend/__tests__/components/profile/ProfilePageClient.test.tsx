import { render, screen } from "@testing-library/react";
import { ProfilePageClient } from "@/components/profile/ProfilePageClient";
import type { ProfileStats } from "@/lib/utils/profileStats";

// Mock child components to test composition
jest.mock("@/components/profile/ProfileHeader", () => ({
  ProfileHeader: ({ name, email }: { name: string; email: string }) => (
    <div data-testid="profile-header">
      {name} - {email}
    </div>
  ),
}));

jest.mock("@/components/profile/ProfileStats", () => ({
  ProfileStats: ({ totalEntries }: { totalEntries: number }) => (
    <div data-testid="profile-stats">Entries: {totalEntries}</div>
  ),
}));

jest.mock("@/components/profile/ProfileInsights", () => ({
  ProfileInsights: ({ averageMood }: { averageMood: number }) => (
    <div data-testid="profile-insights">Mood: {averageMood}</div>
  ),
}));

jest.mock("@/components/profile/ProfileActions", () => ({
  ProfileActions: () => <div data-testid="profile-actions">Actions</div>,
}));

describe("ProfilePageClient", () => {
  const mockStats: ProfileStats = {
    totalEntries: 42,
    thisMonth: 8,
    thisWeek: 3,
    averageMood: 6.5,
    currentStreak: 5,
    longestStreak: 12,
    mostActiveDay: "Monday",
    firstEntryDate: "2025-01-20",
    favoriteModCategory: "Positive",
    totalWords: 15000,
  };

  const defaultProps = {
    name: "Jane Doe",
    email: "jane@example.com",
    image: "https://example.com/avatar.jpg",
    signupDate: "2025-01-15T00:00:00Z",
    stats: mockStats,
    timezone: "UTC",
  };

  it("renders ProfileHeader with user info", () => {
    render(<ProfilePageClient {...defaultProps} />);
    expect(screen.getByTestId("profile-header")).toHaveTextContent(
      "Jane Doe - jane@example.com",
    );
  });

  it("renders 'Your Journal Statistics' heading", () => {
    render(<ProfilePageClient {...defaultProps} />);
    expect(screen.getByText("Your Journal Statistics")).toBeInTheDocument();
  });

  it("renders ProfileStats with stats data", () => {
    render(<ProfilePageClient {...defaultProps} />);
    expect(screen.getByTestId("profile-stats")).toHaveTextContent(
      "Entries: 42",
    );
  });

  it("renders ProfileInsights", () => {
    render(<ProfilePageClient {...defaultProps} />);
    expect(screen.getByTestId("profile-insights")).toHaveTextContent(
      "Mood: 6.5",
    );
  });

  it("renders ProfileActions", () => {
    render(<ProfilePageClient {...defaultProps} />);
    expect(screen.getByTestId("profile-actions")).toBeInTheDocument();
  });
});
