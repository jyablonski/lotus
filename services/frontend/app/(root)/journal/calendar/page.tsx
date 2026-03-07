import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchAllJournalsForUser } from "@/lib/server";
import { CalendarClient } from "@/components/calendar/CalendarClient";
import { toLocalDateString } from "@/lib/utils/calendar";
import { ROUTES } from "@/lib/routes";

export default async function CalendarPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  // Fetch all journals server-side for calendar display
  const { journals, totalCount } = await fetchAllJournalsForUser(
    session.user.id,
  );

  // Pass server date to avoid hydration mismatch with Date.now()
  const timezone = session.user?.timezone ?? "UTC";
  const serverDate = toLocalDateString(new Date(), timezone);

  return (
    <CalendarClient
      journals={journals}
      totalEntries={totalCount}
      serverDate={serverDate}
      timezone={timezone}
    />
  );
}
