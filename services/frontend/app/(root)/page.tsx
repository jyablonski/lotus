import { auth } from "@/auth";
import {
  fetchUserAnalytics,
  fetchRecentJournals,
  fetchTodayTogether,
} from "@/lib/server";
import { LoggedInDashboard } from "@/components/dashboard/LoggedInDashboard";
import LandingPage from "@/components/landing/LandingPage";

export default async function HomePage() {
  const session = await auth();

  // Unauthenticated users see the landing page
  if (!session?.user?.id) {
    return <LandingPage />;
  }

  // Fetch data in parallel on the server
  const [analytics, recentJournals, todayTogether] = await Promise.all([
    fetchUserAnalytics(session.user.id),
    fetchRecentJournals(session.user.id, 5),
    fetchTodayTogether(session.user.id, "nearby"),
  ]);

  return (
    <LoggedInDashboard
      analytics={analytics}
      recentJournals={recentJournals}
      todayTogether={todayTogether}
      userName={session.user.name ?? undefined}
      timezone={session.user.timezone ?? "UTC"}
    />
  );
}
