import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchAllJournalsForUser, fetchFeatureFlags } from "@/lib/server";
import { JournalHomeClient } from "@/components/journal/JournalHomeClient";
import { ROUTES } from "@/lib/routes";

// Always fetch fresh journals and flags so topic tags and feature flags are up to date
export const dynamic = "force-dynamic";

export default async function JournalHomePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const userRole = session.user?.role ?? "";
  const [{ journals, totalCount }, flags] = await Promise.all([
    fetchAllJournalsForUser(session.user.id),
    fetchFeatureFlags(userRole),
  ]);

  const timezone = session.user?.timezone ?? "UTC";
  const showTags = flags.frontend_show_tags === true;

  return (
    <JournalHomeClient
      journals={journals}
      totalCount={totalCount}
      timezone={timezone}
      showTags={showTags}
    />
  );
}
