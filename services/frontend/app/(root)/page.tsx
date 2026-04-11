import { auth } from "@/auth";
import {
  fetchFeatureFlags,
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

  const userRole = session.user.role ?? "";
  const analyticsPromise = fetchUserAnalytics(session.user.id);
  const recentJournalsPromise = fetchRecentJournals(session.user.id, 5);
  const flags = await fetchFeatureFlags(userRole);
  const showCommunityPulse = flags.community_pulse === true;
  const todayTogetherPromise = showCommunityPulse
    ? fetchTodayTogether(session.user.id, "nearby")
    : Promise.resolve(null);

  const [analytics, recentJournals, todayTogether] = await Promise.all([
    analyticsPromise,
    recentJournalsPromise,
    todayTogetherPromise,
  ]);

  return (
    <LoggedInDashboard
      analytics={analytics}
      recentJournals={recentJournals}
      showCommunityPulse={showCommunityPulse}
      todayTogether={todayTogether}
      userName={session.user.name ?? undefined}
      timezone={session.user.timezone ?? "UTC"}
    />
  );
}
