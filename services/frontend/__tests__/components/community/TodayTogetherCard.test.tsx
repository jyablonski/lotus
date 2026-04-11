import { render, screen } from "@testing-library/react";
import { TodayTogetherCard } from "@/components/community/TodayTogetherCard";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("TodayTogetherCard", () => {
  it("renders the fallback state when no snapshot is available", () => {
    render(<TodayTogetherCard snapshot={null} />);

    expect(screen.getByText("Today, Together")).toBeInTheDocument();
    expect(
      screen.getByText(/The community view is quiet right now/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Start writing")).toBeInTheDocument();
  });

  it("renders themes and mood when a snapshot is available", () => {
    render(
      <TodayTogetherCard
        snapshot={{
          bucketDate: "2026-04-07",
          periodApplied: "today",
          themes: [
            {
              name: "rest",
              entryCount: 12,
              uniqueUserCount: 11,
              rank: 1,
              deltaVsPrevious: null,
            },
            {
              name: "change",
              entryCount: 10,
              uniqueUserCount: 10,
              rank: 2,
              deltaVsPrevious: null,
            },
          ],
          dominantMood: "hopeful",
          communityNote: "People are making room to breathe.",
          appliedScopeType: "region",
          appliedScopeValue: "US-CA",
          privacy: {
            state: "fallback",
            scopeFallbackApplied: true,
            periodFallbackApplied: false,
          },
          generatedAt: "2026-04-07T10:00:00Z",
          isEmpty: false,
        }}
      />,
    );

    expect(
      screen.getByText("People are making room to breathe."),
    ).toBeInTheDocument();
    expect(screen.getByText("rest")).toBeInTheDocument();
    expect(screen.getByText("hopeful")).toBeInTheDocument();
    expect(
      screen.getByText("Using a broader privacy-safe view"),
    ).toBeInTheDocument();
  });
});
