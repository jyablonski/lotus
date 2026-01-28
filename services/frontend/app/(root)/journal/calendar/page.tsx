import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchAllJournalsForUser } from "@/lib/server";
import { CalendarClient } from "@/components/calendar/CalendarClient";

/**
 * Format date as YYYY-MM-DD in server's local timezone
 * This provides a stable date string for hydration
 */
function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default async function CalendarPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  // Fetch all journals server-side for calendar display
  const { journals, totalCount } = await fetchAllJournalsForUser(
    session.user.id,
  );

  // Pass server date to avoid hydration mismatch with Date.now()
  const serverDate = toLocalDateString(new Date());

  return (
    <CalendarClient
      journals={journals}
      totalEntries={totalCount}
      serverDate={serverDate}
    />
  );
}
