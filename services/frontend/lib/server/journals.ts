import "server-only";

import {
  JournalEntry,
  BackendJournal,
  transformBackendJournal,
} from "@/types/journal";
import { BACKEND_URL } from "@/lib/config";

export interface JournalsResponse {
  journals: JournalEntry[];
  totalCount: number;
  hasMore: boolean;
}

/**
 * Fetch journals for a user from the backend (server-side only).
 * Calls the Go backend directly, bypassing any API route.
 */
export async function fetchJournalsForUser(
  userId: string,
  options?: { limit?: number; offset?: number; cache?: RequestCache },
): Promise<JournalsResponse> {
  const { limit = 10, offset = 0, cache } = options ?? {};

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/journals?user_id=${userId}&limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        ...(cache === "no-store"
          ? { cache: "no-store" as RequestCache }
          : { next: { revalidate: 30 } }),
      },
    );

    if (!response.ok) {
      console.error(`Backend journals error: ${response.status}`);
      return { journals: [], totalCount: 0, hasMore: false };
    }

    const data = await response.json();

    const journals: JournalEntry[] =
      data.journals?.map((j: BackendJournal) => transformBackendJournal(j)) ||
      [];

    return {
      journals,
      totalCount: parseInt(data.totalCount, 10) || 0,
      hasMore: data.hasMore || false,
    };
  } catch (error) {
    console.error("Error fetching journals:", error);
    return { journals: [], totalCount: 0, hasMore: false };
  }
}

/**
 * Fetch recent journals for dashboard display.
 */
export async function fetchRecentJournals(
  userId: string,
  count: number = 5,
): Promise<JournalEntry[]> {
  const response = await fetchJournalsForUser(userId, { limit: count });
  return response.journals;
}

/**
 * Fetch all journals for a user (for journal home, calendar, profile views).
 * Uses uncached fetch so topic tags and list are always up to date.
 */
export async function fetchAllJournalsForUser(
  userId: string,
): Promise<JournalsResponse> {
  return fetchJournalsForUser(userId, {
    limit: 1000,
    offset: 0,
    cache: "no-store",
  });
}
