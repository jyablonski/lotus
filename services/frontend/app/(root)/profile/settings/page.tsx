import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ProfileSettingsClient } from "@/components/profile/ProfileSettingsClient";
import { fetchUserCommunitySettings } from "@/lib/server";
import { ROUTES } from "@/lib/routes";

export default async function ProfileSettingsPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const timezone = session.user?.timezone ?? "UTC";
  const settings = await fetchUserCommunitySettings(session.user.email ?? "");

  return (
    <ProfileSettingsClient
      timezone={timezone}
      communityInsightsOptIn={settings?.communityInsightsOptIn ?? false}
      communityLocationOptIn={settings?.communityLocationOptIn ?? false}
      communityCountryCode={settings?.communityCountryCode ?? ""}
      communityRegionCode={settings?.communityRegionCode ?? ""}
    />
  );
}
