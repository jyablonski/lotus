import { auth } from "@/auth";
import { fetchUserAnalytics, fetchRecentJournals } from "@/lib/server";
import { LoggedInDashboard } from "@/components/dashboard/LoggedInDashboard";
import LandingPage from "@/components/landing/LandingPage";

export default async function HomePage() {
  const session = await auth();

  // Unauthenticated users see the landing page
  if (!session?.user?.id) {
    return <LandingPage />;
  }

  // Fetch data in parallel on the server
  const [analytics, recentJournals] = await Promise.all([
    fetchUserAnalytics(session.user.id),
    fetchRecentJournals(session.user.id, 5),
  ]);

  return (
    <LoggedInDashboard
      analytics={analytics}
      recentJournals={recentJournals}
      userName={session.user.name ?? undefined}
    />
  );
}
