import { render, screen } from "@testing-library/react";
import { ProfileSettingsClient } from "@/components/profile/ProfileSettingsClient";

jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock("@/components/profile/TimezoneSelector", () => ({
  TimezoneSelector: ({ currentTimezone }: { currentTimezone: string }) => (
    <div data-testid="timezone-selector">{currentTimezone}</div>
  ),
}));

jest.mock("@/components/profile/CommunitySettingsCard", () => ({
  CommunitySettingsCard: ({
    initialInsightsOptIn,
    initialLocationOptIn,
  }: {
    initialInsightsOptIn: boolean;
    initialLocationOptIn: boolean;
  }) => (
    <div data-testid="community-settings-card">
      insights:{String(initialInsightsOptIn)} location:
      {String(initialLocationOptIn)}
    </div>
  ),
}));

describe("ProfileSettingsClient", () => {
  it("renders timezone and community settings controls", () => {
    render(
      <ProfileSettingsClient
        timezone="UTC"
        communityInsightsOptIn={true}
        communityLocationOptIn={false}
        communityCountryCode="US"
        communityRegionCode="US-CA"
      />,
    );

    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByTestId("timezone-selector")).toHaveTextContent("UTC");
    expect(screen.getByTestId("community-settings-card")).toHaveTextContent(
      "insights:true location:false",
    );
  });
});
