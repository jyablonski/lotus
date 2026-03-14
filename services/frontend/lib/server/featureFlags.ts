import "server-only";

import { BACKEND_URL } from "@/lib/config";

export interface FeatureFlags {
  [key: string]: boolean;
}

interface FeatureFlagResponse {
  name: string;
  isActive: boolean;
}

interface GetFeatureFlagsResponse {
  flags: FeatureFlagResponse[];
}

/**
 * Fetch evaluated feature flags from the backend (server-side only).
 * The Go backend queries django-waffle's flag table and evaluates each flag
 * based on the provided user role.
 *
 * Returns a record mapping flag names to booleans, e.g.:
 *   { frontend_maintenance: true, frontend_admin: false }
 */
export async function fetchFeatureFlags(
  userRole: string = "",
): Promise<FeatureFlags> {
  try {
    const params = new URLSearchParams();
    if (userRole) {
      // gRPC-Gateway binds query params by JSON (camelCase) name, not proto name
      params.set("userRole", userRole);
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/feature-flags?${params.toString()}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        next: { revalidate: 30 },
      },
    );

    if (!response.ok) {
      console.error(`Backend feature flags error: ${response.status}`);
      return {};
    }

    const data: GetFeatureFlagsResponse = await response.json();

    const flags: FeatureFlags = {};
    for (const flag of data.flags ?? []) {
      flags[flag.name] = flag.isActive;
    }

    return flags;
  } catch (error) {
    console.error("Error fetching feature flags:", error);
    return {};
  }
}
