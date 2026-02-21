import "server-only";

import { fetchAllJournalsForUser } from "./journals";
import {
  calculateProfileStats,
  type ProfileStats,
} from "@/lib/utils/profileStats";

export type { ProfileStats };

/**
 * Fetch profile stats for a user (server-side only).
 * Fetches journals and delegates all calculation to shared utils.
 */
export async function fetchProfileStats(userId: string): Promise<ProfileStats> {
  const { journals } = await fetchAllJournalsForUser(userId);
  return calculateProfileStats(journals);
}
