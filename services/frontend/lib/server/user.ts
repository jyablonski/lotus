import "server-only";

import { BACKEND_URL } from "@/lib/config";
import { backendHeaders } from "@/lib/server/backendHeaders";

export interface UserCommunitySettings {
  communityInsightsOptIn: boolean;
  communityLocationOptIn: boolean;
  communityCountryCode: string;
  communityRegionCode: string;
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asBoolean(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

export async function fetchUserCommunitySettings(
  email: string,
): Promise<UserCommunitySettings | null> {
  if (!email) {
    return null;
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/users?email=${encodeURIComponent(email)}`,
      {
        method: "GET",
        headers: backendHeaders(),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      console.error(`Backend user settings error: ${response.status}`);
      return null;
    }

    const data = (await response.json()) as Record<string, unknown>;

    return {
      communityInsightsOptIn: asBoolean(
        data.communityInsightsOptIn ?? data.community_insights_opt_in,
      ),
      communityLocationOptIn: asBoolean(
        data.communityLocationOptIn ?? data.community_location_opt_in,
      ),
      communityCountryCode: asString(
        data.communityCountryCode ?? data.community_country_code,
      ),
      communityRegionCode: asString(
        data.communityRegionCode ?? data.community_region_code,
      ),
    };
  } catch (error) {
    console.error("Error fetching user community settings:", error);
    return null;
  }
}
