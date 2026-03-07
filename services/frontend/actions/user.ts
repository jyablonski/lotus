"use server";

import { auth } from "@/auth";
import { BACKEND_URL } from "@/lib/config";

export interface UpdateTimezoneResult {
  success: boolean;
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
        headers: { "Content-Type": "application/json" },
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

    return { success: true };
  } catch (error) {
    console.error("Error updating timezone:", error);
    return {
      success: false,
      error:
        error instanceof Error ? error.message : "Failed to update timezone",
    };
  }
}
