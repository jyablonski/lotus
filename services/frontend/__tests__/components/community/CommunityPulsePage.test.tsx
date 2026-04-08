import { render, screen } from "@testing-library/react";
import { CommunityPulsePage } from "@/components/community/CommunityPulsePage";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("CommunityPulsePage", () => {
  it("renders the populated pulse view", () => {
    render(
      <CommunityPulsePage
        pulse={{
          requestedTimeRange: "today",
          appliedTimeRange: "today",
          requestedScope: "nearby",
          appliedScopeType: "region",
          appliedScopeValue: "US-CA",
          topThemes: [
            {
              name: "rest",
              entryCount: 12,
              uniqueUserCount: 11,
              rank: 1,
              deltaVsPrevious: 0.2,
            },
          ],
          topMoods: [
            {
              name: "hopeful",
              entryCount: 10,
              uniqueUserCount: 10,
              rank: 1,
              deltaVsPrevious: null,
            },
          ],
          risingThemes: [
            {
              name: "change",
              entryCount: 9,
              uniqueUserCount: 9,
              rank: 1,
              deltaVsPrevious: 0.15,
            },
          ],
          communitySummary: "People are leaning toward reset and rest.",
          privacy: {
            state: "ready",
            scopeFallbackApplied: false,
            periodFallbackApplied: false,
          },
          generatedAt: "2026-04-07T10:00:00Z",
          isEmpty: false,
        }}
        promptSet={{
          featuredPrompt: {
            promptId: "prompt-1",
            promptText: "What needs a little more room today?",
            inspirationTags: ["rest"],
            tone: "gentle",
            timeRangeApplied: "today",
            scopeApplied: "region",
            generationMethod: "template",
            category: "naming",
          },
          alternatePrompts: [],
          timeRangeApplied: "today",
          appliedScopeType: "region",
          appliedScopeValue: "US-CA",
          privacy: {
            state: "ready",
            scopeFallbackApplied: false,
            periodFallbackApplied: false,
          },
          generatedAt: "2026-04-07T10:00:00Z",
          isEmpty: false,
        }}
        selectedTimeRange="today"
        selectedScope="nearby"
      />,
    );

    expect(screen.getByText("Community Pulse")).toBeInTheDocument();
    expect(
      screen.getByText("People are leaning toward reset and rest."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("rest")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Today" })).toHaveAttribute(
      "href",
      "/community?timeRange=today&scope=nearby",
    );
  });

  it("renders the empty state when no safe pulse data is available", () => {
    render(
      <CommunityPulsePage
        pulse={null}
        promptSet={null}
        selectedTimeRange="this_week"
        selectedScope="global"
      />,
    );

    expect(
      screen.getByText(/Community Pulse is still warming up/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Community-informed prompts will show up here/i),
    ).toBeInTheDocument();
  });

  it("renders an opt-in CTA when the user has not joined community sharing", () => {
    render(
      <CommunityPulsePage
        pulse={null}
        promptSet={null}
        selectedTimeRange="today"
        selectedScope="nearby"
        isCommunityOptedIn={false}
      />,
    );

    expect(
      screen.getByText("Want to help shape Community Pulse?"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Review community settings" }),
    ).toHaveAttribute("href", "/profile/settings");
  });
});
