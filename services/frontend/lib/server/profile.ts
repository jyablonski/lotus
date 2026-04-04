import "server-only";

import { fetchAllJournalsForUser } from "./journals";
import {
  calculateProfileStats,
  type ProfileStats,
} from "@/lib/utils/profileStats";
import type { JournalEntry } from "@/types/journal";

export type { ProfileStats };

/**
 * Fetch profile stats for a user (server-side only).
 * Fetches journals and delegates all calculation to shared utils.
 */
export async function fetchProfileStats(userId: string): Promise<ProfileStats> {
  const { journals } = await fetchAllJournalsForUser(userId);
  return calculateProfileStats(journals);
}

/**
 * Stats plus full journal list (single paginated fetch) for profile charts / export.
 */
export async function fetchProfilePageData(userId: string): Promise<{
  stats: ProfileStats;
  journals: JournalEntry[];
}> {
  const { journals } = await fetchAllJournalsForUser(userId);
  return {
    stats: calculateProfileStats(journals),
    journals,
  };
}
