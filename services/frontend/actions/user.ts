"use server";

import { auth } from "@/auth";
import { BACKEND_URL } from "@/lib/config";
import { backendHeaders } from "@/lib/server/backendHeaders";

export interface UpdateTimezoneResult {
  success: boolean;
  timezone?: string;
  error?: string;
}

export interface UpdateCommunitySettingsResult {
  success: boolean;
  communityInsightsOptIn?: boolean;
  communityLocationOptIn?: boolean;
  communityCountryCode?: string;
  communityRegionCode?: string;
  error?: string;
}

/**
 * Server action to update the user's timezone preference.
 * Calls PATCH /v1/users/{userId}/timezone on the Go backend.
 */
export async function updateTimezone(
  timezone: string,
): Promise<UpdateTimezoneResult> {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/users/${session.user.id}/timezone`,
      {
        method: "PATCH",
        headers: backendHeaders(),
        body: JSON.stringify({ timezone }),
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error updating timezone:", errorText);
      return {
        success: false,
        error: `Failed to update timezone: ${response.status}`,
      };
    }

    return { success: true, timezone };
  } catch (error) {
    console.error("Error updating timezone:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to update timezone",
    };
  }
}

export async function updateCommunitySettings(input: {
  communityInsightsOptIn: boolean;
  communityLocationOptIn: boolean;
  communityCountryCode: string;
  communityRegionCode: string;
}): Promise<UpdateCommunitySettingsResult> {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return { success: false, error: "Unauthorized" };
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/users/${session.user.id}/community-settings`,
      {
        method: "PATCH",
        headers: backendHeaders(),
        body: JSON.stringify({
          community_insights_opt_in: input.communityInsightsOptIn,
          community_location_opt_in: input.communityLocationOptIn,
          community_country_code: input.communityCountryCode
            .trim()
            .toUpperCase(),
          community_region_code: input.communityRegionCode.trim().toUpperCase(),
        }),
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error updating community settings:", errorText);
      return {
        success: false,
        error: `Failed to update community settings: ${response.status}`,
      };
    }

    const data = (await response.json()) as Record<string, unknown>;
    return {
      success: true,
      communityInsightsOptIn: Boolean(
        data.communityInsightsOptIn ?? data.community_insights_opt_in,
      ),
      communityLocationOptIn: Boolean(
        data.communityLocationOptIn ?? data.community_location_opt_in,
      ),
      communityCountryCode: String(
        data.communityCountryCode ?? data.community_country_code ?? "",
      ),
      communityRegionCode: String(
        data.communityRegionCode ?? data.community_region_code ?? "",
      ),
    };
  } catch (error) {
    console.error("Error updating community settings:", error);
    return {
      success: false,
      error:
        error instanceof Error
          ? error.message
          : "Failed to update community settings",
    };
  }
}
