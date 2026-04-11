import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { CommunityPulsePage } from "@/components/community/CommunityPulsePage";
import { ROUTES } from "@/lib/routes";
import {
  fetchFeatureFlags,
  fetchCommunityPrompts,
  fetchCommunityPulse,
  fetchUserCommunitySettings,
} from "@/lib/server";
import type {
  CommunityScopePreference,
  CommunityTimeRange,
} from "@/types/community";

function normalizeTimeRange(value?: string): CommunityTimeRange {
  if (value === "this_week" || value === "this_month") {
    return value;
  }
  return "today";
}

function normalizeScope(value?: string): CommunityScopePreference {
  if (value === "global") {
    return "global";
  }
  return "nearby";
}

export default async function CommunityPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const session = await auth();

  if (!session?.user?.id) {
    redirect(ROUTES.home);
  }

  const userRole = session.user.role ?? "";
  const flags = await fetchFeatureFlags(userRole);
  if (flags.community_pulse !== true) {
    redirect(ROUTES.home);
  }

  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const timeRange = normalizeTimeRange(
    Array.isArray(resolvedSearchParams?.timeRange)
      ? resolvedSearchParams?.timeRange[0]
      : resolvedSearchParams?.timeRange,
  );
  const scope = normalizeScope(
    Array.isArray(resolvedSearchParams?.scope)
      ? resolvedSearchParams?.scope[0]
      : resolvedSearchParams?.scope,
  );

  const [pulse, promptSet, settings] = await Promise.all([
    fetchCommunityPulse(session.user.id, {
      timeRange,
      scope,
    }),
    fetchCommunityPrompts(session.user.id, {
      surface: "community_page",
      scope,
    }),
    fetchUserCommunitySettings(session.user.email ?? ""),
  ]);

  return (
    <CommunityPulsePage
      pulse={pulse}
      promptSet={promptSet}
      selectedTimeRange={timeRange}
      selectedScope={scope}
      isCommunityOptedIn={settings?.communityInsightsOptIn ?? false}
    />
  );
}
