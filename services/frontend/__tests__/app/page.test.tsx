import { render, screen } from "@testing-library/react";
import { LoggedInDashboard } from "@/components/dashboard/LoggedInDashboard";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("LoggedInDashboard", () => {
  const mockAnalytics = {
    userId: "user-123",
    userEmail: "test@example.com",
    userRole: "user",
    userTimezone: "America/Los_Angeles",
    userCreatedAt: "2024-01-01T00:00:00Z",
    totalJournals: 10,
    activeDays: 5,
    avgMoodScore: 7.5,
    minMoodScore: 3,
    maxMoodScore: 9,
    moodScoreStddev: 1.2,
    positiveEntries: 7,
    negativeEntries: 2,
    neutralEntries: 1,
    avgSentimentScore: 0.6,
    avgJournalLength: 150,
    firstJournalAt: "2024-01-01T00:00:00Z",
    lastJournalAt: "2024-01-15T00:00:00Z",
    lastModifiedAt: "2024-01-15T00:00:00Z",
    totalJournals30d: 8,
    avgMoodScore30d: 7.8,
    minMoodScore30d: 5,
    maxMoodScore30d: 9,
    dailyStreak: 3,
    positivePercentage: 70,
    daysSinceLastJournal: 0,
    daysBetweenFirstAndLastJournal: 14,
    journalsPerActiveDay: 2,
  };

  const mockJournals = [
    {
      journalId: "1",
      userId: "user-123",
      journalText: "This is my first journal entry about today.",
      userMood: 7,
      createdAt: "2024-01-15T10:00:00Z",
    },
    {
      journalId: "2",
      userId: "user-123",
      journalText: "Another great day to write about my experiences.",
      userMood: 8,
      createdAt: "2024-01-14T10:00:00Z",
    },
  ];

  test("renders welcome message with user name", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
        userName="John"
      />,
    );

    expect(screen.getByText("Welcome back, John!")).toBeInTheDocument();
  });

  test("renders welcome message without user name", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
      />,
    );

    expect(screen.getByText("Welcome back!")).toBeInTheDocument();
  });

  test("displays stats from analytics", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
        userName="John"
      />,
    );

    // Check stats labels are displayed
    expect(screen.getByText("Last 30 Days")).toBeInTheDocument();
    expect(screen.getByText("Current Streak")).toBeInTheDocument();
    expect(screen.getByText("Mood Trend")).toBeInTheDocument();
    expect(screen.getByText("Total Entries")).toBeInTheDocument();

    // Check writing stats section
    expect(screen.getByText("Writing Stats")).toBeInTheDocument();
    expect(screen.getByText("Total entries:")).toBeInTheDocument();
    expect(screen.getByText("Active days:")).toBeInTheDocument();
  });

  test("displays recent entries", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
        userName="John"
      />,
    );

    expect(screen.getByText("Recent Entries")).toBeInTheDocument();
    // Check entry previews are rendered
    expect(
      screen.getByText(/This is my first journal entry/),
    ).toBeInTheDocument();
  });

  test("shows empty state when no journals", () => {
    render(
      <LoggedInDashboard
        analytics={null}
        recentJournals={[]}
        userName="John"
      />,
    );

    expect(screen.getByText("No entries yet")).toBeInTheDocument();
    expect(screen.getByText("Create Your First Entry")).toBeInTheDocument();
  });

  test("renders New Entry button", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
        userName="John"
      />,
    );

    expect(screen.getByText("New Entry")).toBeInTheDocument();
  });

  test("renders quick action links", () => {
    render(
      <LoggedInDashboard
        analytics={mockAnalytics}
        recentJournals={mockJournals}
        userName="John"
      />,
    );

    expect(screen.getByText("View Calendar")).toBeInTheDocument();
    expect(screen.getByText("Insights")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });
});
