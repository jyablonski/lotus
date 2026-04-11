import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchCommunityPrompts, fetchFeatureFlags } from "@/lib/server";
import { ROUTES } from "@/lib/routes";
import CreateJournalPageClient from "@/components/journal/CreateJournalPageClient";

export default async function CreateJournalPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const userRole = session.user.role ?? "";
  const flags = await fetchFeatureFlags(userRole);
  const communityPromptSet =
    flags.community_pulse === true
      ? await fetchCommunityPrompts(session.user.id, {
          surface: "journal_create",
          scope: "nearby",
        })
      : null;

  return <CreateJournalPageClient communityPromptSet={communityPromptSet} />;
}
