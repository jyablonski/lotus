import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchAllJournalsForUser } from "@/lib/server";
import { JournalHomeClient } from "@/components/journal/JournalHomeClient";

export default async function JournalHomePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  // Fetch all journals server-side for filtering
  const { journals, totalCount } = await fetchAllJournalsForUser(
    session.user.id,
  );

  return <JournalHomeClient journals={journals} totalCount={totalCount} />;
}
