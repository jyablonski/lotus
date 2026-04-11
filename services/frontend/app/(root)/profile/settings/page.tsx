import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ProfileSettingsClient } from "@/components/profile/ProfileSettingsClient";
import { fetchFeatureFlags, fetchUserCommunitySettings } from "@/lib/server";
import { ROUTES } from "@/lib/routes";

export default async function ProfileSettingsPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const timezone = session.user?.timezone ?? "UTC";
  const userRole = session.user.role ?? "";
  const flags = await fetchFeatureFlags(userRole);
  const showCommunityPulse = flags.community_pulse === true;
  const settings = showCommunityPulse
    ? await fetchUserCommunitySettings(session.user.email ?? "")
    : null;

  return (
    <ProfileSettingsClient
      timezone={timezone}
      showCommunityPulse={showCommunityPulse}
      communityInsightsOptIn={settings?.communityInsightsOptIn ?? false}
      communityLocationOptIn={settings?.communityLocationOptIn ?? false}
      communityCountryCode={settings?.communityCountryCode ?? ""}
      communityRegionCode={settings?.communityRegionCode ?? ""}
    />
  );
}
