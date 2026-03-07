import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchAllJournalsForUser } from "@/lib/server";
import { JournalHomeClient } from "@/components/journal/JournalHomeClient";
import { ROUTES } from "@/lib/routes";

export default async function JournalHomePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  // Fetch all journals server-side for filtering
  const { journals, totalCount } = await fetchAllJournalsForUser(
    session.user.id,
  );

  const timezone = session.user?.timezone ?? "UTC";

  return (
    <JournalHomeClient
      journals={journals}
      totalCount={totalCount}
      timezone={timezone}
    />
  );
}
