import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ProfileSettingsClient } from "@/components/profile/ProfileSettingsClient";
import { ROUTES } from "@/lib/routes";

export default async function ProfileSettingsPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const timezone = session.user?.timezone ?? "UTC";

  return <ProfileSettingsClient timezone={timezone} />;
}
