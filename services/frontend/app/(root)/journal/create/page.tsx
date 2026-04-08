import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchCommunityPrompts } from "@/lib/server";
import { ROUTES } from "@/lib/routes";
import CreateJournalPageClient from "@/components/journal/CreateJournalPageClient";

export default async function CreateJournalPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const communityPromptSet = await fetchCommunityPrompts(session.user.id, {
    surface: "journal_create",
    scope: "nearby",
  });

  return <CreateJournalPageClient communityPromptSet={communityPromptSet} />;
}
