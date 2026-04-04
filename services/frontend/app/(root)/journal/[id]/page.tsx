import { auth } from "@/auth";
import { redirect, notFound } from "next/navigation";
import { fetchJournalById } from "@/lib/server/journals";
import { JournalEntryDetailClient } from "@/components/journal/JournalEntryDetailClient";
import { ROUTES } from "@/lib/routes";

type JournalDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function JournalDetailPage({
  params,
}: JournalDetailPageProps) {
  const session = await auth();
  if (!session?.user?.id) {
    redirect(ROUTES.signin);
  }

  const { id } = await params;
  const entry = await fetchJournalById(session.user.id, id);

  if (!entry) {
    notFound();
  }

  const timezone = session.user.timezone ?? "UTC";

  return <JournalEntryDetailClient entry={entry} timezone={timezone} />;
}
